"""Валидатор контент-пакетов Code Academy (раздел 16 ТЗ: «не выпускать задания без тестов»).

Проверяет:
  1. Соответствие JSON Schema (пакет, урок, сценарий, задания).
  2. Сценарий анимированного урока: код из «видео» реально запускается и выводит
     ровно то, что покажет анимация.
  3. Задания: эталон проходит все тесты; заготовка (fix/complete) и типовые
     неверные решения — НЕ проходят; для predict ответ совпадает с реальным выводом.
  4. Конспект: все блоки ```python выполняются без ошибок.
  5. Длительность озвучки: ≤ 10 минут (ТЗ), предупреждение вне 3–8 минут.

Языки: Python — ca_runner (FastAPI — тоже, нужен pip-пакет fastapi); HTML/CSS/JS, SQL и разбор
Kotlin — ТОТ ЖЕ веб-раннер, что в приложении (web-runner/tools/run-jobs.mjs, настольный Chromium);
программы на Kotlin компилируются и запускаются настоящим kotlinc (переменная KOTLINC или PATH).

Использование: python tools/validate_content.py content/packs [--json report.json] [--require-kotlinc]
Код возврата 1 при ошибках.
"""
import argparse
import hashlib
import json
import pathlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER_DIR = ROOT / "app" / "src" / "main" / "python"
sys.path.insert(0, str(RUNNER_DIR))
import ca_runner  # noqa: E402
import jsonschema  # noqa: E402
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location("narrate", pathlib.Path(__file__).resolve().parents[1] / "content-pipeline" / "narrate.py")
_narrate = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_narrate)
split_phrases = _narrate.split_phrases

SCHEMAS = {n: json.loads((ROOT / "content" / "schema" / f"{n}.schema.json").read_text(encoding="utf-8"))
           for n in ("pack", "lesson", "scenario", "assignment")}
WORDS_PER_MIN = 140  # замер: образцы озвучки ~150 слов/мин; берём с запасом
MAX_MIN, WARN_MIN_LOW, WARN_MIN_HIGH = 10.0, 3.0, 8.0


class Report:
    def __init__(self):
        self.errors, self.warnings, self.stats = [], [], {}

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def load_json(path, schema, rep):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        rep.err(str(path), f"не читается: {e}")
        return None
    errs = sorted(jsonschema.Draft202012Validator(SCHEMAS[schema]).iter_errors(data), key=lambda e: list(e.path))
    for e in errs:
        rep.err(str(path), f"схема {schema}: {'/'.join(map(str, e.path)) or '<корень>'}: {e.message}")
    return data if not errs else None


def norm(text):
    return ca_runner._normalize(text or "", "strip")


RUN_TIMEOUT_S = 5
_CHILD = """
import json, sys, tempfile
sys.path.insert(0, sys.argv[1])
import ca_runner
req = json.loads(sys.stdin.read())
with tempfile.TemporaryDirectory() as d:
    if req["mode"] == "run":
        sys.__stdout__.write(ca_runner.run(req["code"], d, req["stdin"], 65536))
    else:
        sys.__stdout__.write(ca_runner.check(req["code"], json.dumps(req["tests"]), d, 65536))
"""


def _child(req):
    """Код ученика/контента — в отдельном процессе с таймаутом: бесконечный цикл не вешает валидатор."""
    import subprocess
    try:
        p = subprocess.run([sys.executable, "-c", _CHILD, str(RUNNER_DIR)], input=json.dumps(req), capture_output=True,
                           text=True, timeout=RUN_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None
    return json.loads(p.stdout)


def run_code(code, stdin=""):
    r = _child({"mode": "run", "code": code, "stdin": stdin})
    return r if r is not None else {"status": "TIMEOUT", "stdout": "", "stderr": f"превышено время ({RUN_TIMEOUT_S} с)"}


# ---------------------------------------------------------------------------
# Другие языки
# ---------------------------------------------------------------------------

WEB_LANGS = {"html", "js", "sql", "kotlin"}
EXT_LANG = {"py": "python", "html": "html", "htm": "html", "js": "js", "sql": "sql", "kt": "kotlin", "kts": "kotlin"}
KINDS = {
    "python": {"stdout", "function", "answer", "fastapi"},
    "html": {"web", "answer"}, "js": {"web", "answer"}, "sql": {"sql", "answer"}, "kotlin": {"kotlin", "answer"},
}


def lang_of_file(path):
    return EXT_LANG.get(path.rsplit(".", 1)[-1].lower(), "python")


class WebJobs:
    """Задания для веб-раннера копятся и выполняются одним запуском браузера (это быстро)."""

    def __init__(self):
        self.jobs, self.callbacks = [], []

    def add(self, job, callback):
        job["id"] = f"j{len(self.jobs) + 1}"
        self.jobs.append(job)
        self.callbacks.append((job["id"], callback))

    def run(self, rep):
        if not self.jobs:
            return
        runner = ROOT / "web-runner" / "tools" / "run-jobs.mjs"
        # WEBRUNNER_ASSETS — для локальной частичной сборки (только host.js: проверяются html/js).
        assets = pathlib.Path(os.environ.get("WEBRUNNER_ASSETS") or ROOT / "app" / "src" / "main" / "assets" / "webrunner")
        if not (assets / "host.js").exists() or (not os.environ.get("WEBRUNNER_ASSETS") and not (assets / "sql-worker.js").exists()):
            rep.err("web-runner", f"веб-раннер не собран ({len(self.jobs)} проверок не выполнено): cd web-runner && npm install && npm run build")
            return
        with tempfile.TemporaryDirectory() as d:
            jp, op = pathlib.Path(d, "jobs.json"), pathlib.Path(d, "out.json")
            jp.write_text(json.dumps(self.jobs, ensure_ascii=False), "utf-8")
            p = subprocess.run(["node", str(runner), str(jp), str(op), str(assets.parent)], capture_output=True, text=True, timeout=1800)
            if p.returncode != 0 or not op.exists():
                rep.err("web-runner", f"запуск не удался: {(p.stderr or p.stdout)[-800:]}")
                return
            results = json.loads(op.read_text("utf-8"))
        if results.get("__network"):
            rep.err("web-runner", f"контент обращался к сети: {results['__network'][:5]}")
        for jid, cb in self.callbacks:
            cb(results.get(jid) or {"error": "нет результата"})


def find_kotlinc():
    return os.environ.get("KOTLINC") or shutil.which("kotlinc")


_KT_CACHE = {}


def run_kotlin(code, compile_only=False):
    """Компиляция (и запуск, если есть main) настоящим kotlinc. None — kotlinc не найден."""
    kotlinc = find_kotlinc()
    if not kotlinc:
        return None
    key = (code, compile_only)
    if key in _KT_CACHE:
        return _KT_CACHE[key]
    with tempfile.TemporaryDirectory() as d:
        src = pathlib.Path(d, "Main.kt")
        src.write_text(code, "utf-8")
        out = pathlib.Path(d, "out")
        try:
            c = subprocess.run([kotlinc, str(src), "-d", str(out), "-nowarn"], capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            return {"status": "TIMEOUT", "stdout": "", "stderr": "kotlinc: превышено время"}
        if c.returncode != 0:
            res = {"status": "SYNTAX_ERROR", "stdout": "", "stderr": c.stderr}
        elif compile_only or not re.search(r"^\s*fun\s+main\s*\(", code, re.M):
            res = {"status": "OK", "stdout": "", "stderr": ""}
        else:
            kotlin = str(pathlib.Path(kotlinc).with_name("kotlin"))
            try:
                r = subprocess.run([kotlin, "-cp", str(out), "MainKt"], capture_output=True, text=True, timeout=60)
                res = {"status": "OK" if r.returncode == 0 else "ERROR", "stdout": r.stdout, "stderr": r.stderr}
            except subprocess.TimeoutExpired:
                res = {"status": "TIMEOUT", "stdout": "", "stderr": "превышено время"}
    _KT_CACHE[key] = res
    return res


JOBS = WebJobs()
# --no-run: только схемы, структура и озвучка (без запуска кода) — для коммита озвучки,
# где нет веб-раннера, FastAPI и kotlinc. Полная проверка — в workflow «Android».
NO_RUN = False


def check_code(code, tests):
    r = _child({"mode": "check", "code": code, "tests": tests})
    return r if r is not None else {"allPassed": False, "timeout": True}


class Deferred:
    """Запуск в веб-раннере: результат придёт после общего прогона."""

    def __init__(self, job):
        self.job = job


def _as_run(res):
    if res.get("timeout"):
        return {"status": "TIMEOUT", "stdout": "", "stderr": "превышено время"}
    if "result" in res:
        return res["result"]
    return {"status": "ERROR", "stdout": "", "stderr": res.get("error", "нет результата")}


def compare_output(rep, where, i, a, last):
    if a.get("stream") == "stderr":
        if last["status"] == "OK" and not last["stderr"].strip():
            rep.err(where, f"действие {i}: анимация показывает ошибку, а код выполнился без ошибок и предупреждений")
        else:
            full = last["stdout"] + last["stderr"]
            missing = [ln.strip() for ln in a["text"].splitlines() if ln.strip() and ln.strip() != "…" and ln.strip() not in full]
            if missing:
                rep.err(where, f"действие {i}: в сообщении об ошибке нет {missing!r}; фактически: {last['stderr'].strip()[-300:]!r}")
    elif last["status"] != "OK":
        rep.err(where, f"действие {i}: код сцены упал ({last['status']}): {last['stderr'].strip()[-300:]}")
    elif norm(last["stdout"]) != norm(a["text"]):
        rep.err(where, f"действие {i}: анимация покажет {a['text']!r}, а код выводит {last['stdout']!r}")


PREVIEW = "Предпросмотр страницы:\n"


def _compare_preview(rep, where, i, a, res):
    try:
        actual = res["check"]["cases"][0]["actual"]
    except (KeyError, IndexError, TypeError):
        rep.err(where, f"действие {i}: страница не отрисовалась: {str(res)[:300]}")
        return
    if norm(PREVIEW + str(actual)) != norm(a["text"]):
        rep.err(where, f"действие {i}: анимация покажет {a['text']!r}, а на странице {actual!r}")


def start_run(rep, where, lang, code, files, entry, stdin=""):
    """Запуск кода сцены на языке урока: dict (сразу), Deferred (веб-раннер) или None (нечем проверить)."""
    if NO_RUN:
        return None
    if lang == "python":
        return run_code(code, stdin)
    if lang == "kotlin":
        r = run_kotlin(code)
        if r is None:
            rep.warn(where, "kotlinc не найден — вывод программы на Kotlin не проверен")
        return r
    job = {"lang": lang, "mode": "run", "code": code, "stdin": stdin, "entry": entry}
    if lang == "html":
        job["files"] = dict(files)
    if lang == "sql" and entry != "schema.sql" and "schema.sql" in files:
        job["setup"] = files["schema.sql"]  # как в IDE: schema.sql выполняется перед запуском
    return Deferred(job)


def validate_scenario(path, scen, rep):
    files, last, words = {}, None, 0
    for scene in scen["scenes"]:
        where = f"{path}#{scene['id']}"
        words += len(re.findall(r"\w+", scene["narration"]))
        # Привязка к фразам озвучки: номер фразы существует и не идёт назад.
        n_phr = len(split_phrases(scene["narration"]))
        prev_cue = -1
        for i, a in enumerate(scene["actions"]):
            if "cue" in a:
                if a["cue"] >= n_phr:
                    rep.err(where, f"действие {i}: cue={a['cue']}, а фраз в озвучке {n_phr}")
                elif a["cue"] < prev_cue:
                    rep.err(where, f"действие {i}: cue={a['cue']} раньше предыдущего ({prev_cue})")
                prev_cue = max(prev_cue, a["cue"])
        for i, a in enumerate(scene["actions"]):
            f = a.get("file", "main.py")
            t = a["type"]
            if t == "clear":
                files[f] = ""
            elif t == "type":
                files[f] = files.get(f, "") + a["text"]
            elif t == "run":
                rf = a.get("file", "main.py")
                last = start_run(rep, where, lang_of_file(rf), files.get(rf, ""), files, rf, a.get("stdin", ""))
                if last is None:
                    last = "skip"
            elif t == "output":
                if last is None:
                    rep.err(where, f"действие {i}: output без предшествующего run")
                elif isinstance(last, Deferred) and last.job["lang"] == "html" and a["text"].startswith(PREVIEW):
                    job = {"lang": "html", "mode": "check", "code": last.job["code"], "files": last.job.get("files"),
                           "entry": last.job.get("entry"),
                           "tests": {"kind": "web", "lang": "html", "cases": [{"id": "t", "expr": "document.body.innerText", "expected": None}]}}
                    JOBS.add(job, lambda res, w=where, n=i, act=a: _compare_preview(rep, w, n, act, res))
                elif isinstance(last, Deferred):
                    JOBS.add(last.job, lambda res, w=where, n=i, act=a: compare_output(rep, w, n, act, _as_run(res)))
                elif last != "skip":
                    compare_output(rep, where, i, a, last)
                last = None
            elif t == "highlight":
                n = len(files.get(f, "").splitlines())
                bad = [ln for ln in a["lines"] if ln > n]
                if bad:
                    rep.err(where, f"действие {i}: подсветка строк {bad}, а в файле {n} строк")
    minutes = words / WORDS_PER_MIN
    validate_audio(path.parent, scen, rep)
    return words, minutes


def validate_audio(ldir, scen, rep):
    """Озвучка (если уже сделана): совпадение сцен, наличие файлов, разумные тайминги, актуальность текста."""
    meta_path = ldir / "audio" / "narration.json"
    if not meta_path.exists():
        rep.warn(str(ldir), "озвучки ещё нет (появится после workflow «Narrate lessons»)")
        return
    meta = json.loads(meta_path.read_text("utf-8"))
    by_id = {s["id"]: s for s in meta.get("scenes", [])}
    for scene in scen["scenes"]:
        where = f"{meta_path}#{scene['id']}"
        m = by_id.get(scene["id"])
        if not m:
            rep.err(where, "нет озвучки сцены")
            continue
        if not (ldir / "audio" / m["file"]).exists():
            rep.err(where, f"нет файла {m['file']}")
        if m["durationMs"] <= 0 or not m["cues"]:
            rep.err(where, "пустая озвучка")
        prev_end = 0
        for c in m["cues"]:
            if not (prev_end <= c["startMs"] <= c["endMs"] <= m["durationMs"] + 50):
                rep.err(where, f"неверный тайминг фразы {c}")
            prev_end = c["endMs"]
        payload = json.dumps([scene["narration"], scene.get("stress", {})], ensure_ascii=False)
        if m.get("textHash") != hashlib.sha256(payload.encode()).hexdigest()[:16]:
            rep.warn(where, "текст сцены изменился после озвучки — озвучка будет пересобрана")
    extra = set(by_id) - {s["id"] for s in scen["scenes"]}
    if extra:
        rep.err(str(meta_path), f"озвучка лишних сцен: {sorted(extra)}")


def _check_answer_output(rep, where, tests, actual):
    if actual["status"] != "OK":
        rep.err(where, f"код для предсказания падает: {actual['stderr'][-300:]}")
    elif norm(actual["stdout"]) != norm(tests["expected_answer"]):
        rep.err(where, f"expected_answer {tests['expected_answer']!r} не совпадает с реальным выводом {actual['stdout']!r}")


def validate_web_assignment(path, a, rep, lang):
    """HTML/JS, SQL, Kotlin: проверка тем же веб-раннером, что в приложении."""
    where = str(path)
    tests = a["tests"]
    cases = tests["cases"]
    if not any(not c.get("hidden") for c in cases):
        rep.err(where, "нет видимых тестов")
    if tests["kind"] == "sql":
        if not any(c.get("hidden") for c in cases):
            rep.err(where, "у SQL-задания нет скрытых тестов (на других данных): «зашитый» ответ пройдёт")
        for c in cases:
            if not c.get("setup"):
                rep.err(where, f"случай {c['id']}: нет setup (таблиц и данных)")
            if "expected" not in c or "rows" not in c.get("expected", {}):
                rep.err(where, f"случай {c['id']}: нет expected.rows")
    if tests["kind"] == "web":
        if tests.get("lang", "html") not in ("html", "js"):
            rep.err(where, f"tests.lang={tests.get('lang')!r}: для веб-заданий допустимы html и js")
        if any(c.get("function") for c in cases) and not any(c.get("hidden") for c in cases):
            rep.err(where, "у задания с функцией нет скрытых тестов")
    run_lang = lang if lang != "html" or tests.get("lang") != "js" else "js"

    def expect(code, must_pass, label):
        def cb(res):
            rep_ = res.get("check")
            if rep_ is None:
                rep.err(where, f"{label}: проверка не выполнилась: {json.dumps(res, ensure_ascii=False)[:300]}")
            elif must_pass and not rep_.get("allPassed"):
                rep.err(where, f"{label} НЕ проходит тесты: {json.dumps(rep_, ensure_ascii=False)[:500]}")
            elif not must_pass and rep_.get("allPassed"):
                rep.err(where, f"{label} проходит все тесты — тесты не ловят эту ошибку")
        JOBS.add({"lang": run_lang, "mode": "check", "code": code, "tests": tests, "timeoutMs": 60000}, cb)

    expect(a["solution"], True, "эталонное решение")
    if a["type"] in ("fix", "complete"):
        expect(a["starterCode"], False, "заготовка")
    for w in a.get("wrongSolutions", []):
        expect(w["code"], False, f"типовая ошибка «{w['why']}»")
    if not a.get("wrongSolutions"):
        rep.err(where, "нет wrongSolutions — непроверено, что тесты ловят типовые ошибки")
    if lang == "kotlin":
        r = run_kotlin(a["solution"], compile_only=True)
        if r is None:
            rep.warn(where, "kotlinc не найден — компиляция эталона на Kotlin не проверена")
        elif r["status"] != "OK":
            rep.err(where, f"эталон на Kotlin не компилируется: {r['stderr'][-400:]}")
        # Поведение эталона (только CI, настоящим kotlinc): tests.jvm = {main, expected_stdout}.
        jvm = a["tests"].get("jvm")
        if jvm and r is not None and r["status"] == "OK":
            rr = run_kotlin(a["solution"].rstrip() + "\n\n" + jvm["main"].strip() + "\n")
            if rr["status"] != "OK":
                rep.err(where, f"эталон на Kotlin упал при запуске: {rr['stderr'][-400:]}")
            elif norm(rr["stdout"]) != norm(jvm["expected_stdout"]):
                rep.err(where, f"эталон на Kotlin выводит {rr['stdout']!r}, а ожидается {jvm['expected_stdout']!r}")


def validate_assignment(path, a, rep, lang="python"):
    where = str(path)
    tests = a["tests"]
    if tests["kind"] not in KINDS.get(lang, KINDS["python"]):
        rep.err(where, f"вид тестов {tests['kind']!r} не подходит для языка урока {lang!r}")
        return
    if tests["kind"] in ("web", "sql", "kotlin"):
        validate_web_assignment(path, a, rep, lang)
        return
    if tests["kind"] == "answer":
        if lang == "python":
            _check_answer_output(rep, where, tests, run_code(a["code"]))
        elif lang == "html":
            pass  # ответ — вид страницы, а не вывод; сверяется скриптом урока по настоящему рендеру
        elif lang == "sql":
            # Ответ — строки результата последнего запроса (столбцы через « | »): сверяем тем же ядром SQL.
            def val(x):
                for t in (int, float):
                    try:
                        return t(x)
                    except ValueError:
                        pass
                return x
            rows = [[val(v.strip()) for v in ln.split(" | ")] for ln in tests["expected_answer"].strip().splitlines()]
            job = {"lang": "sql", "mode": "check", "code": a["code"],
                   "tests": {"kind": "sql", "ordered": True, "cases": [{"id": "answer", "setup": "", "expected": {"rows": rows}}]}}
            def cb(res, rows=rows):
                rep_ = (res or {}).get("check") or {}
                if not rep_.get("allPassed"):
                    rep.err(where, f"expected_answer не совпадает с результатом запроса: {json.dumps(rep_, ensure_ascii=False)[:400]}")
            JOBS.add(job, cb)
        else:
            r = start_run(rep, where, lang, a["code"], {}, None)
            if isinstance(r, Deferred):
                JOBS.add(r.job, lambda res: _check_answer_output(rep, where, tests, _as_run(res)))
            elif r is not None:
                _check_answer_output(rep, where, tests, r)
        if norm(a["solution"]) != norm(tests["expected_answer"]):
            rep.err(where, "solution не совпадает с expected_answer")
        for w in a.get("wrongSolutions", []):
            if norm(w.get("answer", w["code"])) == norm(tests["expected_answer"]):
                rep.err(where, f"неверный ответ «{w['why']}» засчитывается как верный")
        return
    cases = tests["cases"]
    visible = [c for c in cases if not c.get("hidden")]
    hidden = [c for c in cases if c.get("hidden")]
    if not visible:
        rep.err(where, "нет видимых тестов")
    if tests["kind"] in ("function", "fastapi") and not hidden:
        rep.err(where, f"у задания ({tests['kind']}) нет скрытых тестов")
    if tests["kind"] == "stdout" and any(c.get("stdin") for c in cases) and not hidden:
        rep.err(where, "задание с вводом без скрытых тестов: «зашитый» ответ пройдёт")
    r = check_code(a["solution"], tests)
    if not r.get("allPassed"):
        rep.err(where, f"эталонное решение НЕ проходит тесты: {json.dumps(r, ensure_ascii=False)[:400]}")
    if a["type"] in ("fix", "complete") and check_code(a["starterCode"], tests).get("allPassed"):
        rep.err(where, "заготовка уже проходит все тесты — задание бессмысленно")
    for w in a.get("wrongSolutions", []):
        if check_code(w["code"], tests).get("allPassed"):
            rep.err(where, f"тесты НЕ ловят типовую ошибку «{w['why']}»")
    if not a.get("wrongSolutions"):
        rep.err(where, "нет wrongSolutions — непроверено, что тесты ловят типовые ошибки")
    elif len(a["wrongSolutions"]) < 2:
        rep.warn(where, "меньше двух типовых неверных решений")


def validate_notes(path, rep):
    text = path.read_text(encoding="utf-8")
    if len(text.strip()) < 100:
        rep.err(str(path), "конспект слишком короткий")
    for i, block in enumerate(re.findall(r"```python\n(.*?)```", text, re.S)):
        r = run_code(block)
        if r["status"] != "OK":
            rep.err(str(path), f"блок кода {i + 1} не выполняется: {r['stderr'].strip()[-200:]}")


def validate_pack(pack_dir, rep):
    pack = load_json(pack_dir / "pack.json", "pack", rep)
    if not pack:
        return
    pstats = rep.stats.setdefault(pack["id"], {"lessons": {}})
    seen_assign = set()
    for lid in pack["lessons"]:
        ldir = pack_dir / "lessons" / lid
        lesson = load_json(ldir / "lesson.json", "lesson", rep)
        if not lesson:
            continue
        lesson_lang = lesson.get("runner", "W") if lesson.get("runner") in WEB_LANGS else "python"
        if lesson["id"] != lid:
            rep.err(str(ldir), f"id урока {lesson['id']!r} не совпадает с папкой {lid!r}")
        titles = pack.get("skills", {})
        for sk in lesson["skills"]:
            if sk not in titles:
                rep.err(str(ldir), f"навык {sk!r} без названия в pack.json → skills (нужно для карты знаний)")
        for ref in [lesson["scenario"], lesson["notes"], *lesson["assignments"]]:
            if not (ldir / ref).exists():
                rep.err(str(ldir), f"нет файла {ref}")
        st = {"assignments": len(lesson["assignments"])}
        if (ldir / lesson["scenario"]).exists():
            scen = load_json(ldir / lesson["scenario"], "scenario", rep)
            if scen:
                words, minutes = validate_scenario(ldir / lesson["scenario"], scen, rep)
                st.update(words=words, minutes=round(minutes, 1), scenes=len(scen["scenes"]))
                if minutes > MAX_MIN:
                    rep.err(str(ldir), f"озвучка ~{minutes:.1f} мин > {MAX_MIN} мин: разбейте урок")
                elif not WARN_MIN_LOW <= minutes <= WARN_MIN_HIGH:
                    rep.warn(str(ldir), f"озвучка ~{minutes:.1f} мин (ориентир ТЗ 6–8)")
        if (ldir / lesson["notes"]).exists() and not NO_RUN:
            validate_notes(ldir / lesson["notes"], rep)
        if lesson["passCriteria"]["minAssignmentsPassed"] > len(lesson["assignments"]):
            rep.err(str(ldir), "minAssignmentsPassed больше числа заданий")
        for ref in lesson["assignments"]:
            p = ldir / ref
            if not p.exists():
                continue
            a = load_json(p, "assignment", rep)
            if a:
                key = (lid, a["id"])
                if key in seen_assign:
                    rep.err(str(p), f"повтор id задания {a['id']}")
                seen_assign.add(key)
                if not NO_RUN:
                    validate_assignment(p, a, rep, lesson_lang)
        pstats["lessons"][lid] = st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("packs", type=pathlib.Path)
    ap.add_argument("--json", type=pathlib.Path)
    ap.add_argument("--require-kotlinc", action="store_true")
    ap.add_argument("--no-run", action="store_true", help="не запускать код (только схемы, структура, озвучка)")
    args = ap.parse_args()
    rep = Report()
    global NO_RUN
    NO_RUN = args.no_run
    packs = sorted(p.parent for p in args.packs.glob("*/pack.json"))
    if not packs:
        rep.err(str(args.packs), "не найдено ни одного pack.json")
    for p in packs:
        validate_pack(p, rep)
    JOBS.run(rep)
    if args.require_kotlinc and not find_kotlinc():
        rep.err("kotlinc", "kotlinc не найден, а проверка Kotlin обязательна (--require-kotlinc)")
    for w in rep.warnings:
        print("ПРЕДУПРЕЖДЕНИЕ", w)
    for e in rep.errors:
        print("ОШИБКА", e)
    print(json.dumps(rep.stats, ensure_ascii=False, indent=2))
    print(f"Итог: пакетов {len(packs)}, ошибок {len(rep.errors)}, предупреждений {len(rep.warnings)}")
    if args.json:
        args.json.write_text(json.dumps({"errors": rep.errors, "warnings": rep.warnings, "stats": rep.stats},
                                        ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())

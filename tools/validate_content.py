"""Валидатор контент-пакетов Code Academy (раздел 16 ТЗ: «не выпускать задания без тестов»).

Проверяет:
  1. Соответствие JSON Schema (пакет, урок, сценарий, задания).
  2. Сценарий анимированного урока: код из «видео» реально запускается и выводит
     ровно то, что покажет анимация.
  3. Задания: эталон проходит все тесты; заготовка (fix/complete) и типовые
     неверные решения — НЕ проходят; для predict ответ совпадает с реальным выводом.
  4. Конспект: все блоки ```python выполняются без ошибок.
  5. Длительность озвучки: ≤ 10 минут (ТЗ), предупреждение вне 3–8 минут.

Использование: python tools/validate_content.py content/packs [--json report.json]
Код возврата 1 при ошибках.
"""
import argparse
import json
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "src" / "main" / "python"))
import ca_runner  # noqa: E402
import jsonschema  # noqa: E402

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


def run_code(code, stdin=""):
    with tempfile.TemporaryDirectory() as d:
        return json.loads(ca_runner.run(code, d, stdin, 65536))


def check_code(code, tests):
    with tempfile.TemporaryDirectory() as d:
        return json.loads(ca_runner.check(code, json.dumps(tests), d, 65536))


def validate_scenario(path, scen, rep):
    files, last, words = {}, None, 0
    for scene in scen["scenes"]:
        where = f"{path}#{scene['id']}"
        words += len(re.findall(r"\w+", scene["narration"]))
        for i, a in enumerate(scene["actions"]):
            f = a.get("file", "main.py")
            t = a["type"]
            if t == "clear":
                files[f] = ""
            elif t == "type":
                files[f] = files.get(f, "") + a["text"]
            elif t == "run":
                last = run_code(files.get("main.py", ""), a.get("stdin", ""))
            elif t == "output":
                if last is None:
                    rep.err(where, f"действие {i}: output без предшествующего run")
                elif last["status"] != "OK":
                    rep.err(where, f"действие {i}: код сцены упал ({last['status']}): {last['stderr'].strip()[-200:]}")
                elif norm(last["stdout"]) != norm(a["text"]):
                    rep.err(where, f"действие {i}: анимация покажет {a['text']!r}, а код выводит {last['stdout']!r}")
                last = None
            elif t == "highlight":
                n = len(files.get(f, "").splitlines())
                bad = [ln for ln in a["lines"] if ln > n]
                if bad:
                    rep.err(where, f"действие {i}: подсветка строк {bad}, а в файле {n} строк")
    minutes = words / WORDS_PER_MIN
    return words, minutes


def validate_assignment(path, a, rep):
    where = str(path)
    tests = a["tests"]
    if tests["kind"] == "answer":
        actual = run_code(a["code"])
        if actual["status"] != "OK":
            rep.err(where, f"код для предсказания падает: {actual['stderr'][-200:]}")
        elif norm(actual["stdout"]) != norm(tests["expected_answer"]):
            rep.err(where, f"expected_answer {tests['expected_answer']!r} не совпадает с реальным выводом {actual['stdout']!r}")
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
    if tests["kind"] == "function" and not hidden:
        rep.err(where, "у задания с функцией нет скрытых тестов")
    if tests["kind"] == "stdout" and any(c.get("stdin") for c in cases) and not hidden:
        rep.warn(where, "задание с вводом без скрытых тестов: «зашитый» ответ пройдёт")
    r = check_code(a["solution"], tests)
    if not r.get("allPassed"):
        rep.err(where, f"эталонное решение НЕ проходит тесты: {json.dumps(r, ensure_ascii=False)[:400]}")
    if a["type"] in ("fix", "complete") and check_code(a["starterCode"], tests).get("allPassed"):
        rep.err(where, "заготовка уже проходит все тесты — задание бессмысленно")
    for w in a.get("wrongSolutions", []):
        if check_code(w["code"], tests).get("allPassed"):
            rep.err(where, f"тесты НЕ ловят типовую ошибку «{w['why']}»")
    if not a.get("wrongSolutions"):
        rep.warn(where, "нет wrongSolutions — непроверено, что тесты ловят типовые ошибки")


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
        if lesson["id"] != lid:
            rep.err(str(ldir), f"id урока {lesson['id']!r} не совпадает с папкой {lid!r}")
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
        if (ldir / lesson["notes"]).exists():
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
                validate_assignment(p, a, rep)
        pstats["lessons"][lid] = st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("packs", type=pathlib.Path)
    ap.add_argument("--json", type=pathlib.Path)
    args = ap.parse_args()
    rep = Report()
    packs = sorted(p.parent for p in args.packs.glob("*/pack.json"))
    if not packs:
        rep.err(str(args.packs), "не найдено ни одного pack.json")
    for p in packs:
        validate_pack(p, rep)
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

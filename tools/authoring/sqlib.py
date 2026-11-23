"""Помощник для уроков SQL: ожидаемые результаты считаются настоящим SQLite, эталон и типовые ошибки проверяются тем же ядром
(checkSql из web-runner), что и в приложении."""
import json
import subprocess

from mk import *


def expected(code, setup, columns=True):
    p = subprocess.run(["node", "--experimental-sqlite", "--no-warnings", "-e", """
const {DatabaseSync} = require('node:sqlite');
let s=''; process.stdin.on('data', d => s += d).on('end', () => {
  const {setup, code} = JSON.parse(s); const db = new DatabaseSync(':memory:'); db.exec('PRAGMA foreign_keys = ON'); db.exec(setup);
  const st = db.prepare(code.trim().replace(/;$/, '')); st.setReturnArrays(true);
  const cols = st.columns().map(c => c.name); const rows = st.all().map(r => r.map(v => typeof v === 'bigint' ? Number(v) : v));
  process.stdout.write(JSON.stringify({columns: cols, rows}));
});"""], input=json.dumps({"setup": setup, "code": code}), capture_output=True, text=True, check=True)
    e = json.loads(p.stdout)
    return e if columns else {"rows": e["rows"]}


def sq_out(q, setup):
    r = sql_out(q, setup)
    assert not r["stderr"], (q, r)
    return r["stdout"]


def sq_err(q, setup):
    return sql_out(q, setup)["stderr"]


def answer_rows(code, setup):
    """Ответ для задания «предскажи результат»: строки таблицы по одной в строке, значения через « | »."""
    rows = expected(code, setup, columns=False)["rows"]
    return "\n".join(" | ".join(str(v) for v in r) for r in rows)


def sql_task(id, type, title, statement, goal, solution, cases, wrongs, hints_, explanation, *, starter="-- Ваш запрос\n",
             ordered=False, query=None, check_columns=False, criteria=None, constraints=None,
             input_text="Таблицы создаются автоматически перед запуском.", expected_text="Таблица результата."):
    """cases: [(setup, hidden, hint)]; query — проверочный запрос после кода ученика (для INSERT/UPDATE/DELETE)."""
    tc = []
    for i, case in enumerate(cases):
        setup, hidden, hint = case[:3]
        q = case[3] if len(case) > 3 else query
        if q:
            exp = expected(q, setup + "\n" + solution, columns=False)
        else:
            exp = expected(solution, setup)
        c = {"id": ("h" if hidden else "v") + str(i + 1), "setup": setup}
        if q:
            c["query"] = q
        c["expected"] = exp
        if hidden:
            c["hidden"] = True
        if hint:
            c["hint"] = hint
        tc.append(c)
    tests = {"kind": "sql", "cases": tc}
    if ordered:
        tests["ordered"] = True
    if check_columns:
        tests["checkColumns"] = True

    def passes(code):
        return sql_check(code, tests).get("allPassed")

    assert passes(solution), (id, "эталон не проходит свои тесты", sql_check(solution, tests))
    for w, why in wrongs:
        assert not passes(w), (id, "тесты не ловят неверное решение", why)
    if type in ("fix", "complete"):
        assert not passes(starter), (id, "заготовка проходит")
    return asg(id, type, title, statement, goal, input_text, expected_text, constraints or [], hints_, tests, solution,
               explanation, criteria or ["Результат совпадает на всех наборах данных, включая скрытые."], wrongs,
               starter=starter)


def sql_predict(id, title, code, wrongs, hints_, explanation, *, statement="Что вернёт запрос? Запишите строки результата по одной в строке, значения через « | » (без заголовка таблицы)."):
    """code — скрипт: схема, данные и последний SELECT."""
    parts = code.rstrip().rstrip(";").rsplit(";", 1)
    setup, last = parts[0] + ";", parts[1].strip()
    ans = answer_rows(last, setup)
    for w, why in wrongs:
        assert w.strip() != ans.strip(), (id, "неверный ответ совпал с верным", why)
    return asg(id, "predict", title, statement, title, "—", "Строки результата.", [], hints_,
               {"kind": "answer", "expected_answer": ans}, ans, explanation, ["Правильные строки в правильном порядке."], wrongs, code=code)


def tests_sql_pack(pack_id, lessons, skills, title="Базы данных: SQL"):
    write_pack(pack_id, 9, title, "SQLite прямо в приложении: таблицы, запросы, агрегаты, соединения, изменение данных и проектирование.",
               "sql", lessons, skills)


def merge_pack(lesson_id, skills, pack_id="sql-basics"):
    """Добавить урок и навыки в pack.json пакета (остальное не трогаем)."""
    f = ROOT / "content/packs" / pack_id / "pack.json"
    data = json.loads(f.read_text("utf-8"))
    if lesson_id not in data["lessons"]:
        data["lessons"].append(lesson_id)
    data["skills"].update(skills)
    data["description"] = "SQLite прямо в приложении: таблицы, запросы, агрегаты, соединения, изменение данных и проектирование."
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

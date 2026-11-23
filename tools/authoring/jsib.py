"""Помощники для уроков JavaScript: задания-функции, предсказание вывода, запуск кода тем же раннером."""
from webib import *


def js_run(code):
    r = web_out("js", code)
    assert not r["stderr"], (code, r["stderr"])
    return r["stdout"].rstrip("\n")


def js_err(code):
    return web_out("js", code)["stderr"]


def fn_task(id, type, title, statement, goal, fname, cases, solution, starter, wrongs, hints_, explanation, *,
            visible=2, constraints=None, criteria=None, input_text="Аргументы функции.", expected_text="Возвращаемое значение."):
    """cases: [(args, expected)] или [(args, expected, подсказка)]; первые `visible` видны, остальные скрыты."""
    tc = []
    for i, c in enumerate(cases):
        args, exp = c[0], c[1]
        d = {"id": ("v" if i < visible else "h") + str(i + 1), "function": fname, "args": args, "expected": exp}
        if i >= visible:
            d["hidden"] = True
            if len(c) > 2:
                d["hint"] = c[2]
        tc.append(d)
    tests = {"kind": "web", "lang": "js", "cases": tc}
    a = asg(id, type, title, statement, goal, input_text, expected_text, constraints or [], hints_, tests, solution, explanation,
            criteria or ["Результат верен на всех наборах, включая скрытые."], wrongs, starter=starter)
    web_verify("js", a)
    return a


def stdout_task(id, type, title, statement, goal, cases, solution, starter, wrongs, hints_, explanation, *,
                visible=1, constraints=None, criteria=None):
    """cases: [(stdin_или_'', expected_stdout)] — проверка вывода консоли."""
    tc = []
    for i, c in enumerate(cases):
        d = {"id": ("v" if i < visible else "h") + str(i + 1), "expected_stdout": c[1]}
        if c[0]:
            d["stdin"] = c[0]
        if i >= visible:
            d["hidden"] = True
        tc.append(d)
    tests = {"kind": "web", "lang": "js", "cases": tc}
    a = asg(id, type, title, statement, goal, "—", "Вывод в консоль.", constraints or [], hints_, tests, solution, explanation,
            criteria or ["Вывод совпадает."], wrongs, starter=starter)
    web_verify("js", a)
    return a


def predict_js(id, title, code, wrongs, hints_, explanation, *, statement="Что выведет программа? Каждая строка вывода — с новой строки."):
    ans = js_run(code)
    for w, why in wrongs:
        assert w.strip() != ans.strip(), (id, "неверный ответ совпал с верным", why)
    return asg(id, "predict", title, statement, title, "—", "Строки вывода.", [], hints_,
               {"kind": "answer", "expected_answer": ans}, ans, explanation, ["Все строки верны."], wrongs, code=code)

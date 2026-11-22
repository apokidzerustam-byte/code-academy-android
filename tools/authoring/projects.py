"""Учебные проекты: сквозной «Мои задачи и финансы» (этапы 1–2) и мини-проекты.
Ожидаемый вывод в тестах — настоящий запуск эталона в песочнице ca_runner (Python) или веб-раннере (HTML)."""
import json
import sys
import tempfile

from mk import ROOT, hints, web_jobs

sys.path.insert(0, str(ROOT / "app/src/main/python"))
import ca_runner  # noqa: E402


def py_out(files, stdin, entry="main.py"):
    """Вывод программы так, как его увидит проверка."""
    d = tempfile.mkdtemp()
    ca_runner.write_files(d, json.dumps(files))
    r = json.loads(ca_runner.run(files[entry], d, stdin, 65536, entry))
    assert r["status"] == "OK", r
    return r["stdout"]


def cases_from(files, inputs, entry="main.py"):
    """Тесты stdout по эталону: [(id, stdin, hidden, hint)]."""
    out = []
    for cid, stdin, hidden, hint in inputs:
        c = {"id": cid, "file": entry, "stdin": stdin, "expected_stdout": py_out(files, stdin, entry)}
        if hidden:
            c["hidden"] = True
        if hint:
            c["hint"] = hint
        out.append(c)
    return out


def py_check(files, tests):
    d = tempfile.mkdtemp()
    return json.loads(ca_runner.check(json.dumps(files), json.dumps(tests), d, 65536))


def web_check_files(files, tests):
    entry = tests.get("entry", "index.html")
    job = {"lang": "html", "mode": "check", "code": files[entry], "files": files, "entry": entry, "tests": tests}
    r = web_jobs([job])[0]
    return r.get("check") or r


def milestone(id, title, statement, goal, hints_, tests, solution, explanation, criteria, wrong, starter=None, after=None):
    m = {"id": id, "title": title}
    if after:
        m["afterLesson"] = after
    m.update({"statement": statement, "goal": goal})
    if starter:
        m["starterFiles"] = starter
    m.update({"hints": hints_, "tests": tests, "solutionFiles": solution, "explanation": explanation,
              "criteria": criteria, "wrongSolutions": [{"files": f, "why": w} for f, w in wrong]})
    return m


def verify(project):
    """Эталон этапа проходит; заготовка (эталон прошлого этапа + новые файлы) и типовые ошибки — нет."""
    check = py_check if project["language"] == "python" else web_check_files
    prev = {}
    for m in project["milestones"]:
        start = dict(prev)
        for p, t in m.get("starterFiles", {}).items():
            start.setdefault(p, t)
        good = check(m["solutionFiles"], m["tests"])
        assert good.get("allPassed"), (project["id"], m["id"], "эталон не проходит", json.dumps(good, ensure_ascii=False)[:1500])
        if start:
            bad = check(start, m["tests"])
            assert not bad.get("allPassed"), (project["id"], m["id"], "заготовка проходит")
        for w in m["wrongSolutions"]:
            r = check(w["files"], m["tests"])
            assert not r.get("allPassed"), (project["id"], m["id"], "неверное решение проходит", w["why"])
        prev = m["solutionFiles"]


def write_project(pack_id, project):
    verify(project)
    d = ROOT / "content/packs" / pack_id / "projects" / project["id"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", "utf-8")
    pf = ROOT / "content/packs" / pack_id / "pack.json"
    pack = json.loads(pf.read_text("utf-8"))
    ids = pack.get("projects", [])
    if project["id"] not in ids:
        ids.append(project["id"])
    pack["projects"] = ids
    pf.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"{pack_id}/{project['id']}: этапов {len(project['milestones'])}, "
          f"тестов {sum(len(m['tests']['cases']) for m in project['milestones'])}")


# =====================================================================================
# Сквозной проект «Мои задачи и финансы»: этап 1 — калькулятор, этап 2 — учёт расходов.
# =====================================================================================
CALC_IN = 'a = float(input("Первое число: "))\nop = input("Действие (+ - * /): ")\nb = float(input("Второе число: "))\n'
CALC_BODY = '''if op == "+":
    print("Результат:", round(a + b, 2))
elif op == "-":
    print("Результат:", round(a - b, 2))
elif op == "*":
    print("Результат:", round(a * b, 2))
elif op == "/":
    if b == 0:
        print("На ноль делить нельзя")
    else:
        print("Результат:", round(a / b, 2))
else:
    print("Неизвестное действие")
'''
CALC = "# Мои задачи и финансы — этап 1: калькулятор\n" + CALC_IN + CALC_BODY
calc_files = {"main.py": CALC}
calc_tests = {"kind": "project", "cases": cases_from(calc_files, [
    ("plus", "2\n+\n3\n", False, None),
    ("div", "7\n/\n2\n", False, None),
    ("mul", "5\n*\n1.5\n", False, None),
    ("minus", "10\n-\n12.5\n", False, None),
    ("zero", "1\n/\n0\n", True, "Деление на ноль: программа не должна падать"),
    ("unknown", "2\n^\n3\n", True, "Для неизвестного знака — сообщение «Неизвестное действие»"),
    ("third", "1\n/\n3\n", True, "Результат округляется до 2 знаков: round(…, 2)"),
])}
assert calc_tests["cases"][0]["expected_stdout"] == "Первое число: Действие (+ - * /): Второе число: Результат: 5.0\n"

m1 = milestone(
    "calculator", "Этап 1. Калькулятор",
    "Это первый шаг большого проекта: за курс он вырастет в приложение для задач и личных финансов.\n\n"
    "Напишите калькулятор в файле `main.py`. Программа спрашивает:\n\n"
    "1. `Первое число: `\n2. `Действие (+ - * /): `\n3. `Второе число: `\n\n"
    "и печатает `Результат: <число>` — результат округлён до 2 знаков (`round(…, 2)`).\n\n"
    "- Деление на ноль: `На ноль делить нельзя`.\n- Другой знак: `Неизвестное действие`.\n\n"
    "Пример: 7, `/`, 2 → `Результат: 3.5`.",
    "Числа с дробной частью, условия if/elif/else, проверка особых случаев.",
    hints("Три строки с input уже есть в заготовке — числа сразу превращаются в float.",
          "Для каждого знака — своя ветка: if op == \"+\": … elif op == \"-\": …",
          "Перед делением проверьте, не равен ли b нулю.",
          "Последняя ветка else — для всех остальных знаков.",
          "if op == \"/\":\n    if b == 0:\n        print(\"На ноль делить нельзя\")\n    else:\n        print(\"Результат:\", round(a / b, 2))"),
    calc_tests, calc_files,
    "Каждое действие — своя ветка elif; деление проверяет b == 0 до вычисления, иначе программа упадёт с ZeroDivisionError.",
    ["Четыре действия считаются верно.", "Деление на ноль не роняет программу.", "Неизвестный знак — понятное сообщение."],
    [({"main.py": CALC.replace('    if b == 0:\n        print("На ноль делить нельзя")\n    else:\n        print("Результат:", round(a / b, 2))',
                               '    print("Результат:", round(a / b, 2))')}, "Нет проверки деления на ноль: ZeroDivisionError."),
     ({"main.py": CALC.replace("float(input", "int(input")}, "int() не понимает дробные числа вроде 1.5."),
     ({"main.py": CALC.replace("round(a / b, 2)", "a / b")}, "Результат деления не округлён: 0.3333333333333333."),
     ({"main.py": CALC.replace('else:\n    print("Неизвестное действие")\n', "")}, "Для неизвестного знака программа молчит.")],
    starter={"main.py": "# Мои задачи и финансы — этап 1: калькулятор\n" + CALC_IN + "\n# Посчитайте результат\n"},
    after="py-06-conditions")

MENU_CALC = "    " + CALC_IN.replace("\n", "\n    ").rstrip() + "\n" + "".join("    " + ln + "\n" for ln in CALC_BODY.splitlines())
EXPENSES = '''    expenses = []
    while True:
        line = input("Сумма (пусто — конец): ")
        if line == "":
            break
        expenses.append(float(line))
    if len(expenses) == 0:
        print("Расходов нет")
    else:
        print("Покупок:", len(expenses))
        print("Всего:", round(sum(expenses), 2))
        print("Самая крупная:", max(expenses))
        print("В среднем:", round(sum(expenses) / len(expenses), 2))
'''
FIN = ('# Мои задачи и финансы — этап 2: меню и учёт расходов\nprint("1 — калькулятор")\nprint("2 — расходы")\n'
       'choice = input("Выбор: ")\nif choice == "1":\n' + MENU_CALC + 'elif choice == "2":\n' + EXPENSES +
       'else:\n    print("Нет такого пункта")\n')
fin_files = {"main.py": FIN}
fin_tests = {"kind": "project", "cases": cases_from(fin_files, [
    ("two", "2\n100\n50.5\n\n", False, None),
    ("none", "2\n\n", False, "Без покупок — «Расходов нет» (и никаких ошибок)"),
    ("calc", "1\n2\n+\n3\n", False, "Калькулятор из этапа 1 должен остаться в пункте 1"),
    ("menu", "3\n", False, None),
    ("three", "2\n10\n20\n30\n\n", True, None),
    ("calc-zero", "1\n5\n/\n0\n", True, "Пункт 1: деление на ноль по-прежнему без ошибки"),
    ("avg", "2\n1\n2\n2\n\n", True, "Среднее округляется до 2 знаков"),
])}
m2 = milestone(
    "expenses", "Этап 2. Меню и учёт расходов",
    "Проект растёт: теперь в `main.py` будет **меню**.\n\n"
    "```\n1 — калькулятор\n2 — расходы\nВыбор: \n```\n\n"
    "- `1` — ваш калькулятор из этапа 1 (тот же вывод).\n"
    "- `2` — учёт расходов: программа спрашивает `Сумма (пусто — конец): `, пока не введут пустую строку, "
    "затем печатает:\n\n```\nПокупок: 2\nВсего: 150.5\nСамая крупная: 100.0\nВ среднем: 75.25\n```\n\n"
    "  «Всего» и «В среднем» округлены до 2 знаков. Если сумм не было — `Расходов нет`.\n"
    "- Другой выбор — `Нет такого пункта`.",
    "Список, цикл while с выходом по пустой строке, sum/max/len, повторное использование кода.",
    hints("Сначала два print с пунктами меню и choice = input(\"Выбор: \").",
          "Код калькулятора переносится внутрь if choice == \"1\": — с отступом в 4 пробела.",
          "Для расходов: пустой список, while True и break, когда строка пустая.",
          "Каждую сумму превратите в float и добавьте в список: expenses.append(float(line)).",
          "Покупок — len(expenses), всего — sum, крупная — max, среднее — sum / len. Пустой список проверьте до вычислений."),
    fin_tests, fin_files,
    "Меню выбирает ветку по choice. Калькулятор переехал в первую ветку без изменений. Суммы копятся в списке, "
    "а итоги считают встроенные функции; пустой список проверяется заранее, иначе max() и деление упадут.",
    ["Калькулятор работает в пункте 1.", "Итоги расходов верные, пустой ввод не роняет программу."],
    [({"main.py": FIN.replace("    if len(expenses) == 0:\n        print(\"Расходов нет\")\n    else:\n", "    if True:\n")},
      "Нет проверки пустого списка: max() и деление на ноль падают."),
     ({"main.py": FIN.replace("round(sum(expenses) / len(expenses), 2)", "sum(expenses) / len(expenses)")},
      "Среднее не округлено: 1.6666666666666667."),
     ({"main.py": FIN.split('if choice == "1":')[0] + 'if choice == "2":\n' + EXPENSES + 'else:\n    print("Нет такого пункта")\n'},
      "Калькулятор потерялся: пункт 1 не работает.")],
    after="py-10-lists")

finance = {"id": "finance", "kind": "through", "title": "Мои задачи и финансы",
           "summary": "Сквозной проект курса: от калькулятора до приложения для задач и личных финансов. "
                      "Каждый этап программы добавляет к нему новые возможности.",
           "language": "python", "afterLesson": "py-06-conditions",
           "skills": ["python.if", "python.lists", "python.loops.while", "python.numbers", "python.builtins.aggregate"],
           "milestones": [m1, m2]}

# =====================================================================================
# Мини-проекты Python
# =====================================================================================
TERMO = '''c = float(input("Температура, °C: "))
f = c * 9 / 5 + 32
print("По Фаренгейту:", round(f, 1))
if c < 0:
    print("Мороз")
elif c < 15:
    print("Прохладно")
elif c < 25:
    print("Тепло")
else:
    print("Жарко")
'''
termo_files = {"main.py": TERMO}
termo_tests = {"kind": "project", "cases": cases_from(termo_files, [
    ("warm", "20\n", False, None), ("frost", "-5\n", False, None), ("body", "36.6\n", False, None),
    ("zero", "0\n", True, "0 °C — уже не мороз: мороз только ниже нуля"),
    ("b15", "15\n", True, "Ровно 15 °C — уже «Тепло»"), ("b25", "25\n", True, "Ровно 25 °C — уже «Жарко»"),
    ("minus40", "-40\n", True, None),
])}
thermo = {"id": "thermometer", "kind": "mini", "title": "Термометр",
          "summary": "Перевод температуры из Цельсия в Фаренгейт и подсказка, как одеться.",
          "language": "python", "afterLesson": "py-06-conditions", "skills": ["python.numbers", "python.if"],
          "milestones": [milestone(
              "main", "Термометр",
              "Программа спрашивает `Температура, °C: ` (число может быть дробным) и печатает:\n\n"
              "1. `По Фаренгейту: <F>` — по формуле F = C × 9 / 5 + 32, округлено до 1 знака;\n"
              "2. подсказку: ниже 0 — `Мороз`, от 0 до 15 (не включая 15) — `Прохладно`, от 15 до 25 (не включая 25) — `Тепло`, "
              "25 и выше — `Жарко`.\n\nПример: `20` → `По Фаренгейту: 68.0` и `Тепло`.",
              "Дробные числа, формула, цепочка if/elif/else с границами.",
              hints("Температура может быть дробной: float(input(…)).",
                    "Формула: f = c * 9 / 5 + 32, вывод — round(f, 1).",
                    "Условия проверяйте по порядку, от самого холодного.",
                    "«Ниже нуля» — c < 0; ноль уже не мороз.",
                    "if c < 0: … elif c < 15: … elif c < 25: … else: …"),
              termo_tests, termo_files,
              "Цепочка elif проверяет границы по возрастанию: каждая следующая ветка срабатывает, только если предыдущие не подошли.",
              ["Формула и округление верны.", "Границы 0, 15 и 25 обработаны как в условии."],
              [({"main.py": TERMO.replace("if c < 0", "if c <= 0")}, "Ноль попал в «Мороз»."),
               ({"main.py": TERMO.replace("float(input", "int(input")}, "int() не принимает 36.6."),
               ({"main.py": TERMO.replace("round(f, 1)", "f")}, "Нет округления: 97.88000000000001."),
               ({"main.py": TERMO.replace("elif c < 25", "elif c <= 25")}, "25 °C попало в «Тепло».")],
              starter={"main.py": 'c = float(input("Температура, °C: "))\n# Переведите в Фаренгейт и дайте подсказку\n'})]}

QUIZ = '''score = 0

answer = input("Сколько будет 7 * 8? ")
if answer.strip() == "56":
    print("Верно!")
    score = score + 1
else:
    print("Неверно, правильный ответ: 56")

answer = input("Столица Франции? ")
if answer.strip().lower() == "париж":
    print("Верно!")
    score = score + 1
else:
    print("Неверно, правильный ответ: Париж")

answer = input("Python — язык программирования? (да/нет) ")
if answer.strip().lower() == "да":
    print("Верно!")
    score = score + 1
else:
    print("Неверно, правильный ответ: да")

print("Результат:", score, "из 3")
if score == 3:
    print("Отлично!")
elif score == 2:
    print("Хорошо")
else:
    print("Попробуйте ещё раз")
'''
QUIZ_STARTER = QUIZ.split('answer = input("Столица Франции? ")')[0] + (
    "# Вопрос 2: «Столица Франции? » — ответ Париж (подходят любые буквы: париж, ПАРИЖ)\n"
    "# Вопрос 3: «Python — язык программирования? (да/нет) » — ответ да\n"
    "# Итог: «Результат: N из 3» и оценка\n")
quiz_files = {"main.py": QUIZ}
quiz_tests = {"kind": "project", "cases": cases_from(quiz_files, [
    ("all", "56\nпариж\nДа\n", False, None),
    ("two", "56\nЛондон\nда\n", False, None),
    ("none", "54\nРим\nнет\n", False, None),
    ("spaces", "  56 \n  ПАРИЖ \nнет\n", True, "Пробелы по краям и большие буквы не делают ответ неверным: strip() и lower()"),
    ("one", "1\nПариж\nнет\n", True, "Один верный ответ — «Попробуйте ещё раз»"),
])}
quiz = {"id": "quiz", "kind": "mini", "title": "Викторина",
        "summary": "Три вопроса, подсчёт очков и итоговая оценка.",
        "language": "python", "afterLesson": "py-07-logic", "skills": ["python.if", "python.strings.methods"],
        "milestones": [milestone(
            "main", "Викторина",
            "Первый вопрос уже написан в заготовке. Добавьте ещё два — точно с такими вопросами:\n\n"
            "1. `Столица Франции? ` — ответ `Париж`;\n2. `Python — язык программирования? (да/нет) ` — ответ `да`.\n\n"
            "На верный ответ — `Верно!` и +1 очко, на неверный — `Неверно, правильный ответ: <ответ>`. "
            "Большие буквы и пробелы по краям ответа не важны.\n\n"
            "В конце: `Результат: N из 3` и оценка: 3 — `Отлично!`, 2 — `Хорошо`, иначе — `Попробуйте ещё раз`.",
            "Сравнение строк, методы strip() и lower(), счётчик, условия.",
            hints("Скопируйте блок первого вопроса и поменяйте текст и ответ.",
                  "Ответ «париж» и «ПАРИЖ» должны засчитываться: сравнивайте answer.strip().lower().",
                  "Правильный ответ в сравнении пишите маленькими буквами: \"париж\".",
                  "Итог: print(\"Результат:\", score, \"из 3\").",
                  "if score == 3: print(\"Отлично!\") elif score == 2: print(\"Хорошо\") else: print(\"Попробуйте ещё раз\")"),
            quiz_tests, quiz_files,
            "strip() убирает пробелы, lower() — большие буквы: так ответ сравнивается по смыслу. Счётчик score растёт только в ветке «Верно!».",
            ["Все три вопроса.", "Ответ не зависит от регистра и пробелов.", "Верная итоговая оценка."],
            [({"main.py": QUIZ.replace('answer.strip().lower() == "париж"', 'answer == "Париж"')}, "«париж» маленькими буквами не засчитывается."),
             ({"main.py": QUIZ.replace("elif score == 2", "elif score >= 1")}, "Один верный ответ получает «Хорошо»."),
             ({"main.py": QUIZ.replace('    print("Верно!")\n    score = score + 1\nelse:\n    print("Неверно, правильный ответ: да")',
                                       '    print("Верно!")\nelse:\n    print("Неверно, правильный ответ: да")')},
              "За третий вопрос очко не начисляется.")],
            starter={"main.py": QUIZ_STARTER})]}

SHOP1 = '''items = []
while True:
    item = input("Товар (пусто — конец): ")
    if item == "":
        break
    items.append(item)
print("В списке:", len(items))
n = 1
for item in items:
    print(str(n) + ".", item)
    n = n + 1
'''
SHOP2 = '''items = []
while True:
    item = input("Товар (пусто — конец): ").strip().lower()
    if item == "":
        break
    if item in items:
        print("Уже есть:", item)
    else:
        items.append(item)
if len(items) == 0:
    print("Список пуст")
else:
    print("В списке:", len(items))
    n = 1
    for item in items:
        print(str(n) + ".", item)
        n = n + 1
'''
shop1_tests = {"kind": "project", "cases": cases_from({"main.py": SHOP1}, [
    ("three", "хлеб\nкефир\nсыр\n\n", False, None), ("one", "чай\n\n", False, None),
    ("many", "a\nb\nc\nd\ne\n\n", True, "Номера идут подряд: 1., 2., 3., …"),
])}
shop2_tests = {"kind": "project", "cases": cases_from({"main.py": SHOP2}, [
    ("dup", "хлеб\nкефир\nхлеб\n\n", False, None),
    ("case", "Сыр\n сыр \nчай\n\n", False, "«Сыр» и « сыр » — один товар: strip() и lower()"),
    ("empty", "\n", False, None),
    ("same", "чай\nчай\nчай\n\n", True, None),
    ("plain", "яблоки\nгруши\n\n", True, None),
])}
shopping = {"id": "shopping", "kind": "mini", "title": "Список покупок",
            "summary": "Список покупок с нумерацией, а потом — без повторов.",
            "language": "python", "afterLesson": "py-10-lists", "skills": ["python.lists", "python.loops.while", "python.loops.for"],
            "milestones": [
                milestone("collect", "Этап 1. Собрать список",
                          "Программа спрашивает `Товар (пусто — конец): `, пока не введут пустую строку. "
                          "Потом печатает `В списке: N` и товары с номерами:\n\n```\nВ списке: 2\n1. хлеб\n2. кефир\n```",
                          "Список, цикл while с break, обход списка for.",
                          hints("Начните с пустого списка: items = [].",
                                "while True: … и break, когда товар — пустая строка.",
                                "Добавление: items.append(item).",
                                "Номер — отдельная переменная n, которая растёт в цикле for.",
                                "print(str(n) + \".\", item) печатает «1. хлеб»."),
                          shop1_tests, {"main.py": SHOP1},
                          "while собирает товары до пустой строки, for печатает их с номером; str(n) + \".\" склеивает номер с точкой без пробела.",
                          ["Количество верное.", "Нумерация с 1, формат «1. товар»."],
                          [({"main.py": SHOP1.replace("n = 1\n", "n = 0\n")}, "Нумерация начинается с 0."),
                           ({"main.py": SHOP1.replace('print(str(n) + ".", item)', 'print(n, ".", item)')}, "Лишний пробел: «1 . хлеб»."),
                           ({"main.py": SHOP1.replace("len(items)", "n")}, "Количество печатается неверно.")],
                          starter={"main.py": 'items = []\n# Спрашивайте «Товар (пусто — конец): », пока не введут пустую строку\n'}),
                milestone("unique", "Этап 2. Без повторов",
                          "Улучшим список:\n\n- товар приводится к виду без пробелов по краям и маленькими буквами (`strip().lower()`);\n"
                          "- если такой товар уже есть — печатается `Уже есть: <товар>`, и он не добавляется;\n"
                          "- если список пуст — вместо итогов печатается `Список пуст`.",
                          "Проверка «есть ли в списке» (in), методы строк, особый случай пустого списка.",
                          hints("Приведите товар сразу после input: input(…).strip().lower().",
                                "Проверка повтора: if item in items:.",
                                "Добавляйте товар только в ветке else.",
                                "Пустой список: if len(items) == 0: print(\"Список пуст\").",
                                "Итоги (количество и нумерация) — в ветке else после проверки пустого списка."),
                          shop2_tests, {"main.py": SHOP2},
                          "in проверяет, есть ли значение в списке; благодаря strip().lower() «Сыр» и « сыр » считаются одним товаром.",
                          ["Повторы не добавляются и называются.", "Пустой список — «Список пуст»."],
                          [({"main.py": SHOP2.replace(".strip().lower()", "")}, "«Сыр» и «сыр» считаются разными товарами."),
                           ({"main.py": SHOP2.replace('if len(items) == 0:\n    print("Список пуст")\nelse:\n', "if True:\n")},
                            "Для пустого списка печатается «В списке: 0»."),
                           ({"main.py": SHOP2.replace('        print("Уже есть:", item)\n', "        pass\n")}, "Повтор не называется.")],
                          after="py-10-lists"),
            ]}

# =====================================================================================
# Мини-проект веб: визитка (HTML + CSS + JS в трёх файлах)
# =====================================================================================
V_HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Визитка</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>Анна Смирнова</h1>
  <p>Учусь программировать.</p>
  <ul id="hobbies">
    <li>Python</li>
    <li>Велосипед</li>
    <li>Фотография</li>
  </ul>
  <button id="show">Контакты</button>
  <p id="contacts" class="hidden">anna@example.com</p>
  <script src="script.js"></script>
</body>
</html>
'''
V_CSS = "body {\n  font-family: sans-serif;\n  margin: 16px;\n}\n\nh1 {\n  color: teal;\n}\n\n.hidden {\n  display: none;\n}\n"
V_JS = ('const button = document.getElementById("show");\nconst contacts = document.getElementById("contacts");\n'
        'button.addEventListener("click", () => {\n  contacts.classList.toggle("hidden");\n});\n')
V_START_HTML = V_HTML.split("<body>")[0] + "<body>\n  <!-- Имя, пара слов о себе, список увлечений, кнопка и контакты -->\n  <script src=\"script.js\"></script>\n</body>\n</html>\n"
cs = "getComputedStyle(document.getElementById('contacts')).display"
CLICK = "document.getElementById('show').click();"
v_tests = {"kind": "web", "lang": "html", "entry": "index.html", "cases": [
    {"id": "name", "expr": "((document.querySelector('h1') || {}).textContent || '').trim().length > 0", "expected": True},
    {"id": "hobbies", "expr": "document.querySelectorAll('#hobbies li').length >= 3", "expected": True},
    {"id": "color", "expr": "getComputedStyle(document.querySelector('h1')).color !== 'rgb(0, 0, 0)'", "expected": True},
    {"id": "hidden", "expr": "!!document.getElementById('contacts') && " + cs + " === 'none'", "expected": True},
    {"id": "show", "before": CLICK, "expr": cs + " !== 'none'", "expected": True},
    {"id": "toggle", "hidden": True, "before": CLICK * 2, "expr": cs, "expected": "none",
     "hint": "Второе нажатие снова прячет контакты"},
    {"id": "email", "hidden": True, "expr": "(document.getElementById('contacts') || {}).textContent.includes('@')",
     "expected": True, "hint": "В контактах должен быть адрес почты с @"},
]}
v_sol = {"index.html": V_HTML, "style.css": V_CSS, "script.js": V_JS}
vizitka = {"id": "card", "kind": "mini", "title": "Визитка",
           "summary": "Страница о себе из трёх файлов: разметка, оформление и кнопка, которая показывает контакты.",
           "language": "html", "afterLesson": "web-02-js", "skills": ["web.html", "web.css", "js.dom", "js.events"],
           "milestones": [milestone(
               "main", "Визитка",
               "Сделайте страницу о себе из трёх файлов проекта:\n\n"
               "- `index.html`: заголовок `h1` с вашим именем, список увлечений `<ul id=\"hobbies\">` (не меньше 3 пунктов), "
               "кнопка `<button id=\"show\">` и абзац `<p id=\"contacts\">` с адресом почты;\n"
               "- `style.css`: цвет заголовка (не чёрный) и скрытый абзац контактов (`display: none`);\n"
               "- `script.js`: нажатие кнопки показывает контакты, следующее — снова прячет.\n\n"
               "Файлы `style.css` и `script.js` уже подключены в `index.html`.",
               "Проект из нескольких файлов: HTML, CSS и JavaScript вместе.",
               hints("Список: <ul id=\"hobbies\"> и три <li>.",
                     "Удобно прятать через класс: .hidden { display: none; } и <p id=\"contacts\" class=\"hidden\">.",
                     "В script.js найдите кнопку и абзац через document.getElementById.",
                     "classList.toggle(\"hidden\") добавляет класс, если его нет, и убирает, если есть.",
                     "button.addEventListener(\"click\", () => { contacts.classList.toggle(\"hidden\"); });"),
               v_tests, v_sol,
               "Класс hidden прячет абзац правилом CSS, а toggle по нажатию то добавляет, то убирает его — так кнопка работает как переключатель.",
               ["Имя, 3+ увлечения, цвет заголовка.", "Контакты скрыты и открываются кнопкой, второе нажатие прячет."],
               [(dict(v_sol, **{"style.css": V_CSS.replace(".hidden {\n  display: none;\n}\n", "")}), "Контакты видны сразу: нет правила display: none."),
                (dict(v_sol, **{"script.js": V_JS.replace('classList.toggle("hidden")', 'classList.remove("hidden")')}),
                 "Кнопка только показывает — второе нажатие не прячет."),
                (dict(v_sol, **{"index.html": V_HTML.replace("    <li>Фотография</li>\n", "")}), "В списке только 2 увлечения.")],
               starter={"index.html": V_START_HTML, "style.css": "/* Оформление */\n", "script.js": "// Кнопка «Контакты»\n"})]}

write_project("python-basics", finance)
write_project("python-basics", thermo)
write_project("python-basics", quiz)
write_project("python-basics", shopping)
write_project("web-basics", vizitka)

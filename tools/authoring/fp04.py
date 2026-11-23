from lib import *

begin()
scenes = [
 S("intro", "Качество — это проверка", """
  Проект готов не тогда, когда код написан, а когда вы можете доказать, что он работает. Для этого нужны тесты на самые важные
  функции: разбор ввода, расчёты, отчёты. Ошибки чаще всего живут на границах и в неожиданном вводе: ноль, минус, пустая
  строка, лишние пробелы. Сегодня мы напишем тесты для функций нашего проекта и научимся быстро находить причину падения.""",
  nt("Тестируем: разбор ввода, расчёты, отчёты · особенно границы", at="Для этого")),
 S("table", "Таблица тестов для разбора суммы", """
  Возьмём функцию, которая разбирает сумму из текста: она должна вернуть положительное число или None. Составим таблицу:
  входная строка и ожидаемый результат. В неё входят обычные значения, ноль, минус, не число и пустая строка. Запустим все
  случаи одним циклом и посмотрим на итог.""",
  clr(), t('def parse_amount(text):\n    try:\n        value = float(text)\n    except ValueError:\n        return None\n    return value if value > 0 else None\n\n\n', at="Возьмём"),
  t('cases = [("12.5", 12.5), ("0", None), ("-3", None), ("abc", None), ("", None), (" 7 ", 7.0)]\nfailed = 0\nfor text, expected in cases:\n    got = parse_amount(text)\n    if got != expected:\n        failed += 1\n        print("ошибка:", repr(text), got, expected)\nprint("не прошло:", failed)\n', at="Составим"), run("Запустим")),
 S("report", "Тест для отчёта", """
  Отчёт по категориям — главная функция проекта. Проверим её на нескольких наборах: обычном, с одной категорией и пустом. На
  пустом наборе функция должна вернуть пустой словарь, а не упасть. Такие тесты особенно полезны после рефакторинга:
  если отчёт изменился, они сразу сообщат.""",
  clr(), t('def totals(expenses):\n    result = {}\n    for amount, category in expenses:\n        result[category] = round(result.get(category, 0) + amount, 2)\n    return result\n\n\n', at="Проверим"),
  t('assert totals([]) == {}\nassert totals([(5, "a")]) == {"a": 5}\nassert totals([(1.5, "a"), (2, "b"), (0.5, "a")]) == {"a": 2.0, "b": 2}\nprint("отчёт ок")\n', at="На пустом"), run("На пустом")),
 S("debug", "Находим причину падения", """
  Тест упал. Что дальше? Не гадайте, а сузьте область поиска. Возьмём функцию, которая считает долю категории, но
  ошибается. Сначала воспроизведите проблему на самом коротком примере. Затем напечатайте промежуточные значения и найдите
  место, где они перестают быть ожидаемыми. Исправьте именно причину и добавьте тест, чтобы ошибка не вернулась.""",
  clr(), t('def share(part, total):\n    return round(part // total * 100, 1)\n\n\nprint(share(1, 4))\n', at="Возьмём"), run("Возьмём"),
  t('part, total = 1, 4\nprint(part // total, part / total)\n', at="Затем напечатайте"), run("Затем напечатайте")),
 S("regress", "Регрессионные тесты", """
  Исправив ошибку, превратите её в тест. Такой тест называют регрессионным: он гарантирует, что та же ошибка не появится
  снова при следующей правке. Напишите новый тест с входными данными, на которых программа ломалась. Так набор проверок
  постепенно растёт и всё надёжнее защищает проект.""",
  clr(), t('def share(part, total):\n    return round(part / total * 100, 1)\n\n\nassert share(1, 4) == 25.0\nassert share(1, 3) == 33.3\nprint("регрессия закрыта")\n', at="Исправив"), run("Исправив")),
 S("summary", "Итог", """
  Подведём итог. Тестируйте функции, которые разбирают ввод и считают результат. Включайте границы: ноль, минус, пусто. Ищите
  причину ошибки по шагам: воспроизведите, напечатайте промежуточные значения, исправьте. После исправления добавьте
  регрессионный тест. Теперь осталось показать проект людям: подготовить README и демонстрацию.""",
  nt("границы · по шагам · регрессионный тест", at="Подведём итог")),
]

notes = """
# Качество проекта

```python
def parse_amount(text):
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value > 0 else None

cases = [("12.5", 12.5), ("0", None), ("-3", None), ("abc", None), ("", None), (" 7 ", 7.0)]
for text, expected in cases:
    assert parse_amount(text) == expected, text
print("все тесты прошли")
```

Ошибка → воспроизвести → сузить → исправить → тест, чтобы не вернулась.
"""

def amount_prog(test_body):
    return '''def good(text):
    try:
        value = float(text)
    except ValueError:
        return False
    return value > 0


def bug1(text):
    try:
        value = float(text)
    except ValueError:
        return False
    return value >= 0


def bug2(text):
    try:
        value = float(text)
    except ValueError:
        return False
    return value != 0


def bug3(text):
    return float(text) > 0


VERSIONS = {"good": good, "bug1": bug1, "bug2": bug2, "bug3": bug3}


def tests(is_valid_amount):
''' + test_body + '''

name = input().strip()
try:
    tests(VERSIONS[name])
    print("PASS")
except Exception:
    print("FAIL")
'''

GOOD = "    assert is_valid_amount(\"5\")\n    assert is_valid_amount(\"0.5\")\n    assert not is_valid_amount(\"0\")\n    assert not is_valid_amount(\"-3\")\n    assert not is_valid_amount(\"abc\")\n"

a1 = predict_task("a1-table", "Таблица тестов",
  'def total_with_tax(price, rate):\n    return round(price * (1 + rate), 2)\n\n\ncases = [((100, 0.2), 120.0), ((50, 0.1), 55.0), ((10, 0), 10), ((3, 0.5), 5)]\npassed = 0\nfor args, expected in cases:\n    got = total_with_tax(*args)\n    ok = got == expected\n    passed += ok\n    print(args, got, "ок" if ok else "ОШИБКА")\nprint(passed, "из", len(cases))\n',
  [("(100, 0.2) 120.0 ок\n(50, 0.1) 55.0 ок\n(10, 0) 10 ок\n(3, 0.5) 5 ОШИБКА\n3 из 4", "Результат для (10, 0) — 10 (целое число), а для (3, 0.5) — 4.5; проверьте, какие строки совпали."),
   ("(100, 0.2) 120.0 ок\n(50, 0.1) 55.0 ок\n(10, 0) 10.0 ок\n(3, 0.5) 4.5 ОШИБКА\n3 из 4", "round(10 * 1, 2) возвращает 10, а не 10.0, потому что 10 * (1 + 0) — целое.")],
  hints("Разберите каждый случай отдельно.", "100 · 1.2 = 120.0, 50 · 1.1 = 55.0.", "(10, 0): 10 · (1 + 0) — целое число 10, round оставляет его целым.", "(3, 0.5): 3 · 1.5 = 4.5, а ожидается 5.", "Три совпадения из четырёх."),
  "Строка вывода печатает фактическое значение; для (3, 0.5) оно не совпало с ожидаемым.")

a2 = fn_task("a2-share", "Исправьте долю",
  "Функция `share(part, total)` должна возвращать долю в процентах, округлённую до 1 знака (`share(1, 4)` → `25.0`, `share(1, 3)` → `33.3`), а при `total == 0` возвращать `0.0`. Сейчас она ошибается. Исправьте.",
  "share", "def share(part, total):\n    if total == 0:\n        return 0.0\n    return round(part / total * 100, 1)\n",
  [[1, 4], [1, 3], ([0, 5], True), ([5, 5], True), ([3, 0], True), ([2, 3], True), ([0, 0], True)],
  [("def share(part, total):\n    return round(part // total * 100, 1)\n", "Целочисленное деление теряет дробную часть."),
   ("def share(part, total):\n    return round(part / total * 100, 1)\n", "Деление на ноль не обработано.")],
  hints("Сначала воспроизведите проблему на share(1, 4).", "Результат ноль: часть деления теряется.", "Для долей нужно обычное деление.", "Проверьте случай total равно нулю до деления.", "Округлите итог до одного знака."),
  "Целочисленное деление // отбрасывает дробную часть; защита от нулевого знаменателя — ранний возврат.",
  type="fix", starter="def share(part, total):\n    return round(part // total * 100, 1)\n")

a3 = stdout_task("a3-tests-amount", "Тесты, которые ловят баги",
  "Выше — четыре версии функции `is_valid_amount(text)`: верная `good` и три с ошибками. Напишите в `tests(is_valid_amount)` проверки `assert` так, чтобы программа печатала **`PASS` для `good`** и **`FAIL` для каждой неверной версии**. Версия выбирается входной строкой (`good`, `bug1`, `bug2`, `bug3`).\n\nСумма допустима, если это положительное число.",
  amount_prog(GOOD),
  ["good\n", ("bug1\n", True), ("bug2\n", True), ("bug3\n", True)],
  [(amount_prog("    assert is_valid_amount(\"5\")\n    assert not is_valid_amount(\"-3\")\n    assert not is_valid_amount(\"abc\")\n"), "Нет проверки нуля: bug1 не пойман."),
   (amount_prog("    assert is_valid_amount(\"5\")\n    assert not is_valid_amount(\"0\")\n    assert not is_valid_amount(\"abc\")\n"), "Нет проверки отрицательных: bug2 не пойман."),
   (amount_prog("    assert is_valid_amount(\"5\")\n    assert not is_valid_amount(\"0\")\n    assert not is_valid_amount(\"-3\")\n"), "Нет проверки нечисла: bug3 не пойман."),
   (amount_prog("    assert not is_valid_amount(\"5\")\n"), "Тест неверен: падает на правильной версии.")],
  hints("Сначала запустите со входом good: должно быть PASS.", "У каждой ошибочной версии своя слабость.", "Проверьте обычное положительное число.", "Нужны граничный ноль, отрицательное число и текст, не являющийся числом.", "Пять утверждений: два положительных, ноль, минус и нечисло."),
  "Тест полезен, если способен упасть: bug1 ловит ноль, bug2 — отрицательное число, bug3 — нечисловую строку.",
  starter=amount_prog("    pass\n"), input_text="Название версии: good, bug1, bug2 или bug3.", expected_text="PASS для верной версии и FAIL для каждой неверной.")

a4 = fn_task("a4-parse-amount", "Разбор суммы по-человечески",
  "Напишите `parse_amount(text)`: уберите пробелы по краям, запятую замените точкой (`\"12,5\"` → `12.5`). Верните число, если оно **положительное**; иначе `None` (ноль, минус, не число, пустая строка).",
  "parse_amount", "def parse_amount(text):\n    try:\n        value = float(text.strip().replace(\",\", \".\"))\n    except ValueError:\n        return None\n    return value if value > 0 else None\n",
  [["12,5"], ["abc"], ([" 7 "], True), (["0"], True), (["-1,5"], True), ([""], True), (["3.25"], True), (["1,2,3"], True)],
  [("def parse_amount(text):\n    try:\n        value = float(text.strip())\n    except ValueError:\n        return None\n    return value if value > 0 else None\n", "Запятая как десятичный разделитель не поддерживается."),
   ("def parse_amount(text):\n    try:\n        return float(text.strip().replace(\",\", \".\"))\n    except ValueError:\n        return None\n", "Нулевые и отрицательные суммы принимаются.")],
  hints("Подготовьте строку: обрежьте пробелы и замените запятую.", "Преобразование в число — внутри try.", "При ValueError вернуть None.", "Сумма должна быть строго больше нуля.", "Для «1,2,3» после замены получится не число."),
  "Нормализация ввода (пробелы, запятая) перед разбором делает программу дружелюбнее, а проверка > 0 — безопасной.")

a5 = stdout_task("a5-fix-shares", "Отчёт с долями",
  "Исправьте программу. Ввод — строки `сумма категория`, до пустой строки. Вывод — по строке на категорию: `категория: сумма (доля%)`, где доля — процент от общей суммы с одним знаком после запятой, а порядок — по убыванию суммы, при равенстве по алфавиту. Если данных нет — `Пусто`.",
  "totals = {}\nwhile True:\n    line = input().strip()\n    if not line:\n        break\n    amount, category = line.split()\n    totals[category] = totals.get(category, 0) + float(amount)\nif not totals:\n    print(\"Пусто\")\nelse:\n    all_sum = sum(totals.values())\n    for category, amount in sorted(totals.items(), key=lambda p: (-p[1], p[0])):\n        print(f\"{category}: {round(amount, 2)} ({round(amount / all_sum * 100, 1)}%)\")\n",
  ["10 food\n30 taxi\n10 tea\n\n", ("\n", True), ("5 a\n5 b\n\n", True), ("1 x\n2 x\n1 y\n\n", True)],
  [("totals = {}\nwhile True:\n    line = input().strip()\n    if not line:\n        break\n    amount, category = line.split()\n    totals[category] = totals.get(category, 0) + float(amount)\nall_sum = sum(totals.values())\nfor category, amount in sorted(totals.items(), key=lambda p: (-p[1], p[0])):\n    print(f\"{category}: {round(amount, 2)} ({round(amount / all_sum * 100, 1)}%)\")\n", "Для пустых данных нужно «Пусто» (иначе деление на ноль не случится, но вывод пуст).")],
  hints("Запустите на примере и сравните вывод с условием.", "Сначала посмотрите на порядок категорий.", "Сортировка должна идти по убыванию суммы.", "Доля — обычное деление, умноженное на сто.", "Пустые данные обрабатываются отдельной веткой."),
  "Ошибки в заготовке: сортировка по возрастанию и целочисленное деление; каждая видна на коротком примере.",
  type="fix", starter="totals = {}\nwhile True:\n    line = input().strip()\n    if not line:\n        break\n    amount, category = line.split()\n    totals[category] = totals.get(category, 0) + float(amount)\nif not totals:\n    print(\"Пусто\")\nelse:\n    all_sum = sum(totals.values())\n    for category, amount in sorted(totals.items(), key=lambda p: (p[1], p[0])):\n        print(f\"{category}: {round(amount, 2)} ({round(amount // all_sum * 100, 1)}%)\")\n")

mistakes = [
 {"mistake": "Проверяют только «хороший» ввод", "fix": "Добавляйте ноль, минус, пусто и текст."},
 {"mistake": "Исправляют, не воспроизведя ошибку", "fix": "Сначала самый короткий пример, который падает."},
 {"mistake": "После исправления не добавляют тест", "fix": "Регрессионный тест не даст ошибке вернуться."},
 {"mistake": "Путают // и /", "fix": "// отбрасывает дробную часть."}]

finish("fp-04-quality", "Качество: тесты и отладка", "Проверять функции проекта тестами, искать и закрывать ошибки.",
  {"final.testing": "Тесты проекта", "final.debugging": "Поиск ошибок по шагам", "final.regression": "Регрессионные тесты"},
  ["fp-03-implement"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="final-project")

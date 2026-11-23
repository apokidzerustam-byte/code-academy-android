from lib import *

begin()
scenes = [
 S("intro", "Реализация шаг за шагом", """
  Большой проект нельзя написать за один присест, и не нужно. Работает правило: маленький шаг, запуск, проверка, следующий
  шаг. Сначала самая простая версия, которая уже что-то делает. Потом добавляем команды по одной. После каждой смотрим,
  что всё работает. Так ошибка всегда в последнем изменении, и искать её недолго.""",
  nt("шаг → запуск → проверка → следующий шаг", at="Работает правило")),
 S("loop", "Цикл команд", """
  Основа программы с командной строкой — цикл: прочитать строку, разобрать, выполнить, повторять. Выход — по специальной
  команде или когда ввод закончился. Ввод заканчивается исключением EOFError, и его надо перехватить, иначе программа
  завершится с ошибкой. Напишем цикл, который пока просто повторяет команды.""",
  clr(), t('def main():\n    while True:\n        try:\n            line = input()\n        except EOFError:\n            break\n        if line.strip() == "quit":\n            print("До встречи!")\n            break\n        print("команда:", line)\n\n\n', at="Напишем"),
  t('main()\n', at="Напишем", ), run("Напишем", stdin="add A\nlist\nquit\n")),
 S("dispatch", "Таблица команд", """
  Когда команд становится много, цепочка условий растёт. Лучше сопоставить имя команды с функцией в словаре. Чтобы добавить
  команду, достаточно написать функцию и добавить строку в таблицу. Для неизвестных команд метод get вернёт пустое значение,
  и мы напечатаем сообщение. Каждая функция принимает список аргументов и возвращает строку для вывода.""",
  clr(), t('def cmd_hello(args):\n    return "Привет, " + (" ".join(args) or "мир")\n\n\ndef cmd_sum(args):\n    return str(sum(float(a) for a in args))\n\n\nCOMMANDS = {"hello": cmd_hello, "sum": cmd_sum}\n\n\n', at="Лучше сопоставить"),
  t('for line in ["hello Анна", "sum 1 2 3.5", "dance"]:\n    name, *args = line.split()\n    handler = COMMANDS.get(name)\n    print(handler(args) if handler else f"Неизвестная команда: {name}")\n', at="Для неизвестных"), run("Для неизвестных")),
 S("state", "Состояние программы", """
  Программа помнит данные между командами: список задач и список расходов. Хранить их проще всего в переменных на уровне
  модуля. Это нормально для небольшого проекта, но помните компромисс: чем больше функций читают и меняют общие данные, тем
  труднее разобраться. Поэтому функции получают данные аргументами там, где это возможно.""",
  clr(), t('counter = 0\n\n\ndef bump():\n    global counter\n    counter += 1\n    return counter\n\n\n', at="Хранить"),
  t('def bump_pure(value):\n    return value + 1\n\n\n', at="Поэтому"),
  t('bump()\nbump()\nprint(counter)\nprint(bump_pure(10), bump_pure(10))\n', at="Поэтому"), run("Поэтому")),
 S("check", "Проверка после каждого шага", """
  После каждой добавленной команды запускайте программу на коротком сценарии и сравнивайте вывод с ожидаемым. Хороший
  приём — готовить входной текст заранее. Если что-то не работает, откатите последнюю правку или напечатайте промежуточные
  значения. Не накапливайте непроверенный код: чем больше строк между проверками, тем дороже поиск ошибки.""",
  nt("Короткий сценарий после каждого шага · не копить непроверенное", at="После каждой")),
 S("summary", "Итог", """
  Подведём итог. Растите проект маленькими шагами и проверяйте каждый. Основа программы с командной строкой — цикл чтения,
  выход по quit или по концу ввода. Команды удобно держать в словаре «имя → функция». Состояние программы — списки в
  переменных, но функции лучше делать чистыми. Теперь займёмся качеством: тестами и поиском ошибок.""",
  nt("цикл команд · словарь команд · маленькие шаги", at="Подведём итог")),
]

notes = """
# Реализация по шагам

```python
def cmd_hello(args):
    return "Привет, " + (" ".join(args) or "мир")

COMMANDS = {"hello": cmd_hello}

for line in ["hello Анна", "dance"]:
    name, *args = line.split()
    handler = COMMANDS.get(name)
    print(handler(args) if handler else f"Неизвестная команда: {name}")
```

Цикл: `while True` → `input()` → `except EOFError: break`.
"""

a1 = predict_task("a1-dispatch", "Таблица команд",
  'def up(args):\n    return " ".join(args).upper()\n\n\ndef count(args):\n    return str(len(args))\n\n\nTABLE = {"up": up, "count": count}\nfor line in ["up a b", "count x y z", "count", "boom"]:\n    name, *args = line.split()\n    h = TABLE.get(name)\n    print(h(args) if h else "?")\n',
  [("A B\n3\n0\n?", "Результат функции up — текст в верхнем регистре: «A B»; но проверьте count без аргументов — 0.") ][:0] + [("a b\n3\n0\n?", "Функция up приводит текст к верхнему регистру."), ("A B\n3\n1\n?", "У команды count без аргументов список пуст: длина 0.")],
  hints("Разберите каждую строку по порядку.", "up a b → «A B».", "count x y z → число слов: 3.", "count без аргументов → 0.", "Неизвестная команда → «?»."),
  "Таблица команд сопоставляет имя и функцию; отсутствие в таблице — повод для сообщения.")

a2 = stdout_task("a2-counter", "Мини-REPL: счётчик",
  "Напишите программу, которая читает команды по одной в строке: `inc` — увеличить счётчик на 1, `dec` — уменьшить на 1, `show` — вывести число, `quit` — выход. Начальное значение 0. Если ввод закончился без `quit`, завершайтесь без ошибки. Другие строки игнорируйте.",
  "counter = 0\nwhile True:\n    try:\n        line = input().strip()\n    except EOFError:\n        break\n    if line == \"quit\":\n        break\n    if line == \"inc\":\n        counter += 1\n    elif line == \"dec\":\n        counter -= 1\n    elif line == \"show\":\n        print(counter)\n",
  ["inc\ninc\nshow\nquit\n", ("show\ndec\nshow\n", True), ("inc\nfly\ninc\nshow\nshow\nquit\ninc\nshow\n", True), ("\ninc\n  show  \n", True)],
  [("counter = 0\nwhile True:\n    line = input().strip()\n    if line == \"quit\":\n        break\n    if line == \"inc\":\n        counter += 1\n    elif line == \"dec\":\n        counter -= 1\n    elif line == \"show\":\n        print(counter)\n", "Без quit программа падает с EOFError."),
   ("counter = 0\nwhile True:\n    try:\n        line = input().strip()\n    except EOFError:\n        break\n    if line == \"inc\":\n        counter += 1\n    elif line == \"dec\":\n        counter -= 1\n    elif line == \"show\":\n        print(counter)\n", "Команда quit не останавливает чтение.")],
  hints("Нужен бесконечный цикл с выходом по условию.", "Конец ввода — исключение EOFError.", "Команду quit проверяйте до остальных.", "Счётчик меняется командами inc и dec.", "show печатает текущее значение."),
  "Цикл чтения команд всегда завершается двумя способами: командой выхода и концом ввода.",
  starter="counter = 0\n# читайте команды в цикле\n", type="complete")

a3 = fn_task("a3-parse-expense", "Разбор расхода",
  "Напишите `parse_expense(line)`: из строки `\"12.5 food\"` верните пару `(12.5, \"food\")`. Если сумма не число, не положительна или нет категории — верните `None`. Лишние слова после категории игнорируются.",
  "parse_expense", "def parse_expense(line):\n    parts = line.split()\n    if len(parts) < 2:\n        return None\n    try:\n        amount = float(parts[0])\n    except ValueError:\n        return None\n    if amount <= 0:\n        return None\n    return (amount, parts[1])\n",
  [["12.5 food"], ["abc food"], (["5"], True), (["-3 taxi"], True), (["0 x"], True), (["7 tea hot"], True), ([""], True), (["  2   café  "], True)],
  [("def parse_expense(line):\n    amount, category = line.split()\n    return (float(amount), category)\n", "Падает на неверном вводе."),
   ("def parse_expense(line):\n    parts = line.split()\n    if len(parts) < 2:\n        return None\n    try:\n        amount = float(parts[0])\n    except ValueError:\n        return None\n    return (amount, parts[1])\n", "Неположительные суммы принимаются.")],
  hints("Разделите строку на слова.", "Нужно как минимум два слова.", "Сумму преобразуйте в число внутри try.", "Сумма должна быть больше нуля.", "Результат — пара из числа и категории."),
  "Разбор ввода — отдельная функция, которая возвращает значение или None: вызывающий код решает, что сообщить.")

a4 = fn_task("a4-dispatch", "Диспетчер команд",
  "Напишите `dispatch(line)`: команды `upper <текст>` — вернуть текст в верхнем регистре; `len <текст>` — вернуть длину текста (число, преобразованное в строку); `rev <текст>` — вернуть текст задом наперёд. Для пустой строки верните `\"\"`, для неизвестной команды — `\"Неизвестная команда: <команда>\"`. Текст — всё, что после команды (слова склеиваются одним пробелом).",
  "dispatch", "def dispatch(line):\n    parts = line.split()\n    if not parts:\n        return \"\"\n    command, text = parts[0], \" \".join(parts[1:])\n    actions = {\"upper\": lambda s: s.upper(), \"len\": lambda s: str(len(s)), \"rev\": lambda s: s[::-1]}\n    handler = actions.get(command)\n    return handler(text) if handler else f\"Неизвестная команда: {command}\"\n",
  [["upper hello world"], ["len abc"], (["rev привет"], True), ([""], True), (["jump"], True), (["len   a    b "], True), (["upper"], True)],
  [("def dispatch(line):\n    parts = line.split()\n    command, text = parts[0], \" \".join(parts[1:])\n    if command == \"upper\":\n        return text.upper()\n    if command == \"len\":\n        return str(len(text))\n    if command == \"rev\":\n        return text[::-1]\n    return f\"Неизвестная команда: {command}\"\n", "Пустая строка приводит к ошибке."),
   ("def dispatch(line):\n    parts = line.split()\n    if not parts:\n        return \"\"\n    command, text = parts[0], \" \".join(parts[1:])\n    if command == \"upper\":\n        return text.upper()\n    if command == \"len\":\n        return len(text)\n    if command == \"rev\":\n        return text[::-1]\n    return f\"Неизвестная команда: {command}\"\n", "Длина возвращается числом, а не строкой.")],
  hints("Разберите строку на команду и текст.", "Для пустой строки — сразу пустой ответ.", "Сопоставьте имя команды с действием.", "Длину превратите в строку.", "Для неизвестной команды — сообщение с её названием."),
  "Диспетчер связывает команду с функцией; результат всегда строка — единообразие упрощает проверку.")

a5 = stdout_task("a5-mini-tasks", "Мини-список дел",
  "Программа читает команды: `add <название>` — запомнить задачу; `list` — вывести задачи по одной в строке в виде `1. название`, а если задач нет — `Пусто`; `quit` — выход. Конец ввода — тоже выход.",
  "tasks = []\nwhile True:\n    try:\n        line = input().strip()\n    except EOFError:\n        break\n    if line == \"quit\":\n        break\n    if line.startswith(\"add \"):\n        tasks.append(line[4:].strip())\n    elif line == \"list\":\n        if not tasks:\n            print(\"Пусто\")\n        for i, title in enumerate(tasks, 1):\n            print(f\"{i}. {title}\")\n",
  ["add Молоко\nadd Хлеб\nlist\nquit\n", ("list\n", True), ("add Раз\nlist\nadd Два\nlist\n", True), ("add  Пробелы  \nlist\nquit\n", True)],
  [("tasks = []\nwhile True:\n    try:\n        line = input().strip()\n    except EOFError:\n        break\n    if line == \"quit\":\n        break\n    if line.startswith(\"add \"):\n        tasks.append(line[4:].strip())\n    elif line == \"list\":\n        for i, title in enumerate(tasks, 1):\n            print(f\"{i}. {title}\")\n", "Для пустого списка нужно «Пусто»."),
   ("tasks = []\nwhile True:\n    try:\n        line = input().strip()\n    except EOFError:\n        break\n    if line == \"quit\":\n        break\n    if line.startswith(\"add \"):\n        tasks.append(line[4:].strip())\n    elif line == \"list\":\n        if not tasks:\n            print(\"Пусто\")\n        for i, title in enumerate(tasks):\n            print(f\"{i}. {title}\")\n", "Нумерация должна начинаться с 1.")],
  hints("Задачи накапливаются в списке.", "Команда add: название — всё после «add ».", "Для list нужна нумерация с единицы.", "Пустой список требует отдельного сообщения.", "quit и конец ввода останавливают цикл."),
  "Мини-версия итогового проекта: цикл команд, список задач и вывод с нумерацией через enumerate.",
  starter="tasks = []\n# читайте команды add, list и quit\n", type="complete")

mistakes = [
 {"mistake": "Пишут всё сразу и запускают в конце", "fix": "Запускайте после каждого шага."},
 {"mistake": "Забывают EOFError в цикле чтения", "fix": "Перехватывайте конец ввода."},
 {"mistake": "Длинная цепочка if-elif для команд", "fix": "Словарь «имя → функция»."},
 {"mistake": "Всё хранят в глобальных переменных", "fix": "Передавайте данные аргументами, где можно."}]

finish("fp-03-implement", "Реализация по шагам", "Реализовать программу с командной строкой маленькими проверяемыми шагами.",
  {"final.cli": "Командная строка", "final.dispatch": "Таблица команд", "final.incremental": "Пошаговая разработка"},
  ["fp-02-design"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="final-project")

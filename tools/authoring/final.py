"""Итоговый сквозной проект «Мои задачи и финансы» (этап 15): командная строка с задачами и расходами.
Четыре этапа; эталон каждого этапа проходит свои тесты, заготовка (эталон прошлого этапа) и типовые ошибки — нет."""
from projects import *

HEAD = '''import json

tasks = []
expenses = []
'''

V1 = HEAD + '''

def add_task(title):
    task = {"id": len(tasks) + 1, "title": title, "done": False}
    tasks.append(task)
    return task


def find_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def show_tasks():
    if not tasks:
        print("Задач нет")
        return
    for task in tasks:
        mark = "x" if task["done"] else " "
        print(f"{task['id']}. [{mark}] {task['title']}")


def handle(line):
    parts = line.split()
    if not parts:
        return True
    command = parts[0]
    if command == "quit":
        print("До встречи!")
        return False
    if command == "add":
        task = add_task(" ".join(parts[1:]))
        print(f"Добавлено: #{task['id']} {task['title']}")
    elif command == "list":
        show_tasks()
    elif command == "done":
        task = find_task(int(parts[1]))
        if task is None:
            print(f"Нет задачи #{parts[1]}")
        else:
            task["done"] = True
            print(f"Выполнено: #{task['id']}")
    else:
        print(f"Неизвестная команда: {command}")
    return True


def main():
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not handle(line):
            break


main()
'''

V2 = V1.replace('''def handle(line):''', '''def add_expense(amount, category):
    expenses.append({"amount": amount, "category": category})


def show_report():
    if not expenses:
        print("Расходов нет")
        return
    totals = {}
    for item in expenses:
        totals[item["category"]] = totals.get(item["category"], 0) + item["amount"]
    print("Расходов:", len(expenses))
    print("Всего:", round(sum(item["amount"] for item in expenses), 2))
    print("По категориям:")
    for category, total in sorted(totals.items(), key=lambda pair: (-pair[1], pair[0])):
        print(f"  {category}: {round(total, 2)}")


def handle(line):''').replace('''    else:
        print(f"Неизвестная команда: {command}")''', '''    elif command == "spend":
        amount = float(parts[1])
        add_expense(amount, parts[2])
        print(f"Расход: {amount} {parts[2]}")
    elif command == "report":
        show_report()
    else:
        print(f"Неизвестная команда: {command}")''')

V3 = V2.replace('''def handle(line):''', '''def parse_amount(text):
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value > 0 else None


def handle(line):''').replace('''    if command == "add":
        task = add_task(" ".join(parts[1:]))
        print(f"Добавлено: #{task['id']} {task['title']}")''', '''    if command == "add":
        if len(parts) < 2:
            print("Нужно название")
            return True
        task = add_task(" ".join(parts[1:]))
        print(f"Добавлено: #{task['id']} {task['title']}")''').replace('''        task = find_task(int(parts[1]))
        if task is None:
            print(f"Нет задачи #{parts[1]}")
        else:
            task["done"] = True
            print(f"Выполнено: #{task['id']}")''', '''        if len(parts) < 2 or not parts[1].isdigit():
            print("Нужен номер задачи")
            return True
        task = find_task(int(parts[1]))
        if task is None:
            print(f"Нет задачи #{parts[1]}")
        elif task["done"]:
            print(f"Уже выполнена: #{task['id']}")
        else:
            task["done"] = True
            print(f"Выполнено: #{task['id']}")''').replace('''        amount = float(parts[1])
        add_expense(amount, parts[2])
        print(f"Расход: {amount} {parts[2]}")''', '''        amount = parse_amount(parts[1]) if len(parts) > 1 else None
        if amount is None:
            print("Некорректная сумма")
        elif len(parts) < 3:
            print("Нужна категория")
        else:
            add_expense(amount, parts[2])
            print(f"Расход: {amount} {parts[2]}")''')

V4 = V3.replace('''def handle(line):''', '''HELP = ["add <название> — новая задача", "list — список задач", "done <номер> — выполнить задачу",
        "spend <сумма> <категория> — записать расход", "report — отчёт по расходам",
        "stats — сводка", "export — данные в формате JSON", "quit — выход"]


def show_stats():
    done = sum(1 for task in tasks if task["done"])
    print(f"Задач: {len(tasks)}, выполнено: {done}")
    print("Расходов:", len(expenses))


def handle(line):''').replace('''    else:
        print(f"Неизвестная команда: {command}")''', '''    elif command == "help":
        for text in HELP:
            print(text)
    elif command == "stats":
        show_stats()
    elif command == "export":
        print(json.dumps({"tasks": tasks, "expenses": expenses}, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Неизвестная команда: {command}")''')

def proj_tests(files, inputs):
    return {"kind": "project", "cases": cases_from(files, inputs)}

f1, f2, f3, f4 = ({"main.py": v} for v in (V1, V2, V3, V4))

t1 = proj_tests(f1, [
    ("add-list", "add Купить молоко\nadd Позвонить маме\nlist\nquit\n", False, None),
    ("done", "add Купить молоко\nadd Сдать отчёт\ndone 2\nlist\nquit\n", False, "Выполненная задача отмечается [x] в списке"),
    ("empty", "list\nquit\n", False, "Если задач нет — «Задач нет»"),
    ("missing", "done 5\nquit\n", True, "Несуществующая задача: «Нет задачи #5»"),
    ("unknown", "fly\nquit\n", True, "Неизвестная команда выводится вместе с её названием"),
    ("ids", "add Первая\nadd Вторая\nadd Третья\ndone 1\ndone 3\nlist\nquit\n", True, "Номера задач не меняются после выполнения"),
    ("eof", "add Без выхода\nlist\n", True, "Программа не должна падать, если ввод закончился без quit"),
    ("blank", "\n\nadd Пробелы   между   словами\nlist\nquit\n", True, "Пустые строки пропускаются"),
])
t2 = proj_tests(f2, [
    ("report", "spend 12.5 food\nspend 30 taxi\nspend 7.5 food\nreport\nquit\n", False, None),
    ("none", "report\nquit\n", False, "Без расходов — «Расходов нет»"),
    ("tasks", "add Задача\nlist\nspend 5 tea\nreport\nquit\n", False, "Задачи из этапа 1 продолжают работать"),
    ("order", "spend 10 b\nspend 10 a\nspend 5 c\nreport\nquit\n", True, "Категории — по убыванию суммы, при равенстве — по алфавиту"),
    ("round", "spend 0.1 x\nspend 0.2 x\nreport\nquit\n", True, "Суммы округляются до 2 знаков"),
    ("done", "add A\nadd B\ndone 1\nlist\nquit\n", True, "Этап 1: выполнение задач"),
    ("many", "spend 1 a\nspend 2 b\nspend 3 c\nspend 4 d\nreport\nquit\n", True, None),
])
t3 = proj_tests(f3, [
    ("bad-amount", "spend abc food\nspend -5 food\nspend 0 food\nreport\nquit\n", False, "Сумма должна быть положительным числом"),
    ("no-category", "spend 5\nquit\n", False, "Без категории — «Нужна категория»"),
    ("no-title", "add\nlist\nquit\n", False, "Задача без названия — «Нужно название»"),
    ("done-twice", "add A\ndone 1\ndone 1\nquit\n", False, "Повторное выполнение — «Уже выполнена: #1»"),
    ("done-bad", "done\ndone abc\ndone 0\nquit\n", True, "Нужен номер задачи; номер 0 — «Нет задачи #0»"),
    ("valid", "spend 2.5 tea\nspend 1 tea\nreport\nquit\n", True, "Корректные расходы по-прежнему записываются"),
    ("spend-none", "spend\nquit\n", True, "Команда spend без аргументов не роняет программу"),
])
t4 = proj_tests(f4, [
    ("help", "help\nquit\n", False, None),
    ("stats", "add A\nadd B\nadd C\ndone 2\nspend 1 x\nspend 2 y\nstats\nquit\n", False, "Сводка: задачи и выполненные, число расходов"),
    ("export", "add Купить хлеб\ndone 1\nspend 10.5 food\nexport\nquit\n", False, "JSON с ключами по алфавиту и русскими буквами без \\u-кодов"),
    ("empty-export", "export\nquit\n", True, "Пустые данные — пустые списки"),
    ("all", "add Задача\nspend abc x\nspend 5 x\nreport\nstats\nlist\nquit\n", True, "Все прежние команды работают"),
    ("export-many", "add Первая\nadd Вторая\nspend 3 a\nspend 4 b\nexport\nquit\n", True, None),
])

def wrong(base, old, new, why):
    assert old in base["main.py"], (old, why)
    return ({"main.py": base["main.py"].replace(old, new)}, why)

m1 = milestone("tasks", "Этап 1. Список задач",
  "Итоговый проект собирает всё изученное: вы напишете **программу с командной строкой** в файле `main.py`. Она читает команды по одной в строке (без приглашений, просто `input()`) и работает, пока не встретит `quit` или не закончится ввод.\n\n"
  "Команды этого этапа:\n\n- `add <название>` — новая задача; печатает `Добавлено: #<номер> <название>`. Номера идут с 1.\n- `list` — все задачи по одной в строке: `1. [ ] Купить молоко`; у выполненных вместо пробела `x`. Если задач нет — `Задач нет`.\n- `done <номер>` — отметить выполненной; печатает `Выполнено: #<номер>`, а если такой задачи нет — `Нет задачи #<номер>`.\n- `quit` — печатает `До встречи!` и завершает работу.\n- Любая другая команда: `Неизвестная команда: <команда>`.\n\n"
  "Пустые строки пропускайте. Если ввод закончился без `quit`, программа должна завершиться без ошибки.",
  "Структура программы: данные, небольшие функции, цикл обработки команд.",
  hints("Храните задачи в списке словарей: номер, название, признак «выполнено».",
        "Цикл чтения команд: пока есть ввод, читайте строку и разбирайте её на слова методом split.",
        "Название задачи — все слова после команды, склеенные пробелами.",
        "Для поиска задачи по номеру напишите отдельную функцию, которая возвращает задачу или None.",
        "Ввод может закончиться раньше quit: перехватите EOFError, чтобы программа не падала."),
  t1, f1,
  "Данные лежат в списке словарей, каждая команда обрабатывается в функции handle, а цикл main читает строки и останавливается на quit или конце ввода. Номера задаёт длина списка, поэтому они не меняются.",
  ["Все команды этапа работают.", "Программа не падает на пустом вводе и неизвестных командах."],
  [wrong(f1, '"id": len(tasks) + 1', '"id": len(tasks)', "Номера начинаются с нуля."),
   wrong(f1, 'mark = "x" if task["done"] else " "', 'mark = " "', "Выполненные задачи не отмечаются."),
   wrong(f1, '''        except EOFError:
            break''', '''        except KeyboardInterrupt:
            break''', "Программа падает, если ввод закончился без quit.")],
  after="fp-02-design")
m2 = milestone("finance", "Этап 2. Расходы и отчёт",
  "Добавьте в программу учёт расходов. Новые команды:\n\n- `spend <сумма> <категория>` — записать расход; печатает `Расход: <сумма> <категория>` (сумма — число с плавающей точкой: `12.5`, `30.0`).\n- `report` — отчёт. Если расходов нет: `Расходов нет`. Иначе:\n\n```\nРасходов: 3\nВсего: 50.0\nПо категориям:\n  taxi: 30.0\n  food: 20.0\n```\n\nКатегории — по убыванию суммы, при равенстве — по алфавиту; суммы округляются до 2 знаков.\n\nЗадачи из этапа 1 должны продолжать работать.",
  "Словари для группировки, сортировка по составному ключу, округление.",
  hints("Расходы удобно хранить отдельным списком словарей рядом со списком задач.",
        "Для отчёта соберите словарь «категория → сумма».",
        "Накопление суммы по ключу: totals.get(категория, 0) плюс сумма.",
        "Сортировка по убыванию суммы и по алфавиту при равенстве: ключ-кортеж с минусом перед суммой.",
        "Общую сумму и суммы по категориям округляйте до двух знаков функцией round."),
  t2, f2,
  "Расходы лежат в отдельном списке. Отчёт группирует суммы в словарь и сортирует пары по ключу (−сумма, категория), так порядок получается одинаковым при любых вводах.",
  ["Отчёт верен на разных наборах.", "Команды этапа 1 не сломаны."],
  [wrong(f2, "key=lambda pair: (-pair[1], pair[0])", "key=lambda pair: pair[0]", "Категории отсортированы только по алфавиту."),
   wrong(f2, 'print("Всего:", round(sum(item["amount"] for item in expenses), 2))', 'print("Всего:", sum(item["amount"] for item in expenses))', "Общая сумма не округлена."),
   wrong(f2, '''    if not expenses:
        print("Расходов нет")
        return
''', "", "Пустой отчёт печатает заголовки без данных.")],
  starter=None, after="fp-03-implement")
m3 = milestone("validation", "Этап 3. Проверка ввода",
  "Настоящая программа не должна верить вводу. Добавьте проверки:\n\n- `add` без названия — `Нужно название`.\n- `done` без номера или с нечисловым номером — `Нужен номер задачи`; повторное выполнение — `Уже выполнена: #<номер>`.\n- `spend`: сумма не число или не больше нуля — `Некорректная сумма` (так же, если сумма не указана); нет категории — `Нужна категория`.\n\nНичего при этом не записывайте и не роняйте программу.",
  "Проверка ввода, ранний возврат, функции для разбора значений.",
  hints("Сначала проверьте, что слов в команде достаточно.",
        "Для проверки номера подойдёт метод строки isdigit.",
        "Сумму разберите отдельной функцией: пробуйте float внутри try и возвращайте None при ошибке.",
        "Сумма должна быть строго больше нуля.",
        "Порядок проверок в spend: сначала сумма, затем категория."),
  t3, f3,
  "Каждая команда сначала проверяет аргументы и сообщает о проблеме, не меняя данные. Разбор суммы вынесен в parse_amount: она возвращает число или None.",
  ["Некорректный ввод не меняет данные.", "Все сообщения совпадают с условием."],
  [wrong(f3, "return value if value > 0 else None", "return value", "Отрицательные суммы принимаются."),
   wrong(f3, '''        elif task["done"]:
            print(f"Уже выполнена: #{task['id']}")
''', "", "Повторное выполнение не обрабатывается."),
   wrong(f3, '''        if len(parts) < 2:
            print("Нужно название")
            return True
''', "", "Пустое название принимается.")],
  after="fp-04-quality")
m4 = milestone("final", "Этап 4. Справка, сводка и экспорт",
  "Завершите проект. Новые команды:\n\n- `help` — список команд, по строке на команду (тексты задайте в списке `HELP`, как в условии ниже).\n- `stats` — две строки: `Задач: <всего>, выполнено: <сколько>` и `Расходов: <число>`.\n- `export` — одну строку JSON: `{\"expenses\": …, \"tasks\": …}` — ключи по алфавиту, русские буквы как есть (без `\\u`-кодов).\n\n"
  "Строки справки по порядку:\n\n```\nadd <название> — новая задача\nlist — список задач\ndone <номер> — выполнить задачу\nspend <сумма> <категория> — записать расход\nreport — отчёт по расходам\nstats — сводка\nexport — данные в формате JSON\nquit — выход\n```\n\n"
  "Все прежние команды должны работать как раньше.",
  "Модуль json, параметры dumps, сводные значения, итоговая проверка проекта.",
  hints("Справку удобно хранить в списке строк и печатать циклом.",
        "Для сводки посчитайте выполненные задачи генераторным выражением с sum.",
        "Для экспорта соберите словарь из двух списков и превратите его в строку модулем json.",
        "Параметр sort_keys упорядочит ключи по алфавиту.",
        "Параметр ensure_ascii со значением False сохранит русские буквы как есть."),
  t4, f4,
  "HELP хранит тексты справки, stats считает задачи и расходы, а export превращает данные в JSON: sort_keys даёт стабильный порядок, ensure_ascii=False — читаемые русские буквы.",
  ["Справка, сводка и экспорт совпадают с условием.", "Старые команды не сломались."],
  [wrong(f4, "ensure_ascii=False, sort_keys=True", "sort_keys=True", "Русские буквы превращаются в коды \\uXXXX."),
   wrong(f4, "ensure_ascii=False, sort_keys=True", "ensure_ascii=False", "Ключи не упорядочены по алфавиту."),
   wrong(f4, 'done = sum(1 for task in tasks if task["done"])', "done = len(tasks)", "Сводка считает все задачи выполненными.")],
  after="fp-05-demo")

final = {"id": "finance-final", "kind": "through", "title": "Мои задачи и финансы — итог",
         "summary": "Итоговый проект курса: программа с командной строкой для задач и личных расходов. "
                    "Четыре этапа: список задач, расходы и отчёт, проверка ввода, справка и экспорт.",
         "language": "python", "afterLesson": "fp-02-design",
         "skills": ["final.design", "final.cli", "final.testing", "final.debugging"],
         "milestones": [m1, m2, m3, m4]}

write_project("final-project", final)

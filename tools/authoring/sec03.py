from lib import *

DB = 'import sqlite3\n\nconn = sqlite3.connect(":memory:")\nconn.execute("CREATE TABLE users (name TEXT, role TEXT)")\nconn.executemany("INSERT INTO users VALUES (?, ?)", [("anna", "admin"), ("boris", "user"), ("clara", "user")])\n\n'

begin()
scenes = [
 S("intro", "Когда данные становятся кодом", """
  Инъекция возникает, когда данные пользователя попадают в команду и интерпретируются как её часть. Самый известный пример —
  SQL-инъекция. Программист склеивает текст запроса из строки и введённого значения, а пользователь вводит не имя, а
  кусочек SQL. Эта уязвимость много лет входит в списки самых опасных. Сегодня мы разберём её на игрушечной базе в памяти:
  с вымышленными данными и без доступа к чему-либо реальному. Цель — научиться писать запросы, которые не ломаются
  от чужого ввода.""",
  nt("Данные пользователя **не должны** становиться частью текста команды", at="Программист склеивает")),
 S("setup", "Учебная база", """
  Создадим базу данных SQLite прямо в памяти. В ней таблица пользователей с именем и ролью, три вымышленные записи. База
  исчезнет при завершении программы, поэтому ничего вреда мы не нанесём. Для начала выполним обычный запрос и убедимся, что
  всё работает.""",
  clr(), t(DB, at="Создадим"),
  t('print(conn.execute("SELECT role FROM users WHERE name = \'anna\'").fetchall())\n', at="Для начала"), run("Для начала")),
 S("bad", "Опасная склейка строк", """
  Теперь напишем функцию поиска так, как писать нельзя: подставим имя в запрос через f-строку. Для обычного имени всё
  работает. Но если вместо имени передать значение с кавычкой и условием, которое всегда истинно, то запрос изменит смысл:
  условие в WHERE перестанет что-либо фильтровать, и вернутся все записи. Посмотрим, во что превратился текст запроса.""",
  clr(), t(DB, at="Теперь"),
  t('def find_bad(name):\n    sql = f"SELECT name, role FROM users WHERE name = \'{name}\'"\n    print(sql)\n    return conn.execute(sql).fetchall()\n\n\n', at="Теперь"),
  t('print(find_bad("boris"))\nprint(find_bad("x\' OR \'1\'=\'1"))\n', at="Но если"), run("Посмотрим")),
 S("good", "Параметризованный запрос", """
  Правильное решение — параметризованные запросы. В тексте запроса на месте значения ставится знак вопроса, а сами значения
  передаются отдельно. Драйвер базы данных гарантирует, что значение останется значением, и ничто в нём не будет
  выполнено как команда. Та же самая подозрительная строка теперь просто ищется как имя, которого нет, и ничего не находится.""",
  clr(), t(DB, at="Правильное"),
  t('def find_good(name):\n    return conn.execute("SELECT name, role FROM users WHERE name = ?", (name,)).fetchall()\n\n\n', at="Правильное"),
  t('print(find_good("boris"))\nprint(find_good("x\' OR \'1\'=\'1"))\n', at="Та же"), run("Та же")),
 S("names", "Имена столбцов не параметризуются", """
  Знак вопроса заменяет только значения. Название столбца или таблицы параметром передать нельзя. Если порядок сортировки
  выбирает пользователь, нельзя подставлять его слово в запрос напрямую. Правильный подход — белый список: разрешённые
  названия перечислены в программе, а всё остальное отвергается. Так сортировка работает по допустимым столбцам, а странный
  ввод вызывает ошибку.""",
  clr(), t(DB, at="Правильный"),
  t('ALLOWED = {"name", "role"}\n\n\ndef names_sorted(column):\n    if column not in ALLOWED:\n        raise ValueError("недопустимый столбец")\n    rows = conn.execute(f"SELECT name FROM users ORDER BY {column}").fetchall()\n    return [r[0] for r in rows]\n\n\n', at="Правильный"),
  t('print(names_sorted("name"))\ntry:\n    names_sorted("name; DROP TABLE users")\nexcept ValueError as e:\n    print("отказ:", e)\n', at="Так"), run("Так")),
 S("summary", "Итог", """
  Подведём итог. Никогда не склеивайте SQL из пользовательских данных. Передавайте значения через параметры: знак вопроса и
  кортеж значений. Для имён столбцов и таблиц используйте белый список. Давайте программе доступ к базе с минимально
  необходимыми правами, чтобы даже при ошибке ущерб был ограничен. Те же правила действуют и для других видов
  инъекций: команд оболочки, запросов к другим базам.""",
  nt("`execute(\"... WHERE name = ?\", (name,))` · имена столбцов — по белому списку", at="Передавайте")),
]

notes = """
# SQL-инъекции

```python
import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (name TEXT, role TEXT)")
conn.execute("INSERT INTO users VALUES ('anna', 'admin')")

# безопасно: значение передаётся отдельно
rows = conn.execute("SELECT role FROM users WHERE name = ?", ("anna",)).fetchall()
print(rows)
```

## Правила

1. Не склеивайте SQL из строк пользователя.
2. Значения — через `?` и кортеж параметров.
3. Имена столбцов и таблиц — только из белого списка.
4. Права доступа к базе — минимально необходимые.

Все примеры курса работают только с базой в памяти и вымышленными данными.
"""

a1 = predict_task("a1-sql-text", "Во что превратился запрос",
  'def build(name):\n    return f"SELECT role FROM users WHERE name = \'{name}\'"\n\nprint(build("anna"))\nprint(build("x\' OR \'1\'=\'1"))\n',
  [("SELECT role FROM users WHERE name = 'anna'\nSELECT role FROM users WHERE name = 'x\\' OR \\'1\\'=\\'1'", "Кавычки не экранируются: строка вставляется как есть."), ("SELECT role FROM users WHERE name = anna\nSELECT role FROM users WHERE name = x' OR '1'='1", "Одинарные кавычки вокруг подставляемого значения остаются в шаблоне.")],
  hints("f-строка подставляет значение внутрь шаблона без изменений.", "Вокруг значения в шаблоне уже стоят одинарные кавычки.", "Для «anna» получится обычный запрос.", "Для второй строки внутри остаются свои кавычки.", "Условие превращается в name = 'x' OR '1'='1'."),
  "Подстановка не отличает данные от кода: кавычка во вводе закрывает строку, и остаток становится частью SQL.")

a2 = fn_task("a2-find-role", "Исправьте поиск роли",
  "Функция ищет роль пользователя, склеивая запрос. Перепишите её через **параметр** (`?`), чтобы вводы вроде `x' OR '1'='1` ничего не находили, а имена с апострофом работали.",
  "find_role", DB + "\n\ndef find_role(name):\n    row = conn.execute(\"SELECT role FROM users WHERE name = ?\", (name,)).fetchone()\n    return row[0] if row else None\n",
  [["boris"], ["x' OR '1'='1"], (["nobody"], True), (["anna"], True), (["o'neil"], True), (["clara' --"], True)],
  [(DB + "\n\ndef find_role(name):\n    row = conn.execute(f\"SELECT role FROM users WHERE name = '{name}'\").fetchone()\n    return row[0] if row else None\n", "Склейка строк: инъекция возвращает первую запись.")],
  hints("Проблема — f-строка внутри запроса.", "В запросе на месте значения должен стоять знак вопроса.", "Значение передаётся вторым аргументом execute.", "Второй аргумент — кортеж, даже из одного элемента.", "Запятая после имени делает кортеж: (name,)."),
  "Параметр передаётся отдельно от текста запроса, поэтому кавычки и ключевые слова во вводе остаются обычными символами.",
  type="fix", starter=DB + "\n\ndef find_role(name):\n    row = conn.execute(f\"SELECT role FROM users WHERE name = '{name}'\").fetchone()\n    return row[0] if row else None\n")

a3 = fn_task("a3-count", "Сколько пользователей с ролью",
  "Напишите `count_users(role)`: верните число пользователей с указанной ролью. Запрос должен быть параметризованным. База `users` уже создана.",
  "count_users", DB + "\n\ndef count_users(role):\n    return conn.execute(\"SELECT COUNT(*) FROM users WHERE role = ?\", (role,)).fetchone()[0]\n",
  [["user"], ["admin"], (["guest"], True), (["user' OR '1'='1"], True), (["admin' --"], True)],
  [(DB + "\n\ndef count_users(role):\n    return conn.execute(f\"SELECT COUNT(*) FROM users WHERE role = '{role}'\").fetchone()[0]\n", "Склейка: инъекция считает всех пользователей.")],
  hints("Используйте SELECT COUNT(*) с условием по роли.", "Значение роли передайте параметром.", "Выполните запрос через conn.execute.", "fetchone() вернёт кортеж с одним числом.", "Число — первый элемент кортежа."),
  "COUNT(*) возвращает одну строку с одним столбцом. Параметр защищает от подмены условия.")

a4 = fn_task("a4-sorted", "Сортировка по выбору пользователя",
  "Напишите `names_sorted(column)`: верните список имён из `users`, отсортированных по столбцу `column`. Допустимы только `name` и `role` (при сортировке по `role` порядок внутри роли — по имени); для любого другого значения — `ValueError`.",
  "names_sorted", DB + "\n\nALLOWED = {\"name\", \"role\"}\n\n\ndef names_sorted(column):\n    if column not in ALLOWED:\n        raise ValueError(\"недопустимый столбец\")\n    rows = conn.execute(f\"SELECT name FROM users ORDER BY {column}, name\").fetchall()\n    return [r[0] for r in rows]\n",
  [["name"], ["role"], {"args": ["password"], "expected_error": "ValueError", "hidden": True}, {"args": ["name; DROP TABLE users"], "expected_error": "ValueError", "hidden": True}, {"args": [""], "expected_error": "ValueError", "hidden": True}],
  [(DB + "\n\ndef names_sorted(column):\n    rows = conn.execute(f\"SELECT name FROM users ORDER BY {column}, name\").fetchall()\n    return [r[0] for r in rows]\n", "Нет проверки: недопустимый столбец доходит до базы.")],
  hints("Имя столбца параметром не передать — нужна проверка.", "Перечислите допустимые названия в множестве.", "Если столбца нет в множестве — raise ValueError.", "Проверенное имя можно подставить в запрос.", "Для порядка внутри роли добавьте второй ключ сортировки."),
  "Белый список — единственный надёжный способ принимать имена столбцов: подставляется только то, что программист разрешил заранее.")

a5 = predict_task("a5-count-demo", "Склейка против параметра",
  DB + '\n\ndef bad(role):\n    return len(conn.execute(f"SELECT name FROM users WHERE role = \'{role}\'").fetchall())\n\n\ndef good(role):\n    return len(conn.execute("SELECT name FROM users WHERE role = ?", (role,)).fetchall())\n\n\nprint(bad("user"), good("user"))\nprint(bad("x\' OR \'1\'=\'1"), good("x\' OR \'1\'=\'1"))\n',
  [("2 2\n0 0", "При склейке условие «1=1» истинно для всех трёх строк."), ("2 2\n3 3", "Параметризованный запрос ищет роль буквально и ничего не находит.")],
  hints("В таблице три пользователя: роль admin у одного, user у двоих.", "Для «user» обе функции вернут 2.", "Склеенный запрос с подозрительным значением содержит условие, истинное всегда.", "Он вернёт все 3 записи.", "Параметризованный запрос ищет роль с таким названием буквально: 0."),
  "Склеенный запрос меняет смысл условия; параметризованный всегда ищет значение буквально.")

mistakes = [
 {"mistake": "Собирают запрос через f-строку или +", "fix": "Используйте знаки ? и передавайте значения вторым аргументом execute."},
 {"mistake": "Думают, что достаточно экранировать кавычки", "fix": "Параметры надёжнее ручного экранирования."},
 {"mistake": "Подставляют имя столбца из ввода", "fix": "Белый список разрешённых имён."},
 {"mistake": "Забывают запятую в кортеже из одного элемента", "fix": "(name,) — кортеж; (name) — просто значение."}]

finish("sec-03-sql-injection", "SQL-инъекции", "Понимать, как возникает SQL-инъекция, и писать безопасные параметризованные запросы.",
  {"sec.injection": "SQL-инъекции", "sec.params": "Параметризованные запросы", "sec.whitelist": "Белый список имён"},
  ["sec-02-passwords"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="security-lab")

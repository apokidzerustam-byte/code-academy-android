"""Урок SQL 5: проектирование таблиц — ключи, связи, нормализация."""
from sqlib import *

TASKS = """CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL
);
"""
DEMO = TASKS + """
CREATE TABLE notes (
  id INTEGER PRIMARY KEY,
  task_id INTEGER NOT NULL REFERENCES tasks(id),
  text TEXT NOT NULL
);

INSERT INTO tasks (title) VALUES ('Купить молоко'), ('Написать отчёт');
INSERT INTO notes (task_id, text) VALUES (1, 'Два литра'), (2, 'К пятнице'), (2, 'Согласовать с Ольгой');
"""
BAD = "INSERT INTO notes (task_id, text)\nVALUES (99, 'Заметка к несуществующей задаче');\n"
err_text = sq_err(BAD, DEMO)
assert "FOREIGN KEY" in err_text, err_text
FLAT = """CREATE TABLE flat (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  category TEXT NOT NULL
);

INSERT INTO flat (title, category) VALUES
  ('Купить молоко', 'дом'), ('Написать отчёт', 'работа'),
  ('Позвонить врачу', 'дом'), ('Сдать отчёт', 'работа'), ('Купить хлеб', 'дом');
"""
CATS = """CREATE TABLE categories (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

INSERT INTO categories (name)
SELECT DISTINCT category
FROM flat
ORDER BY category;

SELECT * FROM categories;
"""
INFO = "SELECT name, type, \"notnull\", pk\nFROM pragma_table_info('notes');\n"
JOIN = "SELECT t.title, n.text\nFROM notes n\nJOIN tasks t ON t.id = n.task_id\nORDER BY n.id;\n"

use_file("schema.sql")
scenes = [
    scene("intro", "Как спроектировать таблицы", """
      До сих пор таблицы нам давали готовыми. Теперь научимся придумывать их самим. Главное правило проектирования: каждый
      факт хранится в одном месте. Если название категории выписано в каждой задаче, при переименовании придётся править
      сотни строк, и где-нибудь обязательно забудут. Лучше завести отдельную таблицу и ссылаться на неё по номеру.""",
          [NOTE("**Один факт — одно место.** Повторяющееся выносим в отдельную таблицу и ссылаемся на номер строки.", at="Главное правило")]),
    scene("keys", "Первичный ключ и ограничения", """
      Каждой таблице нужен первичный ключ, номер, по которому строку можно однозначно найти. Объявляем столбец id как
      INTEGER PRIMARY KEY, и база выдаёт номера сама. Дальше уточняем остальные столбцы. NOT NULL запрещает пустое значение.
      UNIQUE не даёт повторять значения: например, две категории с одним названием. Тип столбца тоже важен: INTEGER для целых
      чисел, REAL для дробных и TEXT для строк.""",
          [T(TASKS, at="Каждой таблице"), HL([2], at="Объявляем", file="schema.sql")]),
    scene("fk", "Внешний ключ", """
      Теперь свяжем заметки с задачами. В таблице notes добавляем столбец task_id и пишем слово REFERENCES: оно говорит, что
      значение должно совпадать с номером существующей строки в таблице tasks. Это и есть внешний ключ. В таблице две
      задачи и три заметки: у второй задачи две заметки. Такая связь называется «один ко многим».""",
          [CLEAR(file="schema.sql"), T(DEMO, at="Теперь свяжем"), HL([8], at="REFERENCES", file="schema.sql")]),
    scene("join", "Читаем связанные данные", """
      Чтобы увидеть заметки вместе с названиями задач, соединяем таблицы через JOIN, как в прошлом уроке. Запускаем:
      каждая заметка подписана названием своей задачи. Название хранится только в таблице задач, а в заметках лишь номер.""",
          [CLEAR(file="main.sql"), T(JOIN, at="Чтобы увидеть", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(sq_out(JOIN, DEMO), at="каждая заметка")]),
    scene("violation", "База охраняет связи", """
      Попробуем добавить заметку к задаче номер девяносто девять, которой нет. Внешний ключ не позволит: база откажет и
      объяснит причину. Так в таблицах не появляются «осиротевшие» строки, ссылающиеся в пустоту.""",
          [CLEAR(file="main.sql"), T(BAD, at="Попробуем", file="main.sql"), RUN(at="база откажет", file="main.sql"),
           OUT(err_text.strip(), err=True, at="база откажет")]),
    scene("normalize", "Выносим повторы в справочник", """
      А что делать, если данные уже лежат в одной плоской таблице, где категория повторяется в каждой строке? Создаём
      таблицу categories с уникальным названием. Затем заполняем её командой INSERT с вложенным SELECT: берём
      различающиеся значения словом DISTINCT и сортируем по алфавиту. Запускаем: две категории вместо пяти повторов.
      Дальше задачи будут ссылаться на номера категорий.""",
          [T(FLAT, at="А что делать"), CLEAR(file="main.sql"), T(CATS, at="Создаём", file="main.sql"), HL([6, 7, 8, 9], at="Затем заполняем", file="main.sql"),
           RUN(at="Запускаем", file="main.sql"), OUT(sq_out(CATS, FLAT.split("INSERT INTO flat")[0] + "INSERT INTO flat" + FLAT.split("INSERT INTO flat")[1]), at="две категории")]),
    scene("inspect", "Заглянуть в схему", """
      Как узнать, из чего состоит таблица? Функция pragma table info возвращает по строке на каждый столбец: имя, тип,
      запрет пустых значений и признак первичного ключа. Запустим её для таблицы notes: видно, что task_id обязателен,
      а id — первичный ключ.""",
          [CLEAR(file="main.sql"), T(INFO, at="Как узнать", file="main.sql"), RUN(at="Запустим", file="main.sql"),
           OUT(sq_out(INFO, DEMO), at="видно")]),
    scene("summary", "Итог", """
      Подведём итог. Каждый факт хранится в одном месте. У таблицы есть первичный ключ. NOT NULL, UNIQUE и CHECK охраняют
      значения, а внешний ключ REFERENCES связывает таблицы и не даёт ссылаться на несуществующие строки. Повторы выносим в
      справочник командой INSERT с SELECT. Эти правила пригодятся и в итоговом проекте.""",
          [NOTE("`id INTEGER PRIMARY KEY` · `NOT NULL` · `UNIQUE` · `task_id INTEGER REFERENCES tasks(id)`", at="Подведём итог")]),
]
use_file(None)

notes = """
# SQL: проектирование таблиц

```sql
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,                    -- первичный ключ
  title TEXT NOT NULL                        -- обязательное
);

CREATE TABLE notes (
  id INTEGER PRIMARY KEY,
  task_id INTEGER NOT NULL REFERENCES tasks(id),   -- внешний ключ
  text TEXT NOT NULL
);

INSERT INTO categories (name)                -- заполнить справочник из плоской таблицы
SELECT DISTINCT category FROM flat ORDER BY category;

SELECT name, type, "notnull", pk FROM pragma_table_info('notes');   -- схема таблицы
```

- **Один факт — одно место**: повторяющееся выносим в отдельную таблицу.
- Связь «один ко многим»: у одной задачи много заметок, у заметки одна задача (`task_id`).
- `UNIQUE` не позволяет повторов; `NOT NULL` — пустых значений.
- Внешний ключ не даёт сослаться на несуществующую строку: «FOREIGN KEY constraint failed».
- Типы: `INTEGER`, `REAL`, `TEXT`.
"""

CHECK_INFO = "SELECT name, type, \"notnull\", pk FROM pragma_table_info('categories') ORDER BY name;"
CHECK_UQ = "SELECT COUNT(*) FROM pragma_index_list('categories') WHERE \"unique\" = 1;"
a1 = sql_task("a1-create", "write", "Таблица категорий",
    "Создайте таблицу `categories` с двумя столбцами: `id` — целое число, первичный ключ; `name` — текст, **обязательный** и **уникальный**.",
    "Создавать таблицу с ключами и ограничениями.", "CREATE TABLE categories (\n  id INTEGER PRIMARY KEY,\n  name TEXT NOT NULL UNIQUE\n);",
    [(TASKS, False, None, CHECK_INFO), (TASKS, True, "Проверяется и уникальность названия", CHECK_UQ), (TASKS + "INSERT INTO tasks (title) VALUES ('Любая');", True, None, CHECK_INFO)],
    [("CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT NOT NULL);", "Нет UNIQUE: названия могут повторяться."),
     ("CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT UNIQUE);", "Нет NOT NULL: название можно не указывать."),
     ("CREATE TABLE categories (id INTEGER, name TEXT NOT NULL UNIQUE);", "Нет PRIMARY KEY у id."),
     ("CREATE TABLE categories (id INTEGER PRIMARY KEY, name INTEGER NOT NULL UNIQUE);", "Неверный тип у name: нужен TEXT.")],
    hints("Таблицу создаёт CREATE TABLE.", "В скобках перечисляют столбцы через запятую: имя и тип.", "Первичный ключ записывают после типа: INTEGER PRIMARY KEY.", "У name два ограничения: NOT NULL и UNIQUE.", "Запятая нужна между столбцами, но не после последнего."),
    "PRIMARY KEY делает номер уникальным идентификатором строки, NOT NULL запрещает пустое значение, UNIQUE — повторы.",
    starter="-- Создайте таблицу\n")

FK_INFO = "SELECT \"table\", \"from\", \"to\" FROM pragma_foreign_key_list('notes');"
FK_COLS = "SELECT name, type, \"notnull\" FROM pragma_table_info('notes') ORDER BY name;"
a2 = sql_task("a2-fk", "complete", "Связь заметок с задачами",
    "Таблица `notes` создана без связи: `task_id` просто число. Допишите так, чтобы `task_id` был **внешним ключом** на `tasks(id)` и был обязательным.",
    "Объявлять внешний ключ.", "CREATE TABLE notes (\n  id INTEGER PRIMARY KEY,\n  task_id INTEGER NOT NULL REFERENCES tasks(id),\n  text TEXT NOT NULL\n);",
    [(TASKS, False, None, FK_INFO), (TASKS, True, "Проверяется и обязательность столбца", FK_COLS), (TASKS + "INSERT INTO tasks (title) VALUES ('Любая');", True, None, FK_INFO)],
    [("CREATE TABLE notes (id INTEGER PRIMARY KEY, task_id INTEGER NOT NULL, text TEXT NOT NULL);", "Нет внешнего ключа."),
     ("CREATE TABLE notes (id INTEGER PRIMARY KEY, task_id INTEGER REFERENCES tasks(id), text TEXT NOT NULL);", "task_id не обязателен: нет NOT NULL."),
     ("CREATE TABLE notes (id INTEGER PRIMARY KEY, task_id INTEGER NOT NULL REFERENCES tasks(title), text TEXT NOT NULL);", "Ссылка не на первичный ключ: нужен tasks(id).")],
    hints("Сравните описание столбца task_id с условием.", "Связь с другой таблицей задаёт слово REFERENCES.", "После REFERENCES пишут таблицу и в скобках её столбец.", "Ссылаться нужно на первичный ключ таблицы tasks.", "Обязательность — слова NOT NULL перед REFERENCES."),
    "REFERENCES tasks(id) связывает столбец с первичным ключом другой таблицы; NOT NULL запрещает заметки без задачи.",
    starter="CREATE TABLE notes (\n  id INTEGER PRIMARY KEY,\n  task_id INTEGER,\n  text TEXT NOT NULL\n);\n")

TAGS_INFO = "SELECT name, type, \"notnull\", pk FROM pragma_table_info('tags') ORDER BY name;"
TAGS_FK = "SELECT \"table\", \"from\", \"to\" FROM pragma_foreign_key_list('tags');"
a3 = sql_task("a3-design", "write", "Теги задач",
    "У каждой задачи может быть много тегов. Создайте таблицу `tags`: `id` (целое, первичный ключ), `task_id` (целое, обязательное, внешний ключ на `tasks(id)`) и `name` (текст, обязательный).",
    "Спроектировать таблицу для связи «один ко многим».", "CREATE TABLE tags (\n  id INTEGER PRIMARY KEY,\n  task_id INTEGER NOT NULL REFERENCES tasks(id),\n  name TEXT NOT NULL\n);",
    [(TASKS, False, None, TAGS_INFO), (TASKS, True, "Проверяется связь с таблицей задач", TAGS_FK), (TASKS + "INSERT INTO tasks (title) VALUES ('Другая');", True, None, TAGS_INFO)],
    [("CREATE TABLE tags (id INTEGER PRIMARY KEY, task_id INTEGER NOT NULL, name TEXT NOT NULL);", "Нет внешнего ключа."),
     ("CREATE TABLE tags (id INTEGER PRIMARY KEY, task_id INTEGER NOT NULL REFERENCES tasks(id), name TEXT);", "Название тега не обязательно: нет NOT NULL."),
     ("CREATE TABLE tags (id INTEGER, task_id INTEGER NOT NULL REFERENCES tasks(id), name TEXT NOT NULL);", "Нет первичного ключа.")],
    hints("Связь «один ко многим»: у тега одна задача, а у задачи много тегов.", "Ссылка на задачу хранится в таблице тегов: столбец task_id.", "Первичный ключ — id INTEGER PRIMARY KEY.", "Для task_id: тип, NOT NULL и REFERENCES tasks(id).", "Запятая нужна между столбцами, но не после последнего."),
    "Ссылка всегда лежит на стороне «многих»: таблица tags хранит task_id и ссылается на tasks.",
    starter="-- Создайте таблицу tags\n")

FLAT_SETUP = FLAT.split("INSERT INTO flat")[0] + "CREATE TABLE categories (\n  id INTEGER PRIMARY KEY,\n  name TEXT NOT NULL UNIQUE\n);\n\nINSERT INTO flat (title, category) VALUES\n  ('Б', 'учёба'), ('А', 'дом'), ('В', 'учёба'), ('Г', 'работа'), ('Д', 'дом'), ('Е', 'учёба');\n"
FLAT_B = FLAT.split("INSERT INTO flat")[0] + "CREATE TABLE categories (\n  id INTEGER PRIMARY KEY,\n  name TEXT NOT NULL UNIQUE\n);\n\nINSERT INTO flat (title, category) VALUES ('X', 'яблоки'), ('Y', 'груши'), ('Z', 'яблоки');\n"
FLAT_C = FLAT.split("INSERT INTO flat")[0] + "CREATE TABLE categories (\n  id INTEGER PRIMARY KEY,\n  name TEXT NOT NULL UNIQUE\n);\n\nINSERT INTO flat (title, category) VALUES ('Одна', 'одна');\n"
CHK = "SELECT id, name FROM categories ORDER BY id;"
a4 = sql_task("a4-normalize", "write", "Справочник из плоской таблицы",
    "В таблице `flat` категория записана в каждой строке. Таблица `categories` уже создана и пуста. Заполните её **различающимися** значениями столбца `category` из `flat` по алфавиту (номера выдаст база).",
    "Переносить уникальные значения: INSERT … SELECT DISTINCT.", "INSERT INTO categories (name)\nSELECT DISTINCT category\nFROM flat\nORDER BY category;",
    [(FLAT_SETUP, False, None, CHK), (FLAT_B, True, "Повторы нужно схлопнуть, порядок — по алфавиту", CHK), (FLAT_C, True, None, CHK)],
    [("INSERT INTO categories (name) SELECT category FROM flat ORDER BY category;", "Нет DISTINCT: ошибка уникальности из-за повторов."),
     ("INSERT INTO categories (name) SELECT DISTINCT category FROM flat;", "Нет сортировки: номера выдаются не по алфавиту."),
     ("INSERT INTO categories (name) SELECT DISTINCT title FROM flat ORDER BY title;", "Переносятся названия задач вместо категорий.")],
    hints("Данные нужно скопировать из одной таблицы в другую.", "После INSERT INTO таблица (столбец) вместо VALUES можно написать SELECT.", "Повторы убирает слово DISTINCT сразу после SELECT.", "Берите столбец category из таблицы flat.", "Порядок номеров задаёт ORDER BY category в конце."),
    "INSERT … SELECT копирует результат запроса в таблицу; DISTINCT убирает повторы, ORDER BY определяет порядок добавления и номера.",
    query=CHK, starter="-- Заполните таблицу categories\n")

CODE5 = (DEMO.split("INSERT INTO tasks")[0] + "INSERT INTO tasks (title) VALUES ('А'), ('Б'), ('В');\n"
         "INSERT INTO notes (task_id, text) VALUES (1, 'x'), (1, 'y'), (3, 'z'), (3, 'w'), (3, 'v');\n"
         "SELECT t.title, COUNT(n.id) AS n\nFROM tasks t\nLEFT JOIN notes n ON n.task_id = t.id\nGROUP BY t.id\nHAVING COUNT(n.id) <> 2\nORDER BY n DESC, t.title;\n")
a5 = sql_predict("a5-predict", "Заметки по задачам", CODE5,
    [("А | 2\nБ | 0\nВ | 3", "Задача А осталась: условие HAVING исключает группы ровно с двумя заметками."), ("Б | 0\nВ | 3", "Порядок неверный: сначала должны идти задачи с большим числом заметок.")],
    hints("Сначала LEFT JOIN сохраняет все задачи, даже без заметок.", "Заметок: у А две, у Б ни одной, у В три.", "HAVING убирает группы, где заметок ровно две.", "Остаётся две задачи.", "Сортировка по числу заметок по убыванию."),
    "LEFT JOIN сохраняет задачу без заметок (счёт 0), HAVING отбрасывает группы с двумя, ORDER BY n DESC ставит большие числа первыми.")

skills = {"sql.design": "Проектирование таблиц", "sql.keys": "Первичные и внешние ключи", "sql.normalize": "Нормализация данных"}
write_lesson("sql-05-design", "SQL: проектирование таблиц",
             "Проектировать таблицы: первичные и внешние ключи, ограничения, связь «один ко многим» и вынос повторов в справочник.",
             list(skills), ["sql-04-modify"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Одно и то же значение повторяется в сотне строк", "fix": "Выносите его в справочник и ссылайтесь на номер."},
              {"mistake": "Ссылка на несуществующую строку", "fix": "Внешний ключ запретит: сначала создайте строку, на которую ссылаетесь.", "errorType": "SQLError"},
              {"mistake": "Ссылка не на первичный ключ", "fix": "REFERENCES указывает на столбец id другой таблицы."},
              {"mistake": "Забыли UNIQUE у справочника", "fix": "Без него в справочнике появятся повторы."}],
             min_pass=3, pack="sql-basics", runner="sql")
merge_pack("sql-05-design", skills)

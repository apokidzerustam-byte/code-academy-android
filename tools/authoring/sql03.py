"""Урок SQL 3: связи между таблицами и JOIN."""
from sqlib import *

SCHEMA = """CREATE TABLE authors (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author_id INTEGER REFERENCES authors(id),
  year INTEGER
);

INSERT INTO authors (name) VALUES ('Толстой'), ('Булгаков'), ('Гоголь'), ('Чехов');

INSERT INTO books (title, author_id, year) VALUES
  ('Война и мир', 1, 1869),
  ('Анна Каренина', 1, 1878),
  ('Мастер и Маргарита', 2, 1967),
  ('Ревизор', 3, 1836);
"""
HEAD = SCHEMA.split("INSERT INTO authors")[0]
SETUP_B = HEAD + """INSERT INTO authors (name) VALUES ('Достоевский'), ('Пушкин'), ('Лермонтов');
INSERT INTO books (title, author_id, year) VALUES
  ('Идиот', 1, 1869), ('Бесы', 1, 1872), ('Евгений Онегин', 2, 1833),
  ('Сборник без автора', NULL, 1950), ('Современник', 2, 1936);
"""
SETUP_C = HEAD + """INSERT INTO authors (name) VALUES ('Грибоедов'), ('Гончаров');
INSERT INTO books (title, author_id, year) VALUES ('Горе от ума', 1, 1825), ('Обломов', 2, 1859), ('Обрыв', 2, 1869);
"""

Q_JOIN = "SELECT books.title, authors.name\nFROM books\nJOIN authors ON authors.id = books.author_id;\n"
Q_ALIAS = "SELECT b.title, a.name\nFROM books b\nJOIN authors a ON a.id = b.author_id\nWHERE b.year < 1900\nORDER BY b.title;\n"
Q_LEFT = "SELECT a.name, b.title\nFROM authors a\nLEFT JOIN books b ON b.author_id = a.id\nORDER BY a.name;\n"
Q_COUNT = "SELECT a.name, COUNT(b.id) AS n\nFROM authors a\nLEFT JOIN books b ON b.author_id = a.id\nGROUP BY a.id\nORDER BY a.name;\n"
ERR = "SELECT id, title, name\nFROM books\nJOIN authors ON authors.id = books.author_id;\n"
err_text = sq_err(ERR, SCHEMA)
assert "id" in err_text, err_text

use_file("schema.sql")
scenes = [
    scene("intro", "Зачем несколько таблиц", """
      Представьте, что в таблице книг рядом с каждой книгой записано имя автора. У Толстого две книги, значит, имя
      повторяется дважды, а если автор поменяет написание имени, исправлять придётся каждую строку. Правильнее
      хранить авторов в отдельной таблице, а в книге указывать только номер автора. Такой номер называется внешним ключом: он
      ссылается на строку другой таблицы.""",
          [NOTE("**Внешний ключ** — столбец, в котором лежит номер строки из другой таблицы: `books.author_id → authors.id`.", at="Такой номер")]),
    scene("data", "Две связанные таблицы", """
      У нас две таблицы. В авторах четыре строки, у каждой свой номер id. В книгах столбец author_id хранит номер автора.
      Например, у книги Война и мир стоит единица, значит, её написал автор с номером один. У Чехова пока нет
      книг.""",
          [T(SCHEMA, at="У нас две")]),
    scene("join", "JOIN: соединяем таблицы", """
      Чтобы вывести книгу рядом с именем автора, таблицы нужно соединить. Слово JOIN добавляет вторую таблицу, а после ON
      пишем условие связи: номер автора в книге равен номеру в авторах. Столбцы называем вместе с именем таблицы через
      точку, чтобы не путаться. Запускаем. Каждая книга получила имя своего автора, а Чехова в результате нет:
      у него нет книг.""",
          [CLEAR(file="main.sql"), T(Q_JOIN, at="Слово JOIN", file="main.sql"), HL([3], at="после ON", file="main.sql"),
           RUN(at="Запускаем", file="main.sql"), OUT(sq_out(Q_JOIN, SCHEMA), at="Каждая книга")]),
    scene("alias", "Короткие имена таблиц", """
      Писать полные имена таблиц долго. Поэтому таблицам дают короткие псевдонимы прямо после названия: books станет b,
      authors — a. Дальше используем их везде. Заодно оставим только книги до тысяча девятисотого года и
      отсортируем по названию. Запускаем.""",
          [CLEAR(file="main.sql"), T(Q_ALIAS, at="Поэтому таблицам", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(sq_out(Q_ALIAS, SCHEMA), at="Запускаем")]),
    scene("left", "LEFT JOIN: сохраняем все строки", """
      Обычный JOIN оставляет только те строки, у которых есть пара. А если нужны все авторы, даже без книг? Тогда
      используют LEFT JOIN: левая таблица, то есть та, что стоит после FROM, сохраняется целиком. Если пары нет, значения из
      правой таблицы будут пустыми, NULL. Запускаем. Чехов теперь в списке, а название книги у него пусто.""",
          [CLEAR(file="main.sql"), T(Q_LEFT, at="Тогда", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(sq_out(Q_LEFT, SCHEMA), at="Чехов теперь")]),
    scene("count", "JOIN и группировка", """
      Соединение можно сочетать с группировкой. Посчитаем книги у каждого автора: LEFT JOIN, затем GROUP BY по номеру автора.
      Здесь важная деталь: считаем COUNT от столбца правой таблицы, b точка id. Тогда пустые значения не считаются, и у
      Чехова получится ноль, а не один. Запускаем.""",
          [CLEAR(file="main.sql"), T(Q_COUNT, at="Посчитаем", file="main.sql"), HL([1], at="Здесь важная", file="main.sql"),
           RUN(at="Запускаем", file="main.sql"), OUT(sq_out(Q_COUNT, SCHEMA), at="Запускаем")]),
    scene("error", "Неоднозначный столбец", """
      Если столбец с таким именем есть в обеих таблицах, база не поймёт, какой имеется в виду. Запросим просто id и посмотрим
      на ошибку. Исправляется это просто: пишем имя таблицы или её псевдоним перед точкой.""",
          [CLEAR(file="main.sql"), T(ERR, at="Запросим", file="main.sql"), RUN(at="посмотрим", file="main.sql"),
           OUT(err_text.strip(), err=True, at="посмотрим")]),
    scene("summary", "Итог", """
      Подведём итог. Связанные данные хранят в разных таблицах, а связь задаёт внешний ключ. JOIN с условием ON соединяет
      таблицы и оставляет только пары. LEFT JOIN сохраняет все строки левой таблицы. Для подсчёта связанных строк считайте
      COUNT от столбца правой таблицы. А чтобы не путаться в одинаковых именах, используйте псевдонимы.""",
          [NOTE("`FROM a JOIN b ON b.a_id = a.id` — только пары · `LEFT JOIN` — все строки `a`", at="Подведём итог")]),
]
use_file(None)

notes = """
# SQL: связи и JOIN

```sql
SELECT b.title, a.name
FROM books b
JOIN authors a ON a.id = b.author_id;        -- только книги, у которых есть автор

SELECT a.name, b.title
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;     -- все авторы, даже без книг

SELECT a.name, COUNT(b.id) AS n
FROM authors a
LEFT JOIN books b ON b.author_id = a.id
GROUP BY a.id;                               -- сколько книг у каждого
```

- Внешний ключ: `books.author_id` хранит `authors.id`.
- `JOIN … ON условие` — условие связи пишут после `ON`.
- `LEFT JOIN` — строки левой таблицы сохраняются; без пары справа — `NULL`.
- Не найдено пары: `WHERE b.id IS NULL` (не `= NULL`!).
- `COUNT(b.id)` не считает `NULL`, `COUNT(*)` считает всё.
- Одинаковое имя столбца в обеих таблицах — пишите `a.id` или `b.id`.
"""

a1 = sql_task("a1-join", "write", "Книги с авторами",
    "Выведите название книги и имя автора (`title`, `name`) для всех книг, у которых **есть автор**. Порядок — по названию книги.",
    "Соединять таблицы через JOIN … ON.", "SELECT b.title, a.name\nFROM books b\nJOIN authors a ON a.id = b.author_id\nORDER BY b.title;",
    [(SCHEMA, False, None), (SETUP_B, True, "Книги без автора в результат не попадают"), (SETUP_C, True, None)],
    [("SELECT b.title, a.name FROM books b, authors a ORDER BY b.title;", "Нет условия связи: каждая книга с каждым автором."),
     ("SELECT b.title, a.name FROM books b JOIN authors a ON a.id = b.id ORDER BY b.title;", "Связь по неверным столбцам: нужно b.author_id."),
     ("SELECT b.title, a.name FROM books b LEFT JOIN authors a ON a.id = b.author_id ORDER BY b.title;", "LEFT JOIN оставляет книги без автора."),
     ("SELECT b.title, a.name FROM books b JOIN authors a ON a.id = b.author_id;", "Нет сортировки по названию.")],
    hints("Данные лежат в двух таблицах: нужно соединить их.", "FROM books b JOIN authors a …", "После ON пишут условие связи.", "Номер автора в книге равен номеру в таблице авторов.", "Сортировка — ORDER BY b.title в самом конце."),
    "ON b.author_id = a.id связывает каждую книгу с её автором; обычный JOIN оставляет только пары.",
    ordered=True, starter="SELECT title FROM books\n")

a2 = sql_task("a2-count-books", "write", "Сколько книг у автора",
    "Выведите имена **всех** авторов и число их книг: столбцы `name` и `n`. Авторы без книг тоже нужны (с нулём). Порядок — по имени автора.",
    "Считать связанные строки через LEFT JOIN и COUNT.", "SELECT a.name, COUNT(b.id) AS n\nFROM authors a\nLEFT JOIN books b ON b.author_id = a.id\nGROUP BY a.id\nORDER BY a.name;",
    [(SCHEMA, False, None), (SETUP_B, True, "Бывает, что у автора нет ни одной книги"), (SETUP_C, True, None)],
    [("SELECT a.name, COUNT(b.id) AS n FROM authors a JOIN books b ON b.author_id = a.id GROUP BY a.id ORDER BY a.name;", "Обычный JOIN теряет авторов без книг."),
     ("SELECT a.name, COUNT(*) AS n FROM authors a LEFT JOIN books b ON b.author_id = a.id GROUP BY a.id ORDER BY a.name;", "COUNT(*) считает и пустую строку: у автора без книг получается 1."),
     ("SELECT a.name, COUNT(b.id) AS n FROM authors a LEFT JOIN books b ON b.author_id = a.id ORDER BY a.name;", "Нет группировки.")],
    hints("Нужны все авторы, даже без книг: какой JOIN сохраняет левую таблицу?", "LEFT JOIN: слева authors, справа books.", "Сгруппируйте по автору.", "Считайте COUNT от столбца правой таблицы: пустые значения не считаются.", "ORDER BY a.name — в самом конце."),
    "COUNT(b.id) пропускает NULL, поэтому у автора без книг получается 0.",
    ordered=True, starter="SELECT name FROM authors\n")

a3 = sql_task("a3-no-books", "write", "Авторы без книг",
    "Выведите имена авторов, у которых **нет ни одной книги** (столбец `name`), по алфавиту.",
    "Находить строки без пары: LEFT JOIN … IS NULL.", "SELECT a.name\nFROM authors a\nLEFT JOIN books b ON b.author_id = a.id\nWHERE b.id IS NULL\nORDER BY a.name;",
    [(SCHEMA, False, None), (SETUP_B, True, "Авторов без книг может быть несколько"), (SETUP_C, True, "Если у всех авторов есть книги, результат пуст")],
    [("SELECT a.name FROM authors a LEFT JOIN books b ON b.author_id = a.id WHERE b.id = NULL ORDER BY a.name;", "Сравнение с NULL через = ничего не находит: нужен IS NULL."),
     ("SELECT a.name FROM authors a JOIN books b ON b.author_id = a.id WHERE b.id IS NULL ORDER BY a.name;", "Обычный JOIN не создаёт строк без пары."),
     ("SELECT a.name FROM authors a LEFT JOIN books b ON b.author_id = a.id ORDER BY a.name;", "Нет условия на отсутствие книги.")],
    hints("Нужны авторы, у которых в правой таблице нет пары.", "Сохраните всех авторов: LEFT JOIN.", "У авторов без книг столбцы книги пусты.", "Проверка на пустое значение — IS NULL, не = NULL.", "Проверяйте именно столбец правой таблицы, например b.id."),
    "После LEFT JOIN строки без пары имеют NULL в столбцах правой таблицы; IS NULL их отбирает.",
    ordered=True, starter="SELECT name FROM authors\n")

a4 = sql_task("a4-fix-join", "fix", "Исправьте соединение",
    "Запрос должен вывести название книги и имя автора для книг, **написанных после 1900 года**, по алфавиту названий. Сейчас таблицы соединены неверно. Найдите ошибку.",
    "Читать условие ON.", "SELECT b.title, a.name\nFROM books b\nJOIN authors a ON a.id = b.author_id\nWHERE b.year > 1900\nORDER BY b.title;",
    [(SCHEMA, False, None), (SETUP_B, True, None), (SETUP_C, True, "Если подходящих книг нет, результат пуст")],
    [("SELECT b.title, a.name FROM books b JOIN authors a ON a.id = b.id WHERE b.year > 1900 ORDER BY b.title;", "Связь по неверным столбцам осталась."),
     ("SELECT b.title, a.name FROM books b JOIN authors a ON a.id = b.author_id ORDER BY b.title;", "Потеряно условие на год.")],
    hints("Сравните результат с таблицей данных.", "Условие связи пишется после ON.", "Номер автора в книге — столбец author_id.", "Сравнивать нужно с id таблицы авторов.", "Остальные части запроса менять не нужно."),
    "ON сравнивает внешний ключ книги с первичным ключом автора; сравнение b.id = a.id связывает несвязанные строки.",
    ordered=True, starter="SELECT b.title, a.name\nFROM books b\nJOIN authors a ON a.id = b.id\nWHERE b.year > 1900\nORDER BY b.title;\n")

CODE5 = SCHEMA + "SELECT a.name, COUNT(b.id) AS n\nFROM authors a\nLEFT JOIN books b ON b.author_id = a.id\nWHERE a.id <> 3\nGROUP BY a.id\nHAVING COUNT(b.id) <> 1\nORDER BY a.name;\n"
a5 = sql_predict("a5-predict", "Что вернёт запрос?", CODE5,
    [("Булгаков | 1\nТолстой | 2\nЧехов | 0", "У Булгакова одна книга: условие HAVING её убирает."), ("Толстой | 2", "Чехов тоже подходит: у него 0 книг, а условие — «не равно 1».")],
    hints("Сначала LEFT JOIN сохраняет всех авторов.", "WHERE убирает автора с номером 3 — Гоголя.", "Книг: Толстой — 2, Булгаков — 1, Чехов — 0.", "HAVING оставляет группы, где число книг не равно единице.", "В конце строки упорядочены по имени автора, по алфавиту."),
    "WHERE выполняется до группировки, HAVING — после; сортировка идёт по именам по алфавиту.")

skills = {"sql.join": "JOIN и внешние ключи", "sql.left-join": "LEFT JOIN и отсутствие пары", "sql.alias": "Псевдонимы таблиц"}
write_lesson("sql-03-joins", "SQL: связи и JOIN",
             "Хранить связанные данные в разных таблицах и соединять их запросами JOIN и LEFT JOIN.",
             list(skills), ["sql-02-aggregates"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "JOIN без условия ON", "fix": "Каждая строка встанет с каждой: добавьте условие связи.", "errorType": "SQLError"},
              {"mistake": "Сравнение с NULL через =", "fix": "Используйте IS NULL и IS NOT NULL."},
              {"mistake": "COUNT(*) после LEFT JOIN", "fix": "Считайте COUNT от столбца правой таблицы."},
              {"mistake": "Одинаковое имя столбца в двух таблицах", "fix": "Пишите псевдоним таблицы: a.id, b.id."}],
             min_pass=3, pack="sql-basics", runner="sql")
merge_pack("sql-03-joins", skills)

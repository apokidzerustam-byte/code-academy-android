"""Урок SQL 1: таблица, SELECT, WHERE, ORDER BY, LIMIT. Вывод сцен считается тем же ядром, что в приложении."""
from mk import *

SCHEMA = """CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  year INTEGER
);

INSERT INTO books (title, author, year) VALUES
  ('Мастер и Маргарита', 'Булгаков', 1967),
  ('Война и мир', 'Толстой', 1869),
  ('Евгений Онегин', 'Пушкин', 1833),
  ('Анна Каренина', 'Толстой', 1878);
"""


def out(q):
    r = sql_out(q, SCHEMA)
    assert not r["stderr"], r
    return r["stdout"]


Q1 = "SELECT * FROM books;\n"
Q2 = "SELECT title, year FROM books\nWHERE author = 'Толстой';\n"
Q3 = "SELECT title, year FROM books\nORDER BY year;\n"
Q4 = "SELECT title FROM books\nORDER BY year DESC\nLIMIT 2;\n"
ERR = "SELECT titel FROM books;\n"
err_text = sql_out(ERR, SCHEMA)["stderr"]
assert "нет столбца «titel»" in err_text, err_text

use_file("schema.sql")
scenes = [
    scene("intro", "Зачем нужны базы данных", """
      Почти любое приложение хранит данные: пользователей, заказы, сообщения. Обычно их кладут в базу данных,
      где данные лежат в таблицах, как в электронной таблице: столбцы — это поля, а строки — записи. С базой говорят на языке
      запросов SQL. В приложении работает SQLite — та же база, что встроена в каждый телефон на Андроиде. При каждом
      запуске она создаётся заново и пустой, поэтому смело экспериментируйте: сломать ничего нельзя.""",
          [NOTE("Таблица = столбцы (поля) + строки (записи). Язык запросов — **SQL**.", at="где данные лежат")]),
    scene("create", "Создаём таблицу", """
      Создадим таблицу книг. Пишем CREATE TABLE, имя таблицы books и в скобках столбцы. У каждого столбца есть имя и тип.
      Столбец id — целое число и первичный ключ: уникальный номер строки, который база выдаёт сама. Название — текст,
      и оно обязательно, это значит NOT NULL. Ещё автор и год. Команда заканчивается точкой с запятой.""",
          [CLEAR(), T(SCHEMA.split("\n\n")[0] + "\n", at="Пишем CREATE TABLE"), HL([2], at="Столбец id"),
           HL([3], at="Название — текст"), HL([4, 5], at="Ещё автор")]),
    scene("insert", "Добавляем строки", """
      Теперь добавим книги командой INSERT INTO: имя таблицы, список столбцов и после слова VALUES сами значения в скобках.
      Текст в SQL пишут в одинарных кавычках, числа — без кавычек. Номер id мы не указываем: база проставит его сама.
      Этот файл называется схема. В проектах приложения схема выполняется перед каждым запросом, так что таблица всегда на месте.""",
          [T("\n" + SCHEMA.split("\n\n")[1], at="Теперь добавим"), HL([9, 10, 11, 12], at="Текст в SQL")]),
    scene("select-all", "SELECT: выбрать всё", """
      Переходим к запросам. Откроем файл main и напишем SELECT, звёздочку, FROM books. Звёздочка значит «все столбцы».
      Запускаем. Получилась таблица: четыре книги со всеми полями, и id у них проставлены по порядку. Внизу приложение
      пишет, сколько строк вернул запрос.""",
          [CLEAR(file="main.sql"), T(Q1, at="Откроем файл", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(out(Q1), at="Получилась таблица")]),
    scene("where", "WHERE: условие", """
      Обычно нужны не все строки. Условие пишут после слова WHERE. Выберем только названия и годы книг Толстого:
      SELECT title, year FROM books WHERE author равно Толстой в одинарных кавычках. Запускаем. Осталось две строки.
      Сравнивать можно и числа: больше, меньше, не равно.""",
          [CLEAR(file="main.sql"), T(Q2, at="Выберем только", file="main.sql"), HL([2], at="Выберем только", file="main.sql"),
           RUN(at="Запускаем", file="main.sql"), OUT(out(Q2), at="Осталось две")]),
    scene("order", "ORDER BY: сортировка", """
      Порядок строк база не обещает, если его не попросить. Сортировка — ORDER BY и имя столбца. Отсортируем книги по году.
      Запускаем: сначала Онегин тысяча восемьсот тридцать третьего года, в конце — Мастер и Маргарита. Чтобы сортировать
      от большего к меньшему, после имени столбца пишут DESC.""",
          [CLEAR(file="main.sql"), T(Q3, at="Отсортируем", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(out(Q3), at="сначала Онегин")]),
    scene("limit", "LIMIT: первые строки", """
      А если нужны только две самые новые книги? Сортируем по году в обратном порядке, DESC, и добавляем LIMIT два.
      Запускаем. Получили Мастера и Маргариту и Анну Каренину. Такой запрос — основа любого «топа»: самые новые, самые дорогие,
      самые популярные.""",
          [CLEAR(file="main.sql"), T(Q4, at="Сортируем по году", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(out(Q4), at="Получили")]),
    scene("error", "Ошибка в запросе", """
      Ошибиться в SQL легко. Напишем titel вместо title и запустим. База отвечает: нет столбца titel. Приложение переводит
      сообщение и показывает номер строки, а в скобках оставляет оригинал на английском — его удобно искать в интернете.
      Проверьте написание имени, и запрос заработает.""",
          [CLEAR(file="main.sql"), T(ERR, at="Напишем", file="main.sql"), RUN(at="и запустим", file="main.sql"),
           OUT("нет столбца «titel»", err=True, at="База отвечает")], stress={"titel": "ти́тел"}),
    scene("summary", "Итог", """
      Подведём итог. CREATE TABLE создаёт таблицу, INSERT INTO добавляет строки. SELECT выбирает столбцы, WHERE оставляет
      нужные строки, ORDER BY сортирует, а LIMIT ограничивает количество. Текст — в одинарных кавычках, команда заканчивается
      точкой с запятой.""",
          [NOTE("`SELECT столбцы FROM таблица WHERE условие ORDER BY столбец [DESC] LIMIT n;`", at="Подведём итог")]),
]
use_file(None)

notes = """
# SQL: первые запросы

**Таблица** состоит из столбцов (полей) и строк (записей). Язык запросов к базе — **SQL**.
В приложении работает **SQLite**; база создаётся заново и пустой при каждом запуске.

## Создать таблицу и добавить строки

```sql
CREATE TABLE books (
  id INTEGER PRIMARY KEY,   -- номер строки, база выдаёт сама
  title TEXT NOT NULL,      -- обязательное поле
  author TEXT,
  year INTEGER
);
INSERT INTO books (title, author, year) VALUES ('Война и мир', 'Толстой', 1869);
SELECT * FROM books;
```

- Текст пишут в **одинарных** кавычках: `'Толстой'`. Числа — без кавычек.
- Команда заканчивается **точкой с запятой**.

## Выбрать данные

| Что нужно | Как написать |
|---|---|
| все столбцы | `SELECT * FROM books;` |
| некоторые столбцы | `SELECT title, year FROM books;` |
| только подходящие строки | `... WHERE author = 'Толстой'` |
| сравнение чисел | `WHERE year > 1900`, `<`, `>=`, `<=`, `<>` (не равно) |
| сортировка | `ORDER BY year` (по возрастанию), `ORDER BY year DESC` (по убыванию) |
| первые n строк | `LIMIT 2` (после ORDER BY) |

Порядок частей запроса всегда такой: `SELECT … FROM … WHERE … ORDER BY … LIMIT …`.

## Частые ошибки

- **нет столбца «…»** (`no such column`) — опечатка в имени столбца.
- **нет таблицы «…»** (`no such table`) — таблица не создана или имя написано иначе.
- **синтаксическая ошибка рядом с «…»** — опечатка в ключевом слове или пропущена запятая между столбцами.
- Текст без кавычек — `WHERE author = Толстой` — база ищет **столбец** «Толстой».
- Без `ORDER BY` порядок строк не гарантирован: если порядок важен — сортируйте.
"""

SETUP_A = SCHEMA
SETUP_B = """CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  year INTEGER
);
INSERT INTO books (title, author, year) VALUES
  ('Идиот', 'Достоевский', 1869),
  ('Собачье сердце', 'Булгаков', 1987),
  ('Белая гвардия', 'Булгаков', 1925),
  ('Бесы', 'Достоевский', 1872),
  ('Мёртвые души', 'Гоголь', 1842);
"""
SETUP_C = """CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  year INTEGER
);
INSERT INTO books (title, author, year) VALUES
  ('Отцы и дети', 'Тургенев', 1862),
  ('Ревизор', 'Гоголь', 1836),
  ('Обломов', 'Гончаров', 1859);
"""


def rows(code, setup):
    r = sql_out(code, "")  # не используется — оставлено для ясности
    return r


def expected(code, setup, columns=True):
    """Ожидаемый результат — из эталона, выполненного тем же ядром (и перепроверяется валидатором в Chromium)."""
    import subprocess
    p = subprocess.run(["node", "--experimental-sqlite", "--no-warnings", "-e", """
const {DatabaseSync} = require('node:sqlite');
let s=''; process.stdin.on('data', d => s += d).on('end', () => {
  const {setup, code} = JSON.parse(s); const db = new DatabaseSync(':memory:'); db.exec(setup);
  const st = db.prepare(code.trim().replace(/;$/, '')); st.setReturnArrays(true);
  const cols = st.columns().map(c => c.name); const rows = st.all().map(r => r.map(v => typeof v === 'bigint' ? Number(v) : v));
  process.stdout.write(JSON.stringify({columns: cols, rows}));
});"""], input=json.dumps({"setup": setup, "code": code}), capture_output=True, text=True, check=True)
    e = json.loads(p.stdout)
    return e if columns else {"rows": e["rows"]}


# --- Задание 1: WHERE ---------------------------------------------------------
S1 = "SELECT title FROM books\nWHERE year > 1900;\n"
t1 = {"kind": "sql", "cases": [
    {"id": "v1", "setup": SETUP_A, "expected": expected(S1, SETUP_A)},
    {"id": "h1", "hidden": True, "setup": SETUP_B, "expected": expected(S1, SETUP_B),
     "hint": "Условие должно работать для любых книг, а не только для примера"},
    {"id": "h2", "hidden": True, "setup": SETUP_C, "expected": expected(S1, SETUP_C),
     "hint": "Если подходящих книг нет, запрос возвращает пустую таблицу"},
]}
a1 = asg("a1-where", "write", "Книги XX века",
         "В таблице `books` есть столбцы `id`, `title`, `author`, `year`.\n\n"
         "Напишите запрос, который выводит **только названия** (`title`) книг, написанных **после 1900 года**.",
         "Выбирать строки условием WHERE.", "Таблица books (создаётся автоматически перед запуском).",
         "Один столбец title: книги с year больше 1900.",
         ["Порядок строк не важен.", "Нажмите «Запустить», чтобы увидеть данные таблицы: SELECT * FROM books;"],
         hints("Нужны не все строки, а только подходящие — это работа для WHERE.",
               "Выберите один столбец: SELECT title FROM books.",
               "Условие на число пишется без кавычек: year > 1900.",
               "Порядок частей: SELECT … FROM … WHERE …;",
               "SELECT title FROM books WHERE year > 1900;"),
         t1, S1, "WHERE year > 1900 оставляет только строки, где год больше 1900; SELECT title выводит один столбец.",
         ["Выводится один столбец title.", "Работает на любых данных."],
         [("SELECT title FROM books WHERE title = 'Мастер и Маргарита';", "Ответ «зашит» под пример — на других данных неверно."),
          ("SELECT * FROM books WHERE year > 1900;", "Лишние столбцы: нужен только title."),
          ("SELECT title FROM books WHERE year < 1900;", "Условие наоборот."),
          ("SELECT title FROM books;", "Нет условия — выводятся все книги.")],
         starter="-- Ваш запрос\n")

# --- Задание 2: ORDER BY + LIMIT ----------------------------------------------
S2 = "SELECT title, year FROM books\nORDER BY year\nLIMIT 2;\n"
t2 = {"kind": "sql", "ordered": True, "cases": [
    {"id": "v1", "setup": SETUP_A, "expected": expected(S2, SETUP_A)},
    {"id": "h1", "hidden": True, "setup": SETUP_B, "expected": expected(S2, SETUP_B), "hint": "Сначала сортировка, потом LIMIT"},
    {"id": "h2", "hidden": True, "setup": SETUP_C, "expected": expected(S2, SETUP_C)},
]}
a2 = asg("a2-oldest", "write", "Две самые старые книги",
         "Выведите название и год (`title`, `year`) **двух самых старых** книг: сначала самую старую.",
         "Сортировать (ORDER BY) и ограничивать (LIMIT).", "Таблица books.",
         "Два столбца title, year; две строки по возрастанию года.",
         ["Порядок строк важен."],
         hints("Самые старые — это самые маленькие годы.",
               "Отсортируйте строки по году: ORDER BY year.",
               "По умолчанию ORDER BY сортирует по возрастанию — от старых к новым.",
               "Ограничить число строк можно словом LIMIT в самом конце запроса.",
               "SELECT title, year FROM books ORDER BY year LIMIT 2;"),
         t2, S2, "ORDER BY year ставит книги от старых к новым, LIMIT 2 оставляет первые две.",
         ["Ровно две строки.", "Сначала самая старая книга."],
         [("SELECT title, year FROM books ORDER BY year DESC LIMIT 2;", "DESC выбирает самые новые, а не самые старые."),
          ("SELECT title, year FROM books LIMIT 2;", "Без сортировки — просто первые добавленные строки."),
          ("SELECT title, year FROM books ORDER BY year;", "Нет LIMIT — выводятся все книги."),
          ("SELECT title, year FROM books ORDER BY title LIMIT 2;", "Сортировка по названию, а не по году.")],
         starter="SELECT title, year FROM books\n")

# --- Задание 3: исправить ошибки -----------------------------------------------
S3 = "SELECT title, author FROM books\nWHERE author = 'Булгаков';\n"
STARTER3 = "SELECT title author FROM books\nWHERE author = Булгаков;\n"
t3 = {"kind": "sql", "cases": [
    {"id": "v1", "setup": SETUP_A, "expected": expected(S3, SETUP_A)},
    {"id": "h1", "hidden": True, "setup": SETUP_B, "expected": expected(S3, SETUP_B)},
]}
a3 = asg("a3-fix", "fix", "Исправьте запрос",
         "Запрос должен вывести названия и авторов (`title`, `author`) всех книг Булгакова, но в нём две ошибки. Найдите и исправьте их.",
         "Читать сообщения об ошибках SQL.", "Таблица books.", "Два столбца: title и author, только книги Булгакова.",
         ["Запустите запрос и прочитайте сообщение об ошибке."],
         hints("Запустите запрос: база подскажет, где первая ошибка.",
               "Посмотрите, как записан текст в условии WHERE.",
               "Текст в SQL пишется в одинарных кавычках, иначе база ищет столбец с таким именем.",
               "Сколько столбцов выводит SELECT? Между столбцами нужна запятая — без неё второе слово становится новым именем первого столбца.",
               "SELECT title, author FROM books WHERE author = 'Булгаков';"),
         t3, S3, "Текст 'Булгаков' в кавычках — это значение, а не имя столбца. Столбцы в SELECT разделяются запятыми: без запятой `title author` — это столбец title, переименованный в author.",
         ["Нет ошибок выполнения.", "Два столбца."],
         [(STARTER3, "Обе ошибки на месте."),
          ("SELECT title author FROM books\nWHERE author = 'Булгаков';\n", "Исправлены кавычки, но не запятая: выводится один столбец.")],
         starter=STARTER3)
# Текст в двойных кавычках SQLite (sql.js) принимает как строку, если такого столбца нет, — это не «неверное решение»
# для проверки, поэтому в типовые ошибки не входит; в конспекте сказано писать текст в одинарных кавычках.

# --- Задание 4: предсказать результат -----------------------------------------
CODE4 = "CREATE TABLE t (n INTEGER);\nINSERT INTO t VALUES (5), (2), (8), (2);\nSELECT n FROM t\nWHERE n > 2\nORDER BY n DESC;\n"
ans4 = "\n".join(str(r[0]) for r in expected("SELECT n FROM t WHERE n > 2 ORDER BY n DESC", "CREATE TABLE t (n INTEGER); INSERT INTO t VALUES (5), (2), (8), (2);")["rows"])
a4 = asg("a4-predict", "predict", "Что вернёт запрос?",
         "Какие числа и в каком порядке вернёт запрос? Напишите каждое число с новой строки (без заголовка таблицы).",
         "Понимать WHERE и ORDER BY без запуска.", "—", "Числа по одному в строке.", [],
         hints("Сначала WHERE отбрасывает строки, потом ORDER BY их сортирует.",
               "Условие n > 2 — строго больше: двойки не подходят.",
               "DESC — от большего к меньшему.",
               "Останутся два числа.",
               "Ответ: " + ans4.replace("\n", ", ") + " — каждое число с новой строки."),
         {"kind": "answer", "expected_answer": ans4}, ans4,
         "Строки 2 и 2 не проходят условие n > 2; оставшиеся 5 и 8 сортируются по убыванию.",
         ["Правильные числа в правильном порядке."],
         [("5\n8", "Порядок по возрастанию, а нужен DESC."), ("8\n5\n2\n2", "Двойки не проходят условие n > 2."),
          ("8\n5\n2", "Двойки не проходят условие n > 2.")],
         code=CODE4)

# --- Задание 5: UPDATE (проверочный запрос после кода ученика) -------------------
S5 = "UPDATE books SET year = 1966\nWHERE title = 'Мастер и Маргарита';\n"
CHECK5 = "SELECT title, year FROM books ORDER BY id"
t5 = {"kind": "sql", "cases": [
    {"id": "v1", "setup": SETUP_A, "query": CHECK5, "expected": expected(CHECK5, SETUP_A + S5, columns=False)},
    {"id": "h1", "hidden": True, "setup": SETUP_B + "INSERT INTO books (title, author, year) VALUES ('Мастер и Маргарита', 'Булгаков', 1967);",
     "query": CHECK5, "expected": expected(CHECK5, SETUP_B + "INSERT INTO books (title, author, year) VALUES ('Мастер и Маргарита', 'Булгаков', 1967);" + S5, columns=False),
     "hint": "Меняться должна только одна книга — с этим названием"},
]}
a5 = asg("a5-update", "write", "Исправьте год",
         "Роман «Мастер и Маргарита» впервые напечатали в журнале в **1966** году. Исправьте год **только у этой книги** командой UPDATE.",
         "Изменять данные: UPDATE … SET … WHERE.", "Таблица books.", "У книги «Мастер и Маргарита» год 1966, остальные строки не изменились.",
         ["Не забудьте WHERE: без условия UPDATE изменит все строки."],
         hints("Изменение строк — команда UPDATE.",
               "UPDATE таблица SET столбец = значение …",
               "Какую строку менять, говорит WHERE — как в SELECT.",
               "Название — текст, пишите его в одинарных кавычках точно как в таблице.",
               "UPDATE books SET year = 1966 WHERE title = 'Мастер и Маргарита';"),
         t5, S5, "UPDATE меняет значения в строках, которые подходят под WHERE. Без WHERE изменились бы все книги.",
         ["Изменена ровно одна строка."],
         [("UPDATE books SET year = 1966;", "Нет WHERE — изменились все книги."),
          ("UPDATE books SET year = 1966 WHERE author = 'Булгаков';", "Условие по автору захватывает и другие книги Булгакова."),
          ("SELECT title, year FROM books;", "SELECT только читает данные, а нужно их изменить.")],
         starter="-- Измените год одной книги\n")

skills = {"sql.tables": "Таблицы, CREATE и INSERT", "sql.select": "SELECT и столбцы", "sql.where": "Условия WHERE",
          "sql.order": "Сортировка и LIMIT", "sql.update": "Изменение данных UPDATE", "sql.errors": "Ошибки в SQL"}
write_pack("sql-basics", 9, "Базы данных: SQL", "SQLite прямо в приложении: таблицы, запросы, изменение данных. Пилот этапа 9.",
           "sql", ["sql-01-select"], skills)
write_lesson("sql-01-select", "SQL: первые запросы SELECT",
             "Создавать таблицу, добавлять строки и выбирать данные запросами SELECT, WHERE, ORDER BY и LIMIT; изменять данные UPDATE.",
             list(skills), [], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Текст в условии без кавычек", "fix": "Пишите 'Толстой' в одинарных кавычках — без них база ищет столбец.", "errorType": "SQLError"},
              {"mistake": "Опечатка в имени столбца или таблицы", "fix": "Сверьте имя со схемой: SELECT * FROM таблица; покажет все столбцы.", "errorType": "SQLError"},
              {"mistake": "Пропущена запятая между столбцами", "fix": "SELECT title, year — без запятой второе слово станет псевдонимом первого столбца."},
              {"mistake": "UPDATE или DELETE без WHERE", "fix": "Без условия команда меняет все строки таблицы."},
              {"mistake": "Ожидали порядок без ORDER BY", "fix": "Порядок строк гарантирует только ORDER BY."}],
             min_pass=3, pack="sql-basics", runner="sql")

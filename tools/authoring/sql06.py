"""Урок SQL 6: индексы — ускорение поиска, составные и уникальные индексы, цена индексов.
Результаты считает настоящий SQLite. Тексты планов запросов в сценах показаны как справочные заметки: номера и текст плана зависят от версии SQLite."""
from sqlib import *

USERS = """CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL,
  name TEXT NOT NULL
);

INSERT INTO users (email, name) VALUES
  ('anna@example.com', 'Анна'), ('ivan@example.com', 'Иван'), ('olga@example.com', 'Ольга'),
  ('petr@example.com', 'Пётр'), ('eva@example.com', 'Ева'), ('oleg@example.com', 'Олег');
"""
Q_CREATE = "CREATE INDEX idx_users_email ON users(email);\n\nSELECT name, tbl_name FROM sqlite_master WHERE type = 'index';\n"
Q_PLAN = "EXPLAIN QUERY PLAN\nSELECT name FROM users WHERE email = 'ivan@example.com';\n"
NOTES_T = """CREATE TABLE notes (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  created TEXT NOT NULL,
  text TEXT NOT NULL
);
"""
Q_COMPOSITE = ("CREATE INDEX idx_notes_user_created ON notes(user_id, created);\n\n"
               "SELECT seqno, name FROM pragma_index_info('idx_notes_user_created') ORDER BY seqno;\n")
Q_UNIQUE = "CREATE UNIQUE INDEX idx_users_email ON users(email);\n\nINSERT INTO users (email, name) VALUES ('anna@example.com', 'Другая Анна');\n"
err_text = sq_err(Q_UNIQUE, USERS)
assert "UNIQUE constraint failed" in err_text, err_text
Q_TRAPS = ("-- индекс по email не помогает этим запросам:\nSELECT name FROM users WHERE lower(email) = 'ivan@example.com';\nSELECT name FROM users WHERE email LIKE '%@example.com';\n\n"
           "-- индекс по выражению поможет первому:\nCREATE INDEX idx_users_lower_email ON users(lower(email));\n")

use_file("schema.sql")
scenes = [
    scene("intro", "Зачем нужен индекс", """
      Представьте толстую книгу без оглавления и предметного указателя. Чтобы найти слово, придётся листать все страницы подряд. База
      данных без индекса делает то же самое: чтобы найти пользователя с нужной почтой, она читает таблицу строка за строкой, от начала до
      конца. Это называется полным сканированием. На шести строках незаметно, а на миллионе поиск растянется на секунды. Индекс, это как
      предметный указатель: отсортированная копия одного или нескольких столбцов, где каждому значению сопоставлена строка таблицы.
      Искать в отсортированных данных можно очень быстро, примерно как в словаре, деля область поиска пополам.
      Разберём, как индекс создаётся, как проверить, что он работает, и какую цену за него приходится платить. Начнём с самого простого
      примера: таблица пользователей и поиск по почте.""",
          [NOTE("**Без индекса:** база читает всю таблицу (полное сканирование). **С индексом:** переходит сразу к нужной строке.", at="Индекс, это как"),
           NOTE("Индекс = отсортированная копия столбца + ссылки на строки", at="Искать в отсортированных")]),
    scene("create", "Создаём индекс", """
      Индекс создаёт команда CREATE INDEX. Ей нужны имя индекса, таблица и в скобках столбец. Имя принято составлять из префикса idx,
      названия таблицы и столбца, так его легко узнать. Мы строим индекс по почте, потому что по ней ищем пользователя. Чтобы убедиться, что
      индекс появился, заглянем в служебную таблицу sqlite master: в ней SQLite хранит описание всех таблиц и индексов. Запустим:
      индекс на месте и относится к таблице users.""",
          [CLEAR(file="schema.sql"), T(USERS, at="Индекс создаёт", file="schema.sql"), CLEAR(file="main.sql"), T(Q_CREATE, at="Индекс создаёт", file="main.sql"),
           HL([1], at="Ей нужны", file="main.sql"), HL([3], at="заглянем", file="main.sql"), RUN(at="Запустим", file="main.sql"),
           OUT(sq_out(Q_CREATE, USERS), at="Запустим")]),
    scene("plan", "Как проверить, что индекс работает", """
      Как узнать, использует ли база индекс? Перед запросом пишут слова EXPLAIN QUERY PLAN: база не выполняет запрос, а рассказывает, как
      собирается его выполнять. Если в плане стоит слово SCAN, значит таблица читается целиком. Если SEARCH и слова USING INDEX, значит
      используется индекс, и поиск быстрый. Точный текст плана зависит от версии SQLite, поэтому мы покажем его в заметках, а в заданиях
      будем проверять сами индексы. Запомните сам приём: прежде чем гадать, почему запрос медленный, посмотрите его план.""",
          [CLEAR(file="main.sql"), T(Q_PLAN, at="Как узнать", file="main.sql"),
           NOTE("Без индекса: `SCAN users` — читается вся таблица", at="Если в плане"),
           NOTE("С индексом: `SEARCH users USING INDEX idx_users_email (email=?)` — быстрый поиск", at="Если SEARCH")]),
    scene("cost", "Цена индекса", """
      Если индекс ускоряет поиск, почему бы не построить их на все столбцы? Потому что у индексов есть цена. Первая: место. Индекс это
      отдельная структура на диске. Вторая, важнее: каждое добавление, изменение или удаление строки обновляет и все индексы таблицы,
      поэтому запись замедляется. Индексы нужны там, где данные читают чаще, чем пишут. Что индексировать? Столбцы, по которым часто
      фильтруют в WHERE, соединяют таблицы в JOIN и сортируют в ORDER BY. А вот столбец с двумя значениями, например «выполнено» или нет,
      индексировать почти бесполезно: половина таблицы всё равно подойдёт. И одна приятная новость: первичный ключ уже быстрый сам по себе,
      отдельный индекс для него не нужен.""",
          [NOTE("Индекс ускоряет **чтение**, но замедляет **запись** и занимает место", at="Вторая, важнее"),
           NOTE("Индексируйте столбцы из `WHERE`, `JOIN`, `ORDER BY` с большим числом разных значений", at="Что индексировать"),
           NOTE("Первичный ключ индексировать не нужно: он уже быстрый", at="И одна приятная")]),
    scene("composite", "Составной индекс", """
      Индекс может охватывать несколько столбцов. Пусть в таблице заметок мы часто выбираем заметки одного пользователя и сортируем их по
      дате. Тогда подходит составной индекс по user id и created. Порядок столбцов здесь важен. Индекс отсортирован сначала по первому
      столбцу, внутри него по второму, как телефонная книга сначала по фамилии, затем по имени. Поэтому такой индекс помогает запросам по
      user id и по паре user id с датой. Но искать по одной дате он не поможет: так же, как в книге не найти все имена Анна, не зная фамилий.
      Это называется правилом левого префикса. Если нужен и поиск только по дате, понадобится отдельный индекс по ней. Запустим и посмотрим,
      в каком порядке столбцы вошли в индекс.""",
          [CLEAR(file="schema.sql"), T(NOTES_T, at="Индекс может", file="schema.sql"), CLEAR(file="main.sql"), T(Q_COMPOSITE, at="Тогда подходит", file="main.sql"),
           HL([1], at="Тогда подходит", file="main.sql"), RUN(at="Запустим", file="main.sql"), OUT(sq_out(Q_COMPOSITE, NOTES_T), at="Запустим")]),
    scene("unique", "Уникальный индекс", """
      Есть особый вид индекса: уникальный. К слову CREATE добавляется UNIQUE, и теперь индекс не только ускоряет поиск, но и не позволяет
      повторять значения. По сути это то же ограничение UNIQUE, только созданное отдельной командой. Для почты пользователя это то, что
      нужно: поиск по ней быстрый, а два человека с одной почтой невозможны. Проверим: создаём уникальный индекс и пытаемся добавить ещё
      одну Анну с той же почтой. База откажет и скажет, какое ограничение нарушено.""",
          [CLEAR(file="schema.sql"), T(USERS, at="Есть особый", file="schema.sql"), CLEAR(file="main.sql"), T(Q_UNIQUE, at="Есть особый", file="main.sql"), HL([1], at="К слову CREATE", file="main.sql"),
           RUN(at="Проверим", file="main.sql"), OUT(err_text.strip(), err=True, at="База откажет")]),
    scene("practice", "Как решить, что индексировать", """
      Теперь на практике. Не стройте индексы заранее на всякий случай. Сначала посмотрите на свои запросы. Экран входа ищет пользователя по
      почте: нужен индекс по почте, и лучше уникальный. Экран заметок показывает заметки одного пользователя, новые сверху: нужен
      составной индекс по пользователю и дате. Отчёт считает задачи по категориям: индекс по номеру категории. Дальше действуйте по
      порядку. Нашли медленный запрос. Посмотрели его план. Добавили индекс. Снова посмотрели план и убедились, что он сменился с
      сканирования на поиск. Если не сменился, значит, индекс не подходит этому запросу, и его лучше удалить, чтобы не замедлять запись.""",
          [NOTE("Вход по почте → уникальный индекс по `email`", at="Экран входа"),
           NOTE("Заметки пользователя по дате → составной `(user_id, created)`", at="Экран заметок"),
           NOTE("Найти медленный запрос → посмотреть план → добавить индекс → посмотреть план снова", at="Дальше действуйте")]),
    scene("traps", "Когда индекс не помогает", """
      Бывает, что индекс есть, а запрос по-прежнему медленный. Первая причина: над столбцом вызывается функция. Условие с lower от
      почты уже не совпадает с тем, что лежит в индексе, и база читает таблицу целиком. Вторая причина: LIKE, у которого шаблон начинается
      с процента. Искать по концу строки по отсортированному началу невозможно. Что делать? Для функции можно создать индекс по самому
      выражению, SQLite это умеет. А шаблон с процентом в начале лучше не использовать там, где важна скорость. Помните и ещё про
      лишние индексы: если есть индекс по двум столбцам, отдельный индекс по первому из них обычно уже не нужен.""",
          [CLEAR(file="main.sql"), T(Q_TRAPS, at="Бывает", file="main.sql"), HL([2], at="Первая причина", file="main.sql"), HL([3], at="Вторая причина", file="main.sql"),
           HL([6], at="Для функции", file="main.sql")]),
    scene("summary", "Итог", """
      Подведём итог. Индекс это отсортированная копия столбцов, она ускоряет поиск по ним. Создаётся командой CREATE INDEX, а удаляется
      командой DROP INDEX. Работает ли индекс, показывает EXPLAIN QUERY PLAN. Составной индекс подчиняется правилу левого префикса, уникальный
      заодно запрещает повторы. Платить приходится местом и скоростью записи, поэтому индексируйте только то, что действительно ищут,
      соединяют и сортируют. В заданиях вы создадите обычный, уникальный и составной индексы, удалите лишний и предскажете результат
      вставки с уникальным индексом. Критерий прохождения: решить не меньше трёх заданий из пяти.""",
          [NOTE("`CREATE INDEX idx_… ON таблица(столбец)` · `CREATE UNIQUE INDEX` · `DROP INDEX` · `EXPLAIN QUERY PLAN`", at="Подведём итог")]),
]
use_file(None)

notes = """
# SQL: индексы

Индекс — отсортированная копия одного или нескольких столбцов со ссылками на строки таблицы. Без индекса база читает таблицу целиком (**полное сканирование**), с индексом переходит сразу к нужным строкам.

```sql
CREATE INDEX idx_users_email ON users(email);          -- обычный индекс
CREATE UNIQUE INDEX idx_users_email ON users(email);   -- уникальный: ещё и запрещает повторы
CREATE INDEX idx_notes_user_created ON notes(user_id, created);   -- составной
DROP INDEX idx_users_email;                             -- удалить

EXPLAIN QUERY PLAN SELECT name FROM users WHERE email = 'ivan@example.com';
-- SCAN users                                       — читается вся таблица
-- SEARCH users USING INDEX idx_users_email (email=?) — используется индекс

SELECT name, tbl_name FROM sqlite_master WHERE type = 'index';   -- какие индексы есть
SELECT seqno, name FROM pragma_index_info('idx_notes_user_created') ORDER BY seqno;   -- столбцы индекса
```

- **Цена:** место на диске и более медленная запись (каждое изменение обновляет все индексы).
- Индексируйте столбцы из `WHERE`, `JOIN`, `ORDER BY` с большим числом разных значений; столбцы с двумя значениями почти бесполезны.
- Первичный ключ уже быстрый: отдельный индекс не нужен.
- **Составной индекс** работает по правилу левого префикса: `(user_id, created)` помогает запросам по `user_id` и по паре, но не по одному `created`.
- Индекс не помогает, если над столбцом вызывается функция (`lower(email) = …`) или шаблон `LIKE` начинается с `%`; для функции можно построить индекс по выражению: `CREATE INDEX … ON users(lower(email))`.
- Лишний индекс — тот, что совпадает с левой частью другого: его можно удалить.
- Точный текст плана запроса зависит от версии SQLite.
"""

LIST = "SELECT name, tbl_name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
INFO_EMAIL = "SELECT name FROM pragma_index_info('idx_users_email') ORDER BY seqno;"
LIST_UNIQ = "SELECT name, \"unique\" FROM pragma_index_list('users') ORDER BY name;"
OTHER = USERS.split("INSERT INTO")[0] + "INSERT INTO users (email, name) VALUES ('x@y.ru', 'Икс'), ('z@y.ru', 'Зет');\n"

a1 = sql_task("a1-index", "write", "Индекс по почте",
              "Создайте обычный (не уникальный) индекс `idx_users_email` на столбце `email` таблицы `users`.",
              "Создавать индекс командой CREATE INDEX.", "CREATE INDEX idx_users_email ON users(email);",
              [(USERS, False, None, LIST), (USERS, True, "Индекс должен охватывать столбец email", INFO_EMAIL), (OTHER, True, "Индекс обычный, не уникальный", LIST_UNIQ)],
              [("CREATE INDEX idx_users_name ON users(name);", "Другое имя индекса и другой столбец."),
               ("CREATE INDEX idx_users_email ON users(name);", "Индекс создан по столбцу name, а нужен email."),
               ("CREATE UNIQUE INDEX idx_users_email ON users(email);", "Индекс должен быть обычным: слово UNIQUE лишнее."),
               ("-- индекс не создан\n", "Индекс не создан.")],
              hints("Индекс создаёт команда CREATE INDEX.", "После неё пишут имя индекса, затем слово ON и таблицу.", "Столбец указывают в скобках после имени таблицы.", "Имя уже задано в условии: idx_users_email.",
                    "CREATE INDEX idx_users_email ON users(email);"),
              "CREATE INDEX имя ON таблица(столбец) строит индекс. Слово UNIQUE превратило бы его в уникальный, а здесь нужен обычный.",
              starter="-- Создайте индекс\n")

a2 = sql_task("a2-unique", "write", "Уникальная почта",
              "Две учётные записи с одной почтой недопустимы. Создайте **уникальный** индекс `idx_users_email` на столбце `email` таблицы `users`.",
              "Запретить повторы индексом UNIQUE.", "CREATE UNIQUE INDEX idx_users_email ON users(email);",
              [(USERS, False, None, LIST_UNIQ), (OTHER, True, "Индекс должен быть уникальным", LIST_UNIQ), (USERS, True, "Индекс охватывает email", INFO_EMAIL)],
              [("CREATE INDEX idx_users_email ON users(email);", "Индекс не уникальный: повторы возможны."),
               ("CREATE UNIQUE INDEX idx_users_name ON users(name);", "Другой индекс: нужен idx_users_email по email."),
               ("CREATE UNIQUE INDEX idx_users_email ON users(name);", "Уникальный индекс создан по другому столбцу.")],
              hints("Уникальный индекс создаёт та же команда, но с дополнительным словом.", "Слово UNIQUE ставится между CREATE и INDEX.", "Имя индекса idx_users_email, таблица users, столбец email.",
                    "Уникальные значения нужны для столбца email.", "CREATE UNIQUE INDEX idx_users_email ON users(email);"),
              "Уникальный индекс одновременно ускоряет поиск и запрещает повторяющиеся значения столбца.",
              starter="-- Создайте уникальный индекс\n")

IDX_NOTES = "SELECT seqno, name FROM pragma_index_info('idx_notes_user_created') ORDER BY seqno;"
NOTES_B = NOTES_T + "INSERT INTO notes (user_id, created, text) VALUES (1, '2026-01-01', 'a'), (2, '2026-01-02', 'b');\n"
a3 = sql_task("a3-composite", "write", "Составной индекс",
              "Заметки одного пользователя часто выбирают и сортируют по дате. Создайте составной индекс `idx_notes_user_created` на таблице `notes`: сначала `user_id`, затем `created`.",
              "Создавать составной индекс и помнить о порядке столбцов.", "CREATE INDEX idx_notes_user_created ON notes(user_id, created);",
              [(NOTES_T, False, None, IDX_NOTES), (NOTES_B, True, "Порядок столбцов: сначала user_id, затем created", IDX_NOTES),
               (NOTES_T, True, None, "SELECT name, tbl_name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%' ORDER BY name;")],
              [("CREATE INDEX idx_notes_user_created ON notes(created, user_id);", "Порядок столбцов обратный: сначала нужен user_id."),
               ("CREATE INDEX idx_notes_user_created ON notes(user_id);", "В индексе нет столбца created."),
               ("CREATE INDEX idx_notes_user_created ON notes(created);", "Индекс только по дате: user_id пропущен."),
               ("CREATE INDEX idx_notes_user ON notes(user_id, created);", "Неверное имя индекса.")],
              hints("Составной индекс охватывает несколько столбцов: они перечисляются в скобках через запятую.", "Порядок важен: индекс сортируется сначала по первому столбцу, затем по второму.",
                    "Запросы начинаются с условия по user_id, поэтому он первый.", "Вторым идёт created: по нему сортируют внутри пользователя.",
                    "CREATE INDEX idx_notes_user_created ON notes(user_id, created);"),
              "Индекс по двум столбцам сортируется по первому, затем по второму. Запрос с условием по user_id и сортировкой по created читается подряд, без отдельной сортировки.",
              starter="-- Создайте составной индекс\n")

REDUND = NOTES_T + "CREATE INDEX idx_notes_user ON notes(user_id);\nCREATE INDEX idx_notes_user_created ON notes(user_id, created);\n"
a4 = sql_task("a4-drop", "write", "Лишний индекс",
              "У таблицы `notes` два индекса: `idx_notes_user` (по `user_id`) и `idx_notes_user_created` (по `user_id` и `created`). Первый дублирует левую часть второго и только замедляет запись. Удалите **лишний** индекс.",
              "Удалять ненужные индексы командой DROP INDEX.", "DROP INDEX idx_notes_user;",
              [(REDUND, False, None, LIST), (REDUND + "INSERT INTO notes (user_id, created, text) VALUES (1, '2026-01-01', 'a');", True, "Остаться должен составной индекс", LIST)],
              [("DROP INDEX idx_notes_user_created;", "Удалён составной индекс, а лишний — idx_notes_user."),
               ("DROP INDEX idx_notes_user;\nDROP INDEX idx_notes_user_created;", "Удалены оба индекса."),
               ("-- ничего не удалено\n", "Лишний индекс остался.")],
              hints("Индекс удаляет команда DROP INDEX.", "После неё пишут имя индекса.", "Составной индекс (user_id, created) покрывает запросы по user_id: он нужнее.", "Лишний тот, что включает только первый столбец составного.",
                    "DROP INDEX idx_notes_user;"),
              "Составной индекс (user_id, created) помогает и запросам только по user_id, поэтому отдельный индекс по user_id не нужен: он только занимает место и замедляет запись.",
              starter="-- Удалите лишний индекс\n")

CODE5 = ("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL);\nCREATE UNIQUE INDEX idx_users_email ON users(email);\n"
         "INSERT OR IGNORE INTO users (email, name) VALUES ('a@x.ru', 'Анна');\nINSERT OR IGNORE INTO users (email, name) VALUES ('a@x.ru', 'Другая Анна');\n"
         "INSERT OR IGNORE INTO users (email, name) VALUES ('b@x.ru', 'Борис');\nINSERT OR REPLACE INTO users (email, name) VALUES ('b@x.ru', 'Борис Второй');\n"
         "SELECT id, email, name FROM users ORDER BY id;\n")
a5 = sql_predict("a5-predict", "Повтор почты", CODE5,
                 [("1 | a@x.ru | Анна\n2 | b@x.ru | Борис Второй", "REPLACE удаляет старую строку и вставляет новую уже с новым номером."),
                  ("1 | a@x.ru | Анна\n2 | b@x.ru | Борис\n3 | b@x.ru | Борис Второй", "Уникальный индекс не допускает двух строк с одной почтой."),
                  ("1 | a@x.ru | Другая Анна\n3 | b@x.ru | Борис Второй", "OR IGNORE оставляет старую строку: вторая Анна не добавляется.")],
                 hints("Уникальный индекс не допускает двух строк с одной почтой.", "INSERT OR IGNORE при конфликте молча пропускает новую строку.",
                       "Значит, вторая Анна не добавлена: остаётся первая, номер 1. Борис получает номер 2.", "INSERT OR REPLACE при конфликте удаляет старую строку и вставляет новую.",
                       "Новая строка получает следующий свободный номер, а не номер удалённой: строка Бориса теперь с номером 3."),
                 "IGNORE пропускает новую строку, REPLACE удаляет старую и добавляет новую (с новым номером). В обоих случаях повторов почты не появляется: их запрещает уникальный индекс.")

skills = {"sql.index": "Индексы: создание и проверка", "sql.index-composite": "Составные и уникальные индексы", "sql.index-cost": "Цена индексов"}
write_lesson("sql-06-indexes", "SQL: индексы",
             "Создавать обычные, уникальные и составные индексы, проверять их работу и понимать, чем индексы обходятся.",
             list(skills), ["sql-05-design"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Индексы на все столбцы подряд", "fix": "Индекс замедляет запись и занимает место: создавайте только для частых условий, соединений и сортировок."},
              {"mistake": "Не тот порядок столбцов в составном индексе", "fix": "Первым ставят столбец, по которому всегда фильтруют (правило левого префикса)."},
              {"mistake": "Над столбцом вызывается функция или LIKE '%…'", "fix": "Индекс не используется: постройте индекс по выражению или измените условие."},
              {"mistake": "Индекс на столбце с двумя значениями", "fix": "Такой индекс почти не помогает: подходит половина таблицы."}],
             min_pass=3, pack="sql-basics", runner="sql")
merge_pack("sql-06-indexes", skills)

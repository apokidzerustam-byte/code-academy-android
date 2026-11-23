"""Урок SQL 4: изменение данных — INSERT, UPDATE, DELETE и ограничения."""
from sqlib import *

HEAD = """CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'doing', 'done')),
  priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5)
);

"""
SCHEMA = HEAD + """INSERT INTO tasks (title, status, priority) VALUES
  ('Купить молоко', 'todo', 2),
  ('Написать отчёт', 'doing', 1),
  ('Позвонить врачу', 'todo', 3),
  ('Оплатить интернет', 'done', 2);
"""
SETUP_B = HEAD + """INSERT INTO tasks (title, status, priority) VALUES
  ('Уборка', 'todo', 1), ('Почта', 'todo', 1), ('Спорт', 'doing', 4), ('Налоги', 'done', 5),
  ('Чтение', 'done', 1), ('Звонок', 'todo', 5), ('План', 'doing', 2);
"""
SETUP_C = HEAD + "INSERT INTO tasks (title, status, priority) VALUES ('Единственная', 'todo', 1), ('Готово', 'done', 3);\n"
SETUP_E = HEAD
SHOW = "SELECT id, title, status, priority FROM tasks ORDER BY id;"

INS = "INSERT INTO tasks (title, priority)\nVALUES ('Сдать книги', 1),\n       ('Починить кран', 4);\n"
UPD = "UPDATE tasks\nSET status = 'done'\nWHERE title = 'Купить молоко';\n"
UPD2 = "UPDATE tasks\nSET priority = priority - 1\nWHERE status = 'doing' AND priority > 1;\n"
DEL = "DELETE FROM tasks\nWHERE status = 'done';\n"
BAD = "INSERT INTO tasks (title, status)\nVALUES ('Тест', 'finished');\n"
err_text = sq_err(BAD, SCHEMA)
assert "CHECK" in err_text, err_text

use_file("schema.sql")
scenes = [
    scene("intro", "Три команды изменения", """
      Запросы SELECT только читают данные. Но таблица должна жить: появляются новые записи, старые меняются, ненужные
      исчезают. Для этого есть три команды. INSERT добавляет строки, UPDATE изменяет существующие, DELETE удаляет. Сегодня
      учимся ими пользоваться и узнаем, как база защищает таблицу от неверных данных.""",
          [NOTE("INSERT — добавить · UPDATE — изменить · DELETE — удалить", at="Для этого")]),
    scene("schema", "Таблица с правилами", """
      Возьмём список дел. У каждой задачи есть номер, название, статус и срочность. Посмотрите на правила, которые
      записаны в самой таблице. NOT NULL значит, что название обязательно. DEFAULT задаёт значение по умолчанию: если
      статус не указать, будет todo. А CHECK ограничивает допустимые значения: статус только из трёх слов, а срочность
      от одного до пяти.""",
          [T(SCHEMA, at="Возьмём список"), HL([3, 4, 5], at="NOT NULL", file="schema.sql")]),
    scene("insert", "INSERT: добавляем строки", """
      Добавим две задачи одной командой. После INSERT INTO пишем таблицу и в скобках столбцы, которые заполняем, а
      после VALUES — сами значения, по одной скобке на строку. Статус мы не указали, поэтому подставится значение по
      умолчанию. Номер выдаст сама база. Запускаем и смотрим таблицу: обе новые задачи со статусом todo.""",
          [CLEAR(file="main.sql"), T(INS + "\n" + SHOW + "\n", at="Добавим две", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(sq_out(INS + SHOW, SCHEMA), at="обе новые")]),
    scene("update", "UPDATE: меняем строки", """
      Теперь отметим покупку молока как выполненную. Команда UPDATE, имя таблицы, после SET — какие столбцы меняем, а после
      WHERE — какие строки. Значение можно вычислять из текущего: priority равно priority минус один делает задачу срочнее.
      Запускаем: молоко стало done.""",
          [CLEAR(file="main.sql"), T(UPD + "\n" + SHOW + "\n", at="Теперь отметим", file="main.sql"), HL([3], at="после WHERE", file="main.sql"),
           RUN(at="Запускаем", file="main.sql"), OUT(sq_out(UPD + SHOW, SCHEMA), at="молоко стало")]),
    scene("delete", "DELETE: удаляем строки", """
      Выполненные задачи можно удалить. Команда DELETE FROM, таблица и условие WHERE. Запускаем: задача про интернет
      исчезла. Важно: без WHERE удалятся все строки таблицы, а не только нужные. То же касается UPDATE: без условия он
      изменит всё. Поэтому перед такой командой полезно написать SELECT с тем же WHERE и убедиться, что выбрались именно
      нужные строки.""",
          [CLEAR(file="main.sql"), T(DEL + "\n" + SHOW + "\n", at="Выполненные задачи", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(sq_out(DEL + SHOW, SCHEMA), at="исчезла")]),
    scene("check", "Защита от неверных данных", """
      Попробуем добавить задачу со статусом finished, которого нет в списке. База откажет: проверка CHECK не
      пройдена. Таблица осталась целой. Это удобно: даже если в программе ошибка, неверные данные в таблицу не попадут.""",
          [CLEAR(file="main.sql"), T(BAD, at="Попробуем", file="main.sql"), RUN(at="База откажет", file="main.sql"),
           OUT(err_text.strip(), err=True, at="База откажет")]),
    scene("summary", "Итог", """
      Подведём итог. INSERT INTO добавляет строки, и пропущенные столбцы получают значения по умолчанию. UPDATE с SET и WHERE
      меняет нужные строки. DELETE с WHERE удаляет их. Ограничения NOT NULL, DEFAULT и CHECK защищают таблицу от неверных
      данных. И запомните правило: перед UPDATE и DELETE проверяйте WHERE запросом SELECT.""",
          [NOTE("Перед `UPDATE`/`DELETE` напишите `SELECT … WHERE …` — и убедитесь, что выбрались те строки.", at="запомните правило")]),
]
use_file(None)

notes = """
# SQL: изменение данных

```sql
INSERT INTO tasks (title, priority)
VALUES ('Сдать книги', 1), ('Починить кран', 4);   -- status возьмётся из DEFAULT

UPDATE tasks
SET priority = priority - 1
WHERE status = 'doing' AND priority > 1;

DELETE FROM tasks
WHERE status = 'done';
```

| Ограничение | Что значит |
|---|---|
| `NOT NULL` | значение обязательно |
| `DEFAULT x` | если не указано — подставить `x` |
| `CHECK (условие)` | значение должно удовлетворять условию |
| `PRIMARY KEY` | уникальный номер строки |

- Без `WHERE` команды `UPDATE` и `DELETE` затрагивают **все** строки.
- Перед изменением проверьте условие запросом `SELECT … WHERE …`.
- Нарушение ограничения — ошибка, и команда не выполняется.
- Несколько строк в одном `INSERT`: `VALUES (…), (…), (…)`.
"""

CASES_Q = SHOW
def cases(*extra):
    base = [(SCHEMA, False, None), (SETUP_B, True, "Данных может быть больше, и в них есть подходящие и неподходящие строки"), (SETUP_C, True, None)]
    return base + list(extra)

a1 = sql_task("a1-insert", "write", "Новая задача",
    "Добавьте в таблицу `tasks` одну задачу с названием `Сдать книги` и срочностью `1`. Статус указывать **не нужно** — пусть возьмётся значение по умолчанию.",
    "Добавлять строки командой INSERT.", "INSERT INTO tasks (title, priority)\nVALUES ('Сдать книги', 1);",
    cases((SETUP_E, True, "Работает и на пустой таблице")),
    [("INSERT INTO tasks (title, status, priority) VALUES ('Сдать книги', 'doing', 1);", "Статус указан вручную, а нужен по умолчанию."),
     ("INSERT INTO tasks (title) VALUES ('Сдать книги');", "Не указана срочность 1: подставилась тройка."),
     ("INSERT INTO tasks (title, priority) VALUES ('Сдать книги', 1), ('Сдать книги', 1);", "Добавлено две строки вместо одной."),
     ("UPDATE tasks SET title = 'Сдать книги', priority = 1;", "UPDATE меняет существующие строки, а новая не добавляется.")],
    hints("Новую строку добавляет команда INSERT.", "INSERT INTO таблица (столбцы) VALUES (значения).", "Укажите два столбца: title и priority.", "Текст в одинарных кавычках, число без кавычек.", "Статус не указывайте — подставится DEFAULT."),
    "Столбцы, которых нет в списке, получают значения по умолчанию, а номер выдаёт база.",
    query=SHOW, starter="-- Добавьте задачу\n")

a2 = sql_task("a2-update", "write", "Срочнее!",
    "Сделайте срочнее все задачи со статусом `todo`, у которых срочность больше 1: уменьшите `priority` на 1. Остальные строки не трогайте.",
    "Менять значения по условию.", "UPDATE tasks\nSET priority = priority - 1\nWHERE status = 'todo' AND priority > 1;",
    cases((SETUP_E, True, None)),
    [("UPDATE tasks SET priority = priority - 1 WHERE status = 'todo';", "Не проверена граница: у задач со срочностью 1 получится 0, а CHECK запрещает."),
     ("UPDATE tasks SET priority = priority - 1 WHERE priority > 1;", "Изменены задачи с любым статусом."),
     ("UPDATE tasks SET priority = priority + 1 WHERE status = 'todo' AND priority > 1;", "Срочность уменьшилась бы числом, а здесь она растёт."),
     ("UPDATE tasks SET priority = 1 WHERE status = 'todo' AND priority > 1;", "Всем присвоена единица вместо уменьшения на один.")],
    hints("Менять существующие строки умеет команда UPDATE.", "После SET — столбец и новое значение.", "Новое значение вычисляется из текущего: priority - 1.", "Строки отбирает WHERE: статус todo и срочность больше единицы.", "Два условия соединяются словом AND."),
    "Условие priority > 1 защищает от нарушения CHECK; а статус отбирает только нужные задачи.",
    query=SHOW, starter="-- Измените срочность\n")

a3 = sql_task("a3-delete", "write", "Уборка в списке",
    "Удалите из таблицы все задачи со статусом `done`. Остальные должны остаться.",
    "Удалять строки командой DELETE.", "DELETE FROM tasks\nWHERE status = 'done';",
    cases((SETUP_E, True, "Пустая таблица остаётся пустой")),
    [("DELETE FROM tasks;", "Нет WHERE: удалены все строки."),
     ("DELETE FROM tasks WHERE status = 'todo';", "Удалены не те задачи."),
     ("DELETE FROM tasks WHERE status = 'done' AND priority > 3;", "Удалены не все выполненные: лишнее условие."),
     ("UPDATE tasks SET status = 'todo' WHERE status = 'done';", "Задачи не удалены, а переведены в другой статус.")],
    hints("Удаляет строки команда DELETE.", "Синтаксис: DELETE FROM таблица WHERE условие.", "Какие строки удалять, определяет WHERE.", "Нужны только задачи со статусом done.", "Без WHERE удалятся все строки."),
    "DELETE FROM с WHERE удаляет только подходящие строки; без WHERE очистится вся таблица.",
    query=SHOW, starter="-- Удалите выполненные\n")

a4 = sql_task("a4-fix", "fix", "Ловушка с OR",
    "Нужно пометить как `done` все задачи со срочностью 1 или 2. Команда написана, но помечает **все** задачи подряд. Найдите ошибку в условии.",
    "Читать условие WHERE.", "UPDATE tasks\nSET status = 'done'\nWHERE priority IN (1, 2);",
    cases((SETUP_E, True, None)),
    [("UPDATE tasks SET status = 'done' WHERE priority = 1 OR 2;", "Ошибка осталась: «OR 2» всегда истинно."),
     ("UPDATE tasks SET status = 'done' WHERE priority = 1;", "Пропущены задачи со срочностью 2."),
     ("UPDATE tasks SET status = 'done' WHERE priority <= 3;", "Захвачены и задачи со срочностью 3.")],
    hints("Выполните SELECT с тем же условием: что выберется?", "Каждая часть условия через OR — самостоятельное условие.", "Просто «2» — не сравнение: для базы это всегда истина.", "Нужно сравнить priority со значением 2 или записать список значений.", "Для списка значений есть оператор IN (…)."),
    "Выражение priority = 1 OR 2 разбирается как (priority = 1) OR 2, а число 2 считается истиной. IN (1, 2) записывает то, что имелось в виду.",
    query=SHOW, starter="UPDATE tasks\nSET status = 'done'\nWHERE priority = 1 OR 2;\n")

CODE5 = (HEAD + "INSERT INTO tasks (title, status, priority) VALUES\n  ('А', 'todo', 2), ('Б', 'doing', 4), ('В', 'done', 1), ('Г', 'todo', 5);\n"
         "UPDATE tasks SET priority = priority - 1 WHERE status <> 'done';\n"
         "DELETE FROM tasks WHERE priority > 3;\n"
         "INSERT INTO tasks (title) VALUES ('Д');\n"
         "SELECT title, status, priority FROM tasks ORDER BY priority, title;\n")
a5 = sql_predict("a5-predict", "Что останется в таблице?", CODE5,
    [("В | done | 1\nА | todo | 1\nД | todo | 3\nБ | doing | 3", "Порядок строк неверный: сначала по срочности, затем по названию."),
     ("А | todo | 1\nВ | done | 1\nБ | doing | 3\nД | todo | 3\nГ | todo | 4", "Задача Г удалена: у неё срочность 4 после UPDATE.")],
    hints("Идём по командам сверху вниз, как их выполняет база.", "UPDATE уменьшает срочность у задач, которые не done: А — 1, Б — 3, Г — 4, а В не меняется.", "DELETE удаляет строки со срочностью больше трёх.", "INSERT добавляет задачу Д с значениями по умолчанию.", "Сортировка: сначала по срочности, внутри равной — по названию."),
    "Команды выполняются по порядку: каждая видит результат предыдущей.")

skills = {"sql.insert": "INSERT: добавление строк", "sql.delete": "DELETE и осторожность с WHERE", "sql.constraints": "Ограничения таблицы"}
write_lesson("sql-04-modify", "SQL: изменение данных",
             "Добавлять, изменять и удалять строки командами INSERT, UPDATE и DELETE и понимать ограничения таблицы.",
             list(skills), ["sql-03-joins"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "UPDATE или DELETE без WHERE", "fix": "Без условия затрагиваются все строки: сначала проверьте SELECT-ом.", "errorType": "SQLError"},
              {"mistake": "Условие «x = 1 OR 2»", "fix": "Пишите «x = 1 OR x = 2» или «x IN (1, 2)»."},
              {"mistake": "Забыли указать обязательный столбец (NOT NULL)", "fix": "INSERT вернёт ошибку: укажите значение или задайте DEFAULT."},
              {"mistake": "Значение нарушает CHECK", "fix": "Прочитайте сообщение об ошибке и сверьтесь с описанием таблицы."}],
             min_pass=3, pack="sql-basics", runner="sql")
merge_pack("sql-04-modify", skills)

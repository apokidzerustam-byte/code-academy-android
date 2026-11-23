"""Урок SQL 7: транзакции — атомарность, BEGIN/COMMIT/ROLLBACK, SAVEPOINT.
Результаты считает настоящий SQLite. Код приложения (Python, Room) показан справочно."""
from sqlib import *

ACC = """CREATE TABLE accounts (
  id INTEGER PRIMARY KEY,
  owner TEXT NOT NULL,
  balance INTEGER NOT NULL CHECK (balance >= 0)
);

INSERT INTO accounts (owner, balance) VALUES ('Анна', 500), ('Борис', 200);
"""
T_COMMIT = ("BEGIN;\nUPDATE accounts SET balance = balance - 100 WHERE id = 1;\nUPDATE accounts SET balance = balance + 100 WHERE id = 2;\nCOMMIT;\n\n"
            "SELECT owner, balance FROM accounts ORDER BY id;\n")
T_ROLLBACK = ("BEGIN;\nDELETE FROM accounts;\nSELECT COUNT(*) AS inside FROM accounts;\nROLLBACK;\nSELECT COUNT(*) AS after FROM accounts;\n")
LOG = "CREATE TABLE log (\n  id INTEGER PRIMARY KEY,\n  msg TEXT NOT NULL\n);\n"
T_SAVE = ("BEGIN;\nINSERT INTO log (msg) VALUES ('начало');\nSAVEPOINT step;\nINSERT INTO log (msg) VALUES ('эксперимент');\nROLLBACK TO step;\nCOMMIT;\n\n"
          "SELECT msg FROM log;\n")
PROD = "CREATE TABLE products (\n  id INTEGER PRIMARY KEY,\n  name TEXT NOT NULL,\n  stock INTEGER NOT NULL\n);\n\nINSERT INTO products (name, stock) VALUES ('Чай', 1);\n"
T_RACE = ("-- проверка и списание одной командой\nUPDATE products SET stock = stock - 1 WHERE id = 1 AND stock > 0;\nSELECT changes() AS sold;\n\n"
          "UPDATE products SET stock = stock - 1 WHERE id = 1 AND stock > 0;\nSELECT changes() AS sold;\n")
T_AUTO = ("-- без BEGIN каждая команда фиксируется сама:\nINSERT INTO log (msg) VALUES ('раз');\nINSERT INTO log (msg) VALUES ('два');\n\n"
          "-- с BEGIN — одна общая фиксация:\nBEGIN;\nINSERT INTO log (msg) VALUES ('три');\nINSERT INTO log (msg) VALUES ('четыре');\nCOMMIT;\n")
PY = ('import sqlite3\n\nconn = sqlite3.connect("bank.db")\ntry:\n    with conn:   # BEGIN … COMMIT, а при ошибке — ROLLBACK\n'
      '        conn.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")\n        conn.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")\n'
      'except sqlite3.Error:\n    print("Перевод не выполнен")\n')
CHK_ERR = "UPDATE accounts SET balance = balance - 1000 WHERE id = 1;\n"
err_text = sq_err(CHK_ERR, ACC)
assert "CHECK constraint failed" in err_text, err_text

use_file("schema.sql")
scenes = [
    scene("intro", "Всё или ничего", """
      Представьте перевод денег. С карты Анны нужно списать сто рублей и зачислить их Борису. В базе это две команды. А теперь представьте,
      что после первой электричество выключилось. Деньги у Анны списаны, а Борис их не получил: сто рублей исчезли. Чтобы такого не
      случалось, несколько команд объединяют в транзакцию. Транзакция, это группа операций, которая выполняется целиком или не
      выполняется совсем. Либо обе команды применились, либо база осталась ровно такой, какой была. Третьего не дано. Без транзакции
      каждая команда применяется сразу и сама по себе. С транзакцией мы сами решаем, где начало и где конец группы.""",
          [NOTE("Без транзакции: списали — и свет погас → деньги потеряны", at="Деньги у Анны"),
           NOTE("**Транзакция** — группа операций «всё или ничего»", at="Транзакция, это")]),
    scene("commit", "BEGIN и COMMIT", """
      Транзакция открывается командой BEGIN, а завершается командой COMMIT, что значит «зафиксировать». Всё, что между ними, применяется
      как единое целое. Вот перевод. Сначала BEGIN. Дальше списываем сто с первого счёта и зачисляем сто на второй. В конце COMMIT.
      Запустим и посмотрим на остатки: у Анны четыреста, у Бориса триста. Сумма на двоих не изменилась: так и должно быть при переводе.""",
          [CLEAR(file="schema.sql"), T(ACC, at="Транзакция открывается", file="schema.sql"), CLEAR(file="main.sql"), T(T_COMMIT, at="Вот перевод", file="main.sql"),
           HL([1], at="Сначала BEGIN", file="main.sql"), HL([2, 3], at="Дальше списываем", file="main.sql"), HL([4], at="В конце COMMIT", file="main.sql"),
           RUN(at="Запустим", file="main.sql"), OUT(sq_out(T_COMMIT, ACC), at="Запустим")]),
    scene("rollback", "ROLLBACK: отмена", """
      Если что-то пошло не так, транзакцию отменяют командой ROLLBACK. Все изменения с момента BEGIN откатываются, и база возвращается в
      прежнее состояние. Проверим на опасном примере: внутри транзакции удаляем все счета. Сразу после этого внутри транзакции считаем
      строки: ноль, всё удалено. Потом отменяем. И снова считаем: счета на месте. До COMMIT изменения видны только вам, и пока вы не
      зафиксировали их, их можно просто выбросить.""",
          [CLEAR(file="main.sql"), T(T_ROLLBACK, at="Если что-то", file="main.sql"), HL([2], at="внутри транзакции удаляем", file="main.sql"),
           HL([3], at="Сразу после этого", file="main.sql"), HL([4], at="Потом отменяем", file="main.sql"), RUN(at="И снова считаем", file="main.sql"),
           OUT(sq_out(T_ROLLBACK, ACC), at="И снова считаем")]),
    scene("error", "Когда транзакция спасает", """
      Главная польза транзакции проявляется при ошибке. В нашей таблице есть правило: баланс не может быть отрицательным. Попробуем
      списать с Анны тысячу рублей, хотя у неё пятьсот. База откажет и назовёт нарушенное ограничение. Если бы это была первая команда
      перевода, то вторая, зачисление Борису, уже не должна выполниться, а всё сделанное нужно откатить. Приложение ловит ошибку и
      отправляет ROLLBACK. Поэтому правило такое: после ошибки внутри транзакции её либо откатывают целиком, либо точно знают, что делают.""",
          [CLEAR(file="main.sql"), T(CHK_ERR, at="Попробуем", file="main.sql"), RUN(at="База откажет", file="main.sql"), OUT(err_text.strip(), err=True, at="База откажет")]),
    scene("savepoint", "SAVEPOINT: частичная отмена", """
      Иногда откатить нужно только часть. Для этого есть точки сохранения. Команда SAVEPOINT ставит метку с именем, а ROLLBACK TO
      возвращает состояние к этой метке, не отменяя всё остальное. В примере мы добавляем запись «начало», ставим метку step, добавляем
      запись «эксперимент» и откатываемся к метке. Затем фиксируем. В журнале осталась только запись «начало».""",
          [CLEAR(file="schema.sql"), T(LOG, at="Иногда откатить", file="schema.sql"), CLEAR(file="main.sql"), T(T_SAVE, at="Иногда откатить", file="main.sql"),
           HL([3], at="Команда SAVEPOINT", file="main.sql"), HL([5], at="ROLLBACK TO", file="main.sql"), HL([6], at="Затем фиксируем", file="main.sql"),
           RUN(at="В журнале", file="main.sql"), OUT(sq_out(T_SAVE, LOG), at="В журнале")]),
    scene("auto", "Автоматическая фиксация", """
      Что происходит, если мы вообще не пишем BEGIN? Тогда каждая команда сама становится маленькой транзакцией и фиксируется сразу. Это называется
      автоматической фиксацией. Команда BEGIN переключает базу в ручной режим: фиксация откладывается до COMMIT. Есть у этого и приятный
      побочный эффект. Фиксация, это запись на диск, и она дорогая. Если добавлять тысячу строк по одной, база будет фиксировать тысячу
      раз. Если обернуть вставки в одну транзакцию, фиксация случится один раз, и вставка станет заметно быстрее. Поэтому массовую загрузку
      данных почти всегда делают внутри транзакции.""",
          [CLEAR(file="schema.sql"), T(LOG, at="Что происходит", file="schema.sql"), CLEAR(file="main.sql"), T(T_AUTO, at="Что происходит", file="main.sql"),
           HL([2, 3], at="Тогда каждая", file="main.sql"), HL([6, 9], at="Команда BEGIN", file="main.sql"), NOTE("Массовая вставка в одной транзакции быстрее: диск записывается один раз", at="Если обернуть")]),
    scene("race", "Гонка: прочитал, изменил, записал", """
      Одна из самых коварных ошибок называется гонкой. Двое покупателей одновременно берут последний пакет чая. Приложение читает остаток: один.
      Первый покупатель проверяет, что остаток положителен, и собирается записать ноль. Второй уже тоже прочитал единицу и тоже собирается
      записать ноль. В итоге чай продан дважды, хотя на складе он был один. Лекарство: не читать и писать отдельными шагами, а поручить
      проверку и изменение одной команде. Условие stock больше нуля вместе с UPDATE выполняется как единое целое. Функция changes сообщает,
      сколько строк команда изменила: единица значит, что покупка удалась, ноль значит, что товар уже закончился. Запустим: первая
      покупка успешна, вторая получает ноль.""",
          [CLEAR(file="schema.sql"), T(PROD, at="Одна из самых", file="schema.sql"), CLEAR(file="main.sql"), T(T_RACE, at="Лекарство", file="main.sql"),
           HL([2], at="Условие stock", file="main.sql"), HL([3], at="Функция changes", file="main.sql"), RUN(at="Запустим", file="main.sql"), OUT(sq_out(T_RACE, PROD), at="Запустим")]),
    scene("acid", "Четыре гарантии", """
      За транзакциями стоят четыре гарантии, их обозначают словом ACID. Первая, атомарность: всё или ничего, о чём мы и говорили.
      Вторая, согласованность: после транзакции все правила таблиц, ограничения и внешние ключи, соблюдены. Третья, изолированность:
      параллельные транзакции не видят чужих незавершённых изменений. Четвёртая, долговечность: после COMMIT данные сохранены, даже если
      сразу отключится питание. Эти четыре свойства и делают базу данных надёжным хранилищем, а не просто файлом. SQLite выполняет их при каждом COMMIT, поэтому
      телефон, который разрядился посреди записи, не оставит базу в полусломанном состоянии: при следующем запуске она либо увидит
      транзакцию целиком, либо откатит её.""",
          [NOTE("**A**tomicity — всё или ничего · **C**onsistency — правила соблюдены", at="Первая, атомарность"),
           NOTE("**I**solation — чужие незавершённые изменения не видны · **D**urability — после COMMIT данные не пропадут", at="Третья, изолированность")]),
    scene("app", "Транзакции в коде приложения", """
      В приложении транзакции чаще всего открывают не руками, а средствами библиотеки. В Питоне у соединения есть менеджер контекста: блок
      with сам делает COMMIT при успехе и ROLLBACK при исключении. В Андроиде в библиотеке Room для этого служит аннотация Transaction над
      функцией. Но есть правила на любом языке. Держите транзакцию короткой: пока она открыта, другие записи ждут. Не спрашивайте
      пользователя и не обращайтесь к сети внутри транзакции: вы не знаете, сколько это продлится. И всегда завершайте её, иначе база
      останется заблокированной. Учтите и особенность SQLite: писать в неё одновременно может только один участник, остальные ждут своей очереди.
      Для приложения на телефоне этого достаточно, но именно поэтому короткие транзакции так важны.""",
          [CLEAR(file="app.py"), T(PY, at="В приложении", file="app.py"), HL([5], at="блок with", file="app.py"), HL([8, 9], at="Но есть правила", file="app.py")]),
    scene("summary", "Итог", """
      Подведём итог. Транзакция объединяет несколько команд в одно целое. BEGIN открывает её, COMMIT фиксирует, ROLLBACK отменяет, а
      SAVEPOINT позволяет откатить часть. Транзакции нужны везде, где несколько изменений должны быть согласованы: переводы, заказы с
      позициями, перенос данных. Держите их короткими и всегда завершайте. В заданиях вы напишете перевод, отмену, частичный откат и
      добавление заказа с позициями, а также предскажете итог. Критерий прохождения: решить не меньше трёх заданий из пяти.""",
          [NOTE("`BEGIN` · `COMMIT` · `ROLLBACK` · `SAVEPOINT имя` / `ROLLBACK TO имя`", at="Подведём итог")]),
]
use_file(None)

notes = """
# SQL: транзакции

**Транзакция** — группа операций, которая выполняется целиком или не выполняется совсем.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;      -- зафиксировать
-- ROLLBACK; -- или отменить всё с момента BEGIN

SAVEPOINT step;        -- метка
ROLLBACK TO step;      -- откат только до метки
```

| Свойство ACID | Смысл |
|---|---|
| Atomicity | всё или ничего |
| Consistency | после транзакции все правила таблиц соблюдены |
| Isolation | параллельные транзакции не видят чужих незавершённых изменений |
| Durability | после COMMIT данные не пропадут даже при сбое питания |

В приложении:

```py
with conn:      # COMMIT при успехе, ROLLBACK при исключении
    conn.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    conn.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
```

В Room для той же цели служит аннотация `@Transaction` над функцией Dao.

- Держите транзакции короткими: открытая запись блокирует другие.
- Не ждите ввода пользователя и не обращайтесь к сети внутри транзакции.
- Всегда завершайте транзакцию — `COMMIT` или `ROLLBACK`.
- Ошибка внутри транзакции: либо откатить всё, либо точно знать, что делаешь.
- `last_insert_rowid()` возвращает номер последней вставленной строки — удобно, когда в транзакции добавляют заказ и его позиции.
"""

BAL = "SELECT id, balance FROM accounts ORDER BY id;"
ACC_B = ACC.split("INSERT INTO")[0] + "INSERT INTO accounts (owner, balance) VALUES ('Вера', 900), ('Глеб', 10), ('Дина', 0);\n"
a1 = sql_task("a1-transfer", "write", "Перевод между счетами",
              "Переведите **150** со счёта с `id = 1` на счёт с `id = 2` одной транзакцией: откройте её, спишите и зачислите, зафиксируйте.",
              "Объединить две операции в транзакцию.",
              "BEGIN;\nUPDATE accounts SET balance = balance - 150 WHERE id = 1;\nUPDATE accounts SET balance = balance + 150 WHERE id = 2;\nCOMMIT;",
              [(ACC, False, None, BAL), (ACC_B, True, "Меняются именно счета 1 и 2", BAL)],
              [("BEGIN;\nUPDATE accounts SET balance = balance - 150 WHERE id = 1;\nCOMMIT;", "Деньги списаны, но не зачислены."),
               ("BEGIN;\nUPDATE accounts SET balance = balance + 150 WHERE id = 2;\nCOMMIT;", "Деньги зачислены, но не списаны."),
               ("BEGIN;\nUPDATE accounts SET balance = balance - 150 WHERE id = 2;\nUPDATE accounts SET balance = balance + 150 WHERE id = 1;\nCOMMIT;", "Направление перевода перепутано."),
               ("BEGIN;\nUPDATE accounts SET balance = balance - 100 WHERE id = 1;\nUPDATE accounts SET balance = balance + 100 WHERE id = 2;\nCOMMIT;", "Сумма перевода должна быть 150.")],
              hints("Транзакция начинается командой BEGIN и заканчивается COMMIT.", "Внутри две команды UPDATE: одна уменьшает баланс, другая увеличивает.",
                    "Списать нужно со счёта 1, зачислить — на счёт 2.", "Сумма в обеих командах одна и та же: 150.",
                    "BEGIN; UPDATE … SET balance = balance - 150 WHERE id = 1; UPDATE … SET balance = balance + 150 WHERE id = 2; COMMIT;"),
              "Две команды UPDATE между BEGIN и COMMIT применяются как единое целое: деньги не могут пропасть.",
              starter="-- Напишите транзакцию перевода\n")

ORD = ("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT NOT NULL);\nINSERT INTO orders (customer) VALUES ('А'), ('Б'), ('В');\n")
ORD_B = ("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT NOT NULL);\n")
CNT = "SELECT COUNT(*) FROM orders;"
a2 = sql_task("a2-rollback", "complete", "Отменить удаление",
              "Сотрудник начал транзакцию и выполнил `DELETE FROM orders;`, но удалять заказы было нельзя. "
              "Допишите скрипт: **отмените** транзакцию, а затем добавьте заказ клиента «Г» (таблица `orders`, поле `customer`). "
              "В итоге должны остаться прежние заказы и появиться новый.",
              "Отменять транзакцию командой ROLLBACK и продолжать работу после неё.",
              "BEGIN;\nDELETE FROM orders;\nROLLBACK;\nINSERT INTO orders (customer) VALUES ('Г');",
              [(ORD, False, None, CNT),
               (ORD, True, "Прежние заказы должны остаться, новый — добавиться", "SELECT id, customer FROM orders ORDER BY id;"),
               (ORD_B, True, None, CNT)],
              [("BEGIN;\nDELETE FROM orders;\nCOMMIT;\nINSERT INTO orders (customer) VALUES ('Г');", "COMMIT фиксирует удаление, а нужно отменить."),
               ("BEGIN;\nDELETE FROM orders;\nINSERT INTO orders (customer) VALUES ('Г');", "Транзакция осталась открытой: удаление не отменено."),
               ("BEGIN;\nDELETE FROM orders;\nROLLBACK;", "Заказ «Г» не добавлен.")],
              hints("Транзакция уже открыта и содержит опасное удаление.", "Сначала завершите транзакцию так, чтобы удаление не сохранилось.",
                    "COMMIT фиксирует изменения, а нужна обратная команда.", "Команда отката — «откат назад» по-английски (roll back), слитно, одно слово.",
                    "ROLLBACK; а следом обычный INSERT INTO orders (customer) VALUES ('Г'); — после отката транзакции уже нет."),
              "ROLLBACK откатывает все изменения с момента BEGIN: заказы возвращаются в прежнее состояние. После отката транзакции нет, и следующая команда выполняется как обычно.",
              starter="BEGIN;\nDELETE FROM orders;\n-- отмените удаление и добавьте заказ «Г»\n")

LOGT = LOG + "INSERT INTO log (msg) VALUES ('старое');\n"
a3 = sql_task("a3-savepoint", "complete", "Частичный откат",
              "В транзакции уже добавлена запись «начало» и поставлена метка `sp`, после которой добавлена запись «эксперимент». Откатите **только эксперимент** (к метке `sp`) и зафиксируйте остальное.",
              "Использовать SAVEPOINT и ROLLBACK TO.", "BEGIN;\nINSERT INTO log (msg) VALUES ('начало');\nSAVEPOINT sp;\nINSERT INTO log (msg) VALUES ('эксперимент');\nROLLBACK TO sp;\nCOMMIT;",
              [(LOG, False, None, "SELECT msg FROM log ORDER BY id;"), (LOGT, True, "Раньше сделанное тоже остаётся", "SELECT msg FROM log ORDER BY id;")],
              [("BEGIN;\nINSERT INTO log (msg) VALUES ('начало');\nSAVEPOINT sp;\nINSERT INTO log (msg) VALUES ('эксперимент');\nCOMMIT;", "Эксперимент не откатан."),
               ("BEGIN;\nINSERT INTO log (msg) VALUES ('начало');\nSAVEPOINT sp;\nINSERT INTO log (msg) VALUES ('эксперимент');\nROLLBACK;", "ROLLBACK отменяет всё, включая «начало»: нужен откат к метке.")],
              hints("Метка sp уже поставлена: запись «эксперимент» добавлена после неё.", "Откат только до метки — это ROLLBACK TO, а не простой ROLLBACK.", "После отката к метке транзакция остаётся открытой.",
                    "Потом её нужно зафиксировать.", "ROLLBACK TO sp; затем COMMIT;"),
              "ROLLBACK TO sp отменяет только то, что сделано после метки; транзакция остаётся открытой, и COMMIT фиксирует оставшееся.",
              starter="BEGIN;\nINSERT INTO log (msg) VALUES ('начало');\nSAVEPOINT sp;\nINSERT INTO log (msg) VALUES ('эксперимент');\n-- откатите эксперимент и завершите транзакцию\n")

SHOP = ("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT NOT NULL);\n"
        "CREATE TABLE order_items (id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id), product TEXT NOT NULL, qty INTEGER NOT NULL);\n")
SHOP_B = SHOP + "INSERT INTO orders (customer) VALUES ('Старый'), ('Ещё один');\nINSERT INTO order_items (order_id, product, qty) VALUES (1, 'Хлеб', 1), (2, 'Сыр', 3);\n"
SHOWQ = "SELECT o.id, o.customer, i.product, i.qty FROM orders o JOIN order_items i ON i.order_id = o.id ORDER BY o.id, i.id;"
a4 = sql_task("a4-order", "write", "Заказ с позицией",
              "Добавьте одной транзакцией заказ клиента «Анна» и его позицию: товар «Чай», количество 2. Номер заказа в позиции возьмите функцией `last_insert_rowid()`, а не записывайте числом.",
              "Связать вставки в транзакции через last_insert_rowid().",
              "BEGIN;\nINSERT INTO orders (customer) VALUES ('Анна');\nINSERT INTO order_items (order_id, product, qty) VALUES (last_insert_rowid(), 'Чай', 2);\nCOMMIT;",
              [(SHOP, False, None, SHOWQ), (SHOP_B, True, "В таблицах уже есть заказы: номер нового заказа не равен 1", SHOWQ)],
              [("BEGIN;\nINSERT INTO orders (customer) VALUES ('Анна');\nINSERT INTO order_items (order_id, product, qty) VALUES (1, 'Чай', 2);\nCOMMIT;", "Номер заказа записан числом: при других данных позиция попадёт к чужому заказу."),
               ("BEGIN;\nINSERT INTO orders (customer) VALUES ('Анна');\nCOMMIT;", "Нет позиции заказа."),
               ("BEGIN;\nINSERT INTO orders (customer) VALUES ('Анна');\nINSERT INTO order_items (order_id, product, qty) VALUES (last_insert_rowid(), 'Чай', 1);\nCOMMIT;", "Количество должно быть 2.")],
              hints("Сначала добавляется заказ, затем его позиция: всё между BEGIN и COMMIT.", "Номер только что добавленной строки возвращает функция last_insert_rowid().",
                    "Подставьте её вместо номера заказа в INSERT позиции.", "Позиция: product — «Чай», qty — 2.",
                    "INSERT INTO order_items (order_id, product, qty) VALUES (last_insert_rowid(), 'Чай', 2);"),
              "last_insert_rowid() возвращает номер последней вставленной строки, поэтому позиция всегда привязывается к только что созданному заказу, какой бы номер он ни получил.",
              starter="-- Напишите транзакцию\n")

CODE5 = ("CREATE TABLE acc (id INTEGER PRIMARY KEY, balance INTEGER NOT NULL);\nINSERT INTO acc VALUES (1, 100), (2, 50);\nBEGIN;\nUPDATE acc SET balance = balance - 30 WHERE id = 1;\n"
         "SAVEPOINT s1;\nUPDATE acc SET balance = balance + 30 WHERE id = 2;\nUPDATE acc SET balance = 0 WHERE id = 1;\nROLLBACK TO s1;\nUPDATE acc SET balance = balance + 10 WHERE id = 2;\nCOMMIT;\n"
         "SELECT id, balance FROM acc ORDER BY id;\n")
a5 = sql_predict("a5-predict", "Откат к метке", CODE5,
                 [("1 | 100\n2 | 50", "Основная транзакция зафиксирована (COMMIT): изменения после BEGIN сохраняются, кроме отката до метки."),
                  ("1 | 0\n2 | 80", "Откат к метке s1 отменил обе команды после неё."),
                  ("1 | 70\n2 | 80", "Зачисление 30 стояло после метки и откатилось.")],
                 hints("Пройдите по шагам: сначала у первого счёта 70.", "Метка s1 ставится после списания: к ней можно вернуться.",
                       "Всё между меткой и ROLLBACK TO отменяется: зачисление 30 и обнуление.", "После отката первый счёт 70, второй 50.",
                       "Потом второму добавляют 10 и фиксируют: получается 60."),
                 "ROLLBACK TO s1 отменяет только действия после метки: списание 30 с первого счёта остаётся, зачисление 30 и обнуление откатываются; затем второй счёт получает 10, и COMMIT фиксирует итог.")

skills = {"sql.transaction": "Транзакции: BEGIN, COMMIT, ROLLBACK", "sql.savepoint": "SAVEPOINT и частичный откат", "sql.acid": "Гарантии ACID"}
write_lesson("sql-07-transactions", "SQL: транзакции",
             "Объединять операции в транзакции, откатывать их целиком или частично и понимать гарантии ACID.",
             list(skills), ["sql-06-indexes"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Перевод без транзакции", "fix": "Объедините списание и зачисление в BEGIN … COMMIT."},
              {"mistake": "Транзакция осталась открытой", "fix": "Всегда завершайте её: COMMIT или ROLLBACK, иначе база блокируется."},
              {"mistake": "Номер связанной строки записан числом", "fix": "Берите номер из last_insert_rowid() или из результата вставки."},
              {"mistake": "Долгая транзакция с ожиданием ввода или сети", "fix": "Держите транзакции короткими: открытая запись блокирует других."}],
             min_pass=3, pack="sql-basics", runner="sql")
merge_pack("sql-07-transactions", skills)

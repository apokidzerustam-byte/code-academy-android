"""Урок SQL 2: агрегаты и группировка."""
from sqlib import *

SCHEMA = """CREATE TABLE sales (
  id INTEGER PRIMARY KEY,
  product TEXT NOT NULL,
  category TEXT NOT NULL,
  price REAL NOT NULL,
  qty INTEGER NOT NULL
);

INSERT INTO sales (product, category, price, qty) VALUES
  ('Хлеб', 'еда', 3.5, 10),
  ('Молоко', 'еда', 4.0, 5),
  ('Ручка', 'канцелярия', 2.0, 20),
  ('Тетрадь', 'канцелярия', 1.5, 30),
  ('Наушники', 'техника', 120.0, 2);
"""
HEAD = SCHEMA.split("\n\n")[0] + "\n"
SETUP_B = HEAD + """INSERT INTO sales (product, category, price, qty) VALUES
  ('Чай', 'еда', 1.0, 12), ('Кофе', 'еда', 2.0, 4), ('Сахар', 'еда', 2.0, 6),
  ('Диск', 'техника', 10.0, 1), ('Кабель', 'техника', 5.0, 6),
  ('Скрепки', 'канцелярия', 0.5, 20);
"""
SETUP_C = HEAD + """INSERT INTO sales (product, category, price, qty) VALUES
  ('Мышь', 'техника', 15.0, 2), ('Клавиатура', 'техника', 25.0, 1);
"""
SETUP_E = HEAD

Q_COUNT = "SELECT COUNT(*) FROM sales;\n"
Q_SUM = "SELECT SUM(price * qty) AS revenue,\n       MIN(price) AS cheapest,\n       MAX(price) AS dearest\nFROM sales;\n"
Q_GROUP = "SELECT category, COUNT(*) AS n\nFROM sales\nGROUP BY category;\n"
Q_HAVING = "SELECT category, SUM(qty) AS total\nFROM sales\nGROUP BY category\nHAVING SUM(qty) >= 20;\n"
Q_AVG = "SELECT category, ROUND(AVG(price), 2) AS avg_price\nFROM sales\nGROUP BY category\nORDER BY avg_price DESC;\n"
ERR = "SELECT category, price FROM sales\nWHERE COUNT(*) > 1;\n"
err_text = sq_err(ERR, SCHEMA)
assert "COUNT" in err_text or "агрегат" in err_text, err_text

use_file("schema.sql")
scenes = [
    scene("intro", "Один ответ на много строк", """
      До сих пор запрос возвращал строки таблицы. Но часто нужен один итог: сколько всего товаров, какова сумма
      выручки, какая самая высокая цена. Для этого в SQL есть агрегатные функции: они берут много строк и
      сворачивают их в одно значение. Сегодня работаем с таблицей продаж: товар, категория, цена и количество.""",
          [NOTE("**Агрегат** — функция, которая сворачивает много строк в одно значение: COUNT, SUM, AVG, MIN, MAX.", at="Для этого")]),
    scene("data", "Таблица продаж", """
      Вот таблица sales. В ней пять строк: хлеб и молоко в категории еда, ручка и тетрадь в канцелярии и наушники в технике.
      У каждой строки есть цена за штуку и количество проданных штук.""",
          [T(SCHEMA, at="Вот таблица")]),
    scene("count", "COUNT, SUM, MIN, MAX", """
      Функция COUNT со звёздочкой считает строки. Запускаем: пять. Функция SUM складывает значения столбца, а внутри можно
      написать выражение: цена умножить на количество — это выручка по каждой строке, и SUM их сложит. MIN и MAX находят
      наименьшее и наибольшее. Каждому результату можно дать имя словом AS: оно появится в заголовке столбца.""",
          [CLEAR(file="main.sql"), T(Q_COUNT, at="Функция COUNT", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(sq_out(Q_COUNT, SCHEMA), at="пять"),
           CLEAR(file="main.sql"), T(Q_SUM, at="Функция SUM", file="main.sql"), RUN(at="Каждому результату", file="main.sql"),
           OUT(sq_out(Q_SUM, SCHEMA), at="Каждому результату")]),
    scene("group", "GROUP BY: итоги по группам", """
      Чаще нужен итог не по всей таблице, а по группам: сколько товаров в каждой категории. Для этого после FROM
      добавляем GROUP BY и имя столбца. База делит строки на группы с одинаковым значением и считает функцию для
      каждой группы отдельно. Запускаем: еда — два товара, канцелярия — два, техника — один. В списке выбираемых столбцов
      можно оставлять только то, по чему группируем, и агрегаты.""",
          [CLEAR(file="main.sql"), T(Q_GROUP, at="Для этого после", file="main.sql"), HL([3], at="Для этого после", file="main.sql"),
           RUN(at="Запускаем", file="main.sql"), OUT(sq_out(Q_GROUP, SCHEMA), at="еда")]),
    scene("having", "HAVING: условие на группы", """
      А как оставить только группы, где продано не меньше двадцати штук? WHERE тут не подойдёт: он работает до группировки,
      и агрегатов в нём писать нельзя. Для условий на результат группировки есть слово HAVING. Оно пишется после
      GROUP BY. Запускаем: остались только канцелярия, где пятьдесят штук, и больше ничего: в еде пятнадцать, в технике две.""",
          [CLEAR(file="main.sql"), T(Q_HAVING, at="Для условий", file="main.sql"), HL([4], at="Оно пишется", file="main.sql"),
           RUN(at="Запускаем", file="main.sql"), OUT(sq_out(Q_HAVING, SCHEMA), at="остались")]),
    scene("avg", "Среднее и округление", """
      Среднее значение даёт функция AVG, а ROUND округляет число до нужного количества знаков. Посчитаем среднюю цену
      по каждой категории и отсортируем по убыванию. Сортировать можно по имени, которое мы дали результату.
      Запускаем: самые дорогие товары в технике, самые дешёвые — в канцелярии.""",
          [CLEAR(file="main.sql"), T(Q_AVG, at="Посчитаем", file="main.sql"), RUN(at="Запускаем", file="main.sql"),
           OUT(sq_out(Q_AVG, SCHEMA), at="самые дорогие")]),
    scene("error", "Частая ошибка: агрегат в WHERE", """
      Если попытаться использовать агрегат в условии WHERE, база откажет: функции для групп нельзя применять к отдельным
      строкам. Запустим такой запрос и прочитаем сообщение. Решение простое: условие на агрегат переносим в HAVING.""",
          [CLEAR(file="main.sql"), T(ERR, at="Если попытаться", file="main.sql"), RUN(at="Запустим", file="main.sql"),
           OUT(err_text.strip(), err=True, at="Запустим")]),
    scene("summary", "Итог", """
      Подведём итог. COUNT, SUM, AVG, MIN и MAX сворачивают строки в одно значение. GROUP BY делит строки на группы, и функции
      считаются для каждой группы. WHERE фильтрует строки до группировки, HAVING — группы после неё. Результатам можно
      давать имена через AS и округлять их функцией ROUND.""",
          [NOTE("`SELECT … FROM … WHERE … GROUP BY … HAVING … ORDER BY … LIMIT …`", at="Подведём итог")]),
]
use_file(None)

notes = """
# SQL: агрегаты и группировка

```sql
SELECT COUNT(*) FROM sales;                         -- сколько строк
SELECT SUM(price * qty) AS revenue FROM sales;      -- выручка
SELECT MIN(price), MAX(price) FROM sales;           -- наименьшая и наибольшая цена

SELECT category, COUNT(*) AS n
FROM sales
GROUP BY category;                                  -- итоги по группам

SELECT category, SUM(qty) AS total
FROM sales
GROUP BY category
HAVING SUM(qty) >= 20;                              -- условие на группы

SELECT category, ROUND(AVG(price), 2) AS avg_price
FROM sales
GROUP BY category
ORDER BY avg_price DESC;
```

| Функция | Что делает |
|---|---|
| `COUNT(*)` | число строк |
| `SUM(x)` | сумма |
| `AVG(x)` | среднее |
| `MIN(x)`, `MAX(x)` | наименьшее и наибольшее |

- `WHERE` — условие на **строки** (до группировки), `HAVING` — на **группы** (после).
- В `SELECT` при группировке — только столбцы из `GROUP BY` и агрегаты.
- Агрегат в `WHERE` — ошибка «misuse of aggregate».
"""

ALL = [(SCHEMA, False, None), (SETUP_B, True, "Запрос должен работать на любых данных, а не только на примере"), (SETUP_C, True, None)]

a1 = sql_task("a1-revenue", "write", "Общая выручка",
    "В таблице `sales` есть столбцы `id`, `product`, `category`, `price`, `qty`.\n\nНапишите запрос, который возвращает **одно число**: общую выручку — сумму `price * qty` по всем строкам.",
    "Применять SUM к выражению.", "SELECT SUM(price * qty) AS revenue FROM sales;",
    [(SCHEMA, False, None), (SETUP_B, True, "Выручка считается по всем строкам"), (SETUP_C, True, None)],
    [("SELECT SUM(price) FROM sales;", "Не учтено количество."), ("SELECT SUM(qty) FROM sales;", "Суммируется количество, а не выручка."),
     ("SELECT price * qty FROM sales;", "Возвращает выручку по каждой строке, а не итог."), ("SELECT COUNT(*) FROM sales;", "Считается число строк.")],
    hints("Нужен один итог по всей таблице — это агрегат.", "Суммирует значения функция SUM.", "Выручка строки — цена, умноженная на количество.", "Выражение можно писать прямо в скобках функции.", "SELECT SUM(price * qty) FROM sales;"),
    "SUM(price * qty) сначала считает выручку каждой строки, а затем складывает результаты.", starter="-- Ваш запрос\n")

a2 = sql_task("a2-per-category", "write", "Товаров в категориях",
    "Выведите для каждой категории её название и **число строк** (товаров) в ней: столбцы `category` и `n`. Порядок — по названию категории по алфавиту.",
    "Группировать строки: GROUP BY.", "SELECT category, COUNT(*) AS n\nFROM sales\nGROUP BY category\nORDER BY category;",
    [(SCHEMA, False, None), (SETUP_B, True, "Категорий может быть больше или меньше"), (SETUP_C, True, "Если в категории одна строка, всё равно нужна строка с единицей")],
    [("SELECT category, COUNT(*) AS n FROM sales ORDER BY category;", "Нет группировки: одна строка на всю таблицу."),
     ("SELECT category, COUNT(*) AS n FROM sales GROUP BY product ORDER BY category;", "Группировка по товару вместо категории."),
     ("SELECT category, SUM(qty) AS n FROM sales GROUP BY category ORDER BY category;", "Суммируется количество, а нужно число строк."),
     ("SELECT category, COUNT(*) AS n FROM sales GROUP BY category ORDER BY n DESC;", "Порядок по числу, а не по названию.")],
    hints("Нужен итог по каждой категории — это группировка.", "После FROM пишут GROUP BY category.", "Число строк в группе считает COUNT(*).", "Порядок — ORDER BY category в самом конце.", "SELECT category, COUNT(*) AS n FROM sales GROUP BY category ORDER BY category;"),
    "GROUP BY category делит таблицу на группы, COUNT(*) считает строки в каждой, ORDER BY упорядочивает итог.",
    ordered=True, starter="SELECT category FROM sales\n")

a3 = sql_task("a3-having", "write", "Категории с большим спросом",
    "Выведите категории, в которых продано **не меньше 20 штук** (сумма `qty`): столбцы `category` и `total`. Порядок строк не важен.",
    "Фильтровать группы условием HAVING.", "SELECT category, SUM(qty) AS total\nFROM sales\nGROUP BY category\nHAVING SUM(qty) >= 20;",
    [(SCHEMA, False, None), (SETUP_B, True, "Граница включена: ровно 20 тоже подходит"), (SETUP_C, True, "Бывает, что ни одна категория не подходит")],
    [("SELECT category, SUM(qty) AS total FROM sales GROUP BY category;", "Нет условия на группы."),
     ("SELECT category, SUM(qty) AS total FROM sales GROUP BY category HAVING SUM(qty) > 20;", "Строго больше: пропущены группы ровно с 20."),
     ("SELECT category, SUM(qty) AS total FROM sales WHERE qty >= 20 GROUP BY category;", "Условие применено к отдельным строкам, а не к группам."),
     ("SELECT category, COUNT(*) AS total FROM sales GROUP BY category HAVING COUNT(*) >= 20;", "Считается число строк, а нужна сумма количества.")],
    hints("Условие касается итога по группе, а не отдельной строки.", "Для условий на группы — HAVING.", "HAVING пишется после GROUP BY.", "В условии повторите агрегат: SUM(qty).", "Граница «не меньше» — знак >=."),
    "HAVING применяется после группировки и может использовать агрегаты, а WHERE — до неё и только к строкам.")

a4 = sql_task("a4-avg", "write", "Средняя цена",
    "Выведите для каждой категории её название и **среднюю цену** товара, округлённую до 2 знаков: столбцы `category` и `avg_price`. Порядок — от большей средней цены к меньшей (при равенстве — по названию категории).",
    "Применять AVG и ROUND.", "SELECT category, ROUND(AVG(price), 2) AS avg_price\nFROM sales\nGROUP BY category\nORDER BY avg_price DESC, category;",
    [(SCHEMA, False, None), (SETUP_B, True, "Среднее не всегда круглое число: нужно округление до 2 знаков"), (SETUP_C, True, None)],
    [("SELECT category, AVG(price) AS avg_price FROM sales GROUP BY category ORDER BY avg_price DESC, category;", "Нет округления."),
     ("SELECT category, ROUND(AVG(price), 2) AS avg_price FROM sales GROUP BY category ORDER BY avg_price, category;", "Порядок по возрастанию."),
     ("SELECT category, ROUND(MAX(price), 2) AS avg_price FROM sales GROUP BY category ORDER BY avg_price DESC, category;", "Считается максимум, а не среднее."),
     ("SELECT category, ROUND(AVG(price * qty), 2) AS avg_price FROM sales GROUP BY category ORDER BY avg_price DESC, category;", "Усредняется выручка, а не цена.")],
    hints("Среднее значение — функция AVG.", "Группируем по категории.", "Округляет ROUND(значение, число_знаков).", "Сортируем по имени результата: ORDER BY avg_price DESC.", "При равенстве — добавьте второй столбец сортировки через запятую."),
    "ROUND(AVG(price), 2) — среднее с двумя знаками; ORDER BY можно писать по псевдониму результата.",
    ordered=True, starter="SELECT category FROM sales\n")

CODE5 = SCHEMA + "SELECT category, SUM(qty) AS total\nFROM sales\nWHERE price < 100\nGROUP BY category\nHAVING SUM(qty) > 20\nORDER BY category;\n"
a5 = sql_predict("a5-predict", "Что вернёт запрос?", CODE5,
    [("канцелярия | 50\nеда | 15", "В еде продано 15 штук, условие HAVING требует больше 20."), ("канцелярия | 50\nтехника | 2", "Техника отброшена условием WHERE: цена 120 не меньше 100.")],
    hints("Порядок выполнения: WHERE, затем GROUP BY, затем HAVING.", "WHERE price < 100 убирает наушники.", "Остаются еда (15 штук) и канцелярия (50 штук).", "HAVING оставляет группы со штуками больше 20.", "Остаётся одна категория."),
    "Сначала WHERE убирает строки, потом группы считаются, потом HAVING убирает группы.")

skills = {"sql.aggregates": "Агрегатные функции", "sql.group": "GROUP BY и HAVING", "sql.round": "Среднее и округление"}
write_lesson("sql-02-aggregates", "SQL: агрегаты и группировка",
             "Считать итоги функциями COUNT, SUM, AVG, MIN, MAX, группировать строки и фильтровать группы.",
             list(skills), ["sql-01-select"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Агрегат в WHERE", "fix": "Условие на итог группы пишите в HAVING.", "errorType": "SQLError"},
              {"mistake": "Столбец в SELECT не из GROUP BY и не агрегат", "fix": "Группируйте по нему или оберните агрегатом."},
              {"mistake": "HAVING вместо WHERE для обычных строк", "fix": "Фильтр на строки — WHERE, он работает быстрее."},
              {"mistake": "Забывают ROUND для среднего", "fix": "AVG даёт много знаков после запятой."}],
             min_pass=3, pack="sql-basics", runner="sql")
merge_pack("sql-02-aggregates", skills)

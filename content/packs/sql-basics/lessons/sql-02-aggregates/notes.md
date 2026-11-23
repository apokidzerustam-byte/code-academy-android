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

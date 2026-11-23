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

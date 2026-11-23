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

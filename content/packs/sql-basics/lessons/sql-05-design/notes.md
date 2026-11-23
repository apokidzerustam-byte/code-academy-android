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

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

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

```python
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

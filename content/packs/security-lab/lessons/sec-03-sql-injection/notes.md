# SQL-инъекции

```python
import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (name TEXT, role TEXT)")
conn.execute("INSERT INTO users VALUES ('anna', 'admin')")

# безопасно: значение передаётся отдельно
rows = conn.execute("SELECT role FROM users WHERE name = ?", ("anna",)).fetchall()
print(rows)
```

## Правила

1. Не склеивайте SQL из строк пользователя.
2. Значения — через `?` и кортеж параметров.
3. Имена столбцов и таблиц — только из белого списка.
4. Права доступа к базе — минимально необходимые.

Все примеры курса работают только с базой в памяти и вымышленными данными.

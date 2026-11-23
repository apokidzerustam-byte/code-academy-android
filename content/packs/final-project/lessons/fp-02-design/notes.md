# Проектирование структуры

```python
tasks = []

def add_task(tasks, title):
    task = {"id": len(tasks) + 1, "title": title, "done": False}
    tasks.append(task)
    return task

def split_command(line):
    parts = line.split()
    if not parts:
        return "", []
    return parts[0].lower(), parts[1:]

task = add_task(tasks, "Купить хлеб")
print(f"Добавлено: #{task['id']} {task['title']}")
print(split_command("ADD Купить   молоко"))
```

1. Данные: список задач, список расходов.
2. Операции возвращают результат, не печатают.
3. Оболочка печатает и читает ввод.

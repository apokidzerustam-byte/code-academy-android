# Реализация по шагам

```python
def cmd_hello(args):
    return "Привет, " + (" ".join(args) or "мир")

COMMANDS = {"hello": cmd_hello}

for line in ["hello Анна", "dance"]:
    name, *args = line.split()
    handler = COMMANDS.get(name)
    print(handler(args) if handler else f"Неизвестная команда: {name}")
```

Цикл: `while True` → `input()` → `except EOFError: break`.

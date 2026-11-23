# Демонстрация и выпуск

```python
steps = [
    ("add Купить хлеб", "Добавлено: #1 Купить хлеб"),
    ("spend 12.5 food", "Расход: 12.5 food"),
    ("report", "Расходов: 1"),
]
for number, (command, result) in enumerate(steps, 1):
    print(f"{number}. {command} -> {result}")

checks = {"функции": True, "тесты": True, "README": False, "секреты": True}
print(f"готово {sum(checks.values())} из {len(checks)}")
```

Чек-лист: функции · тесты · README · нет секретов · пример запуска.

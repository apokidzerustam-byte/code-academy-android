# Слои приложения

```python
class ListRepo:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def all(self):
        return list(self.items)


class FinanceService:
    def __init__(self, repo):
        self.repo = repo

    def add(self, kind, amount):
        if kind not in ("income", "expense"):
            raise ValueError("неизвестный тип")
        if amount <= 0:
            raise ValueError("сумма должна быть положительной")
        self.repo.add((kind, amount))

    def balance(self):
        return sum(a if k == "income" else -a for k, a in self.repo.all())
```

## Слои

1. **Интерфейс** — ввод и вывод, никаких правил.
2. **Логика (сервис)** — правила предметной области.
3. **Данные (репозиторий)** — сохранить и отдать.

Зависимости направлены вниз. Варианты схем: MVC, MVVM, чистая архитектура.

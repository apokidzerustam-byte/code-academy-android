# Внедрение зависимостей

```python
class Service:
    def __init__(self, repo):
        self.repo = repo

    def add(self, item):
        self.repo.add(item.strip().lower())


class FakeRepo:
    def __init__(self):
        self.saved = []

    def add(self, item):
        self.saved.append(item)


fake = FakeRepo()
Service(fake).add("  Молоко ")
print(fake.saved)
```

## Правила

1. Не создавайте зависимость внутри — принимайте снаружи.
2. Для проверок подставляйте поддельные реализации.
3. Время и случайность — тоже зависимости: `today` параметром.
4. Всё собирается в одном месте — корне композиции (`main`).

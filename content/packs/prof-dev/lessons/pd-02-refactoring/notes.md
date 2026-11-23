# Рефакторинг

```python
DISCOUNTS = {"regular": 0, "silver": 5, "gold": 10, "vip": 20}

def discounted(price, percent=10):
    return price - price * percent / 100

def discount_for(kind):
    return DISCOUNTS.get(kind, 0)

def count_adults(items):
    return sum(1 for p in items if p["age"] >= 18)

def old(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total

def new(n):
    return n * (n + 1) // 2

print(all(old(n) == new(n) for n in range(100)))
```

Маленькие шаги · проверка после каждого шага · граничные значения.

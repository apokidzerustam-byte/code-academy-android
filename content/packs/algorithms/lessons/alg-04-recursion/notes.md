# Рекурсия

```python
def factorial(n):
    if n == 0:          # базовый случай
        return 1
    return n * factorial(n - 1)   # шаг рекурсии

print(factorial(5))     # 120
```

## Список

```python
def total(items):
    if not items:
        return 0
    return items[0] + total(items[1:])
```

## Вложенные списки

```python
def deep_sum(data):
    result = 0
    for item in data:
        if isinstance(item, list):
            result += deep_sum(item)
        else:
            result += item
    return result

print(deep_sum([1, [2, 3], [[4], 5]]))   # 15
```

## Запомните

1. Сначала базовый случай.
2. Каждый шаг должен приближать к базовому случаю.
3. Глубина ограничена (~1000): для больших данных используйте цикл.

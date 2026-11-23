# Оптимизация

## Мемоизация

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(fib(80))
print(fib.cache_info())
```

## Динамическое программирование

```python
def ways(n):               # способы подняться на n ступенек (шаг 1 или 2)
    table = [1, 1]
    for i in range(2, n + 1):
        table.append(table[i - 1] + table[i - 2])
    return table[n]
```

## Префиксные суммы

```python
nums = [3, 1, 4, 1, 5, 9, 2, 6]
prefix = [0]
for x in nums:
    prefix.append(prefix[-1] + x)

def range_sum(l, r):       # включительно
    return prefix[r + 1] - prefix[l]
```

## Правило

Сначала **измерьте**, потом оптимизируйте: часто хватает замены `list` на `set` или `dict`.

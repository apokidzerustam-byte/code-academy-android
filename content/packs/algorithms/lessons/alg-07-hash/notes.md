# Хеш-таблицы

```python
def bucket(key, size):
    return sum(ord(ch) for ch in key) % size

def put(table, key, value):
    chain = table[bucket(key, len(table))]
    for pair in chain:
        if pair[0] == key:
            pair[1] = value
            return
    chain.append([key, value])

def get(table, key):
    for k, v in table[bucket(key, len(table))]:
        if k == key:
            return v
    return None
```

## Подсчёт и пары

```python
counts = {}
for ch in "ананас":
    counts[ch] = counts.get(ch, 0) + 1

def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
```

## Запомните

1. Коллизия — разные ключи в одной корзине; решаем цепочками.
2. Ключи `dict` и элементы `set` — только неизменяемые.
3. `x in set` и `dict[key]` — O(1) в среднем; `x in list` — O(n).

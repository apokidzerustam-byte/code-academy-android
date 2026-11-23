# Быстрые сортировки

## Слияние

```python
def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def merge_sort(items):
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    return merge(merge_sort(items[:mid]), merge_sort(items[mid:]))
```

## Быстрая сортировка

```python
def quick_sort(items):
    if len(items) <= 1:
        return list(items)
    pivot = items[0]
    less = [x for x in items if x < pivot]
    equal = [x for x in items if x == pivot]
    more = [x for x in items if x > pivot]
    return quick_sort(less) + equal + quick_sort(more)
```

| | Слияние | Быстрая |
|---|---|---|
| Среднее | O(n log n) | O(n log n) |
| Худшее | O(n log n) | O(n²) |
| Память | O(n) | O(log n)…O(n) |

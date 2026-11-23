# Сортировки

## Пузырёк

```python
def bubble_sort(items):
    items = list(items)
    swapped = True
    while swapped:
        swapped = False
        for i in range(len(items) - 1):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = items[i + 1], items[i]
                swapped = True
    return items

print(bubble_sort([5, 2, 9, 1, 7]))
```

## Выбор и вставки

```python
def selection_sort(items):
    items = list(items)
    for i in range(len(items)):
        smallest = i
        for j in range(i + 1, len(items)):
            if items[j] < items[smallest]:
                smallest = j
        items[i], items[smallest] = items[smallest], items[i]
    return items

def insertion_sort(items):
    items = list(items)
    for i in range(1, len(items)):
        j = i
        while j > 0 and items[j - 1] > items[j]:
            items[j - 1], items[j] = items[j], items[j - 1]
            j -= 1
    return items
```

## Встроенная сортировка

```python
tasks = [("отчёт", 2), ("почта", 1), ("звонок", 2), ("зарядка", 1)]
print(sorted(tasks, key=lambda t: (t[1], t[0])))
print(sorted(tasks, key=lambda t: t[1], reverse=True))
```

| Алгоритм | Худший случай | Устойчивый |
|---|---|---|
| Пузырёк | O(n²) | да |
| Выбор | O(n²) | нет |
| Вставки | O(n²) | да |
| `sorted` (Timsort) | O(n log n) | да |

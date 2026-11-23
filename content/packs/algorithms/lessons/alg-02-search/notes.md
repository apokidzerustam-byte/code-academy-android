# Поиск: линейный и бинарный

## Линейный поиск — O(n)

```python
def linear_search(items, target):
    for i in range(len(items)):
        if items[i] == target:
            return i
    return -1

print(linear_search(["Аня", "Борис", "Вера"], "Вера"))   # 2
```

## Бинарный поиск — O(log n)

Работает **только на отсортированном** списке: сравниваем с серединой и отбрасываем половину.

```python
def binary_search(items, target):
    low, high = 0, len(items) - 1
    while low <= high:
        mid = (low + high) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

nums = [1, 3, 5, 7, 9, 11, 13, 15]
print(binary_search(nums, 11), binary_search(nums, 4))   # 5 -1
```

Для миллиона элементов бинарному поиску нужно около 20 шагов, линейному — до миллиона.

## Готовые средства Python

```python
from bisect import bisect_left

items = [1, 3, 5, 7, 9]
print(7 in items, items.index(7))   # True 3 — линейно
i = bisect_left(items, 7)
print(i, items[i] == 7)             # 3 True — бинарно
```

## Запомните

1. Бинарный поиск без сортировки даёт неверный результат.
2. Условие цикла — `low <= high` (нестрогое).
3. Границы сдвигаем на `mid + 1` и `mid - 1`, иначе возможен бесконечный цикл.

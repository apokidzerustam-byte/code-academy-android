# Цикл for и range

```python
for i in range(5):
    print(i)        # 0 1 2 3 4
```

## range

| Запись | Числа |
| --- | --- |
| `range(5)` | 0, 1, 2, 3, 4 |
| `range(1, 6)` | 1, 2, 3, 4, 5 |
| `range(2, 11, 2)` | 2, 4, 6, 8, 10 |
| `range(5, 0, -1)` | 5, 4, 3, 2, 1 |

Конец в `range` **не входит**.

## Сумма

```python
total = 0
for i in range(1, 101):
    total += i
print(total)        # 5050
```

## Перебор строки и in

```python
count = 0
for ch in "программирование":
    if ch in "аеёиоуыэюя":
        count += 1
print(count)        # 7
```

## continue и break

```python
for i in range(1, 11):
    if i % 3 == 0:
        continue    # пропустить это число
    print(i, end=" ")
print()
```

`print(..., end=" ")` выводит без перехода на новую строку.

## Запомните

1. `for` — когда число повторений известно, `while` — когда нет.
2. `range(a, b)` не включает `b`.
3. `continue` — к следующей итерации, `break` — выйти из цикла.

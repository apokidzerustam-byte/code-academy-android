# Срезы, кортежи, множества

## Срезы

```python
nums = [10, 20, 30, 40, 50, 60]
print(nums[1:4])     # [20, 30, 40]  — конец не включается
print(nums[:3], nums[3:])
print(nums[::2])     # [10, 30, 50]
print(nums[::-1])    # перевёрнутый список
print("привет"[1:4]) # рив
```

## Кортежи

```python
point = (3, 4)
x, y = point          # распаковка
a, b = 1, 2
a, b = b, a           # обмен значений
print(x, y, a, b)
```

Присвоить элемент кортежа нельзя: `TypeError: 'tuple' object does not support item assignment`.

## Множества

```python
marks = [5, 3, 5, 4, 3, 5]
unique = set(marks)
print(sorted(unique), len(unique), 4 in unique)

anna = {"Матрица", "Солярис", "Аватар"}
boris = {"Аватар", "Начало", "Матрица"}
print(sorted(anna & boris))   # общие
print(sorted(anna - boris))   # только у Ани
```

| Операция | Смысл |
| --- | --- |
| `a \| b` | объединение |
| `a & b` | пересечение |
| `a - b` | разность |

## enumerate и zip

```python
names = ["Аня", "Борис", "Вера"]
marks = [5, 4, 3]
for i, name in enumerate(names, 1):
    print(i, name)
for name, mark in zip(names, marks):
    print(name, mark)
```

## Запомните

1. Конец среза не включается.
2. Множество не хранит повторы и не гарантирует порядок.
3. Пустое множество — `set()`, а не `{}`.

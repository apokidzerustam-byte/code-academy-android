# Словари

```python
ages = {"Аня": 25, "Борис": 30, "Вера": 22}
print(ages["Аня"], len(ages))              # 25 3
print(ages.get("Глеб"), ages.get("Глеб", 0))   # None 0
print("Вера" in ages)                      # True
```

`ages["Глеб"]` для отсутствующего ключа даёт `KeyError`.

## Изменение

```python
ages = {"Аня": 25, "Борис": 30, "Вера": 22}
ages["Глеб"] = 19      # добавить
ages["Аня"] = 26       # обновить
del ages["Борис"]      # удалить
print(ages.pop("Вера"), ages)
```

## Перебор

```python
prices = {"хлеб": 40, "молоко": 90, "сыр": 350}
for name, price in prices.items():
    print(name, price)
print(sum(prices.values()), sorted(prices))
```

## Подсчёт частот

```python
counts = {}
for word in "да нет да да нет может".split():
    counts[word] = counts.get(word, 0) + 1
print(counts)       # {'да': 3, 'нет': 2, 'может': 1}
```

## Словарь списков

```python
marks = {"Аня": [5, 4, 5], "Борис": [3, 4]}
marks["Борис"].append(5)
for name, lst in marks.items():
    print(name, sum(lst) / len(lst))
```

## Запомните

1. Ключи — только неизменяемые значения (строки, числа, кортежи).
2. Для безопасного чтения используйте `get`.
3. `for k in d` перебирает ключи, `d.items()` — пары.

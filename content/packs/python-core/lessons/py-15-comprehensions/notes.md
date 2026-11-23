# Списковые включения, lambda, sorted с key

```python
nums = [1, 2, 3, 4, 5, 6]
print([n * n for n in nums])                    # квадраты
print([n for n in nums if n % 2 == 0])          # чётные
print([n * n for n in nums if n % 2 == 0])      # квадраты чётных
```

## Словари и множества

```python
words = ["кот", "собака", "слон", "ёж"]
print({w: len(w) for w in words})
print({len(w) for w in words})
```

## lambda

```python
square = lambda x: x * x
print(square(5))       # 25
```

## sorted с ключом

```python
words = ["слон", "кот", "собака", "ёж"]
print(sorted(words, key=len))
print(sorted(words, key=len, reverse=True))

people = [("Аня", 25), ("Борис", 20), ("Вера", 25), ("Глеб", 20)]
print(sorted(people, key=lambda p: p[1]))
print(sorted(people, key=lambda p: (-p[1], p[0])))   # по убыванию возраста, затем по имени
```

## Запомните

1. `sorted` возвращает **новый** список, исходный не меняется; `lst.sort()` сортирует на месте.
2. Сортировка устойчивая: равные ключи сохраняют исходный порядок.
3. Если включение не помещается в одну читаемую строку — используйте обычный цикл.

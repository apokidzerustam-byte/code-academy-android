# Файлы

```python
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("Купить хлеб\n")
    f.write("Позвонить маме\n")

with open("notes.txt", encoding="utf-8") as f:
    for line in f:
        print(line.strip())
```

| Режим | Что делает |
| --- | --- |
| `"r"` | чтение (по умолчанию); файла нет — `FileNotFoundError` |
| `"w"` | запись; **стирает** старое содержимое |
| `"a"` | дозапись в конец |

## Файла нет

```python
try:
    with open("settings.txt", encoding="utf-8") as f:
        data = f.read()
except FileNotFoundError:
    data = "настроек пока нет"
print(data)
```

## Разбор таблицы

```python
with open("cart.txt", "w", encoding="utf-8") as f:
    f.write("хлеб;2;40\nмолоко;1;90\n")

total = 0
with open("cart.txt", encoding="utf-8") as f:
    for line in f:
        name, qty, price = line.strip().split(";")
        total += int(qty) * int(price)
print(total)    # 170
```

## Запомните

1. Всегда `with open(...)` и `encoding="utf-8"`.
2. `"w"` стирает файл — для дозаписи используйте `"a"`.
3. `strip()` убирает перевод строки в конце.

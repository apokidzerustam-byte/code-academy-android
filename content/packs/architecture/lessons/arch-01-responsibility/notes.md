# Единая ответственность

```python
def parse_line(line):
    name, amount = line.split(";")
    return name, int(amount)


def totals_by_name(rows):
    totals = {}
    for name, amount in rows:
        totals[name] = totals.get(name, 0) + amount
    return totals


def format_report(totals):
    return "\n".join(f"{name}: {totals[name]}" for name in sorted(totals))
```

## Идеи

1. Разбор, вычисления и оформление — отдельные функции.
2. Чистая функция: результат зависит только от аргументов, снаружи ничего не меняет.
3. Ввод-вывод — на границе программы.
4. Имя функции — глагол; если в описании «и» — разделите.

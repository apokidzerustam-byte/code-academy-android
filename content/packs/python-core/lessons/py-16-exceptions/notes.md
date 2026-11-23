# Исключения

```python
try:
    number = int("абв")
except ValueError:
    print("Это не число")
print("программа продолжается")
```

## Несколько обработчиков, else и finally

```python
def divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        print("на ноль делить нельзя")
    except TypeError as e:
        print("неверный тип:", e)
    else:
        print("результат", result)
    finally:
        print("готово")

divide(10, 2)
divide(1, 0)
```

## raise

```python
def check_age(age):
    if age < 0 or age > 150:
        raise ValueError("недопустимый возраст")
    return age

try:
    check_age(-3)
except ValueError as e:
    print("ошибка:", e)
```

## Частые исключения

| Исключение | Когда возникает |
| --- | --- |
| `ValueError` | подходящий тип, неподходящее значение: `int("abc")` |
| `TypeError` | неверный тип: `"1" + 1` |
| `ZeroDivisionError` | деление на ноль |
| `KeyError` | нет ключа в словаре |
| `IndexError` | индекс вне списка |
| `FileNotFoundError` | файла нет |

## Запомните

1. Ловите конкретные ошибки, а не голый `except`.
2. `else` — когда ошибки не было; `finally` — всегда.
3. Для недопустимых данных вызывайте `raise`.

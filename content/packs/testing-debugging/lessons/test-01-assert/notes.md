# Тесты и assert

```python
def bigger(a, b):
    if a > b:
        return a
    return b

assert bigger(3, 7) == 7
assert bigger(5, 5) == 5, "равные числа"
```

`assert` ничего не печатает при успехе; при неудаче — `AssertionError` с вашим сообщением.

## Таблица тестов

```python
def bigger(a, b):
    return a if a > b else b

cases = [(3, 7, 7), (10, 4, 10), (0, -1, 0)]
for a, b, expected in cases:
    got = bigger(a, b)
    print(a, b, "->", got, "ок" if got == expected else "ОШИБКА")
```

## Что проверять

1. Обычные значения.
2. Границы: ноль, равные числа, пустая строка.
3. Неудобные значения: отрицательные, очень большие.

## Тест полезен, если способен упасть

Хороший тест можно проверить так: намеренно сломайте код — тест должен это заметить.

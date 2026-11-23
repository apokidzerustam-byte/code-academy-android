# Параметры по умолчанию, именованные аргументы, область видимости

```python
def power(base, exponent=2):
    return base ** exponent

print(power(5))        # 25
print(power(2, 10))    # 1024
```

## Именованные аргументы

```python
def format_price(rubles, kopeks=0, currency="₽"):
    return f"{rubles}.{kopeks:02d} {currency}"

print(format_price(150))                    # 150.00 ₽
print(format_price(10, currency="$"))       # 10.00 $
```

## Несколько возвращаемых значений

```python
def min_max(items):
    return min(items), max(items)

low, high = min_max([4, 9, 1, 7])
print(low, high)    # 1 9
```

## Область видимости

```python
x = 10

def f():
    x = 5          # новая локальная переменная
    return x * 2

print(f(), x)      # 10 10
```

## Ловушка: изменяемое значение по умолчанию

```python
def add_tag(tag, tags=None):
    if tags is None:
        tags = []
    tags.append(tag)
    return tags

print(add_tag("a"), add_tag("b"))   # ['a'] ['b']
```

## Запомните

1. Необязательные параметры ставят после обязательных.
2. Для списков и словарей по умолчанию используйте `None`.
3. Присваивание внутри функции создаёт локальную переменную.

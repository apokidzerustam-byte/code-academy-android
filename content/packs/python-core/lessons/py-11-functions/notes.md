# Функции

**Функция** — именованный набор действий. Объявляется через `def`, вызывается по имени.

```python
def greet(name):
    print("Привет,", name)

greet("Аня")
greet("Борис")
```

## return

```python
def square(x):
    return x * x

a = square(5)
print(a)                      # 25
print(square(3) + square(4))  # 25
```

`print` только показывает значение, `return` отдаёт его программе. После `return` функция завершается.

## Несколько параметров

```python
def area(width, height):
    return width * height

print(area(4, 5))   # 20
```

## Функции вызывают функции

```python
def is_even(n):
    return n % 2 == 0

def count_even(numbers):
    count = 0
    for n in numbers:
        if is_even(n):
            count += 1
    return count

print(count_even([1, 2, 3, 4, 5, 6]))   # 3
```

## Ошибки

| Ошибка | Что произошло |
| --- | --- |
| результат `None` | в функции нет `return` |
| `TypeError: add() missing 1 required positional argument` | аргументов меньше, чем параметров |
| `NameError: name 'hello' is not defined` | функцию вызвали раньше, чем объявили |

## Запомните

1. Функция делает одну понятную вещь.
2. Нужен результат — используйте `return`, а не `print`.
3. Сначала `def`, потом вызов.

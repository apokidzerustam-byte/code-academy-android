# Наследование и dataclass

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        return "Гав"

class Cat(Animal):
    def speak(self):
        return "Мяу"

for animal in [Dog("Рекс"), Cat("Мурка"), Animal("Зверь")]:
    print(animal.name, animal.speak())
```

## super()

```python
class Person:
    def __init__(self, name):
        self.name = name

class Student(Person):
    def __init__(self, name, school):
        super().__init__(name)
        self.school = school

s = Student("Аня", "Гимназия 5")
print(s.name, s.school, isinstance(s, Person))
```

## dataclass

```python
from dataclasses import dataclass

@dataclass
class Transaction:
    title: str
    amount: float

print(Transaction("кофе", -150) == Transaction("кофе", -150))   # True
```

## Запомните

1. Дочерний класс: `class Child(Parent)`.
2. В `__init__` потомка вызывайте `super().__init__(...)`.
3. Полиморфизм: один вызов метода — разное поведение объектов.

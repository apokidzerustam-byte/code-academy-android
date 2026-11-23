# Классы и объекты

```python
class Student:
    def __init__(self, name):
        self.name = name
        self.marks = []

    def add_mark(self, mark):
        self.marks.append(mark)

    def average(self):
        return sum(self.marks) / len(self.marks)

    def __str__(self):
        return f"{self.name}, средний балл {self.average():.1f}"

anna = Student("Аня")
anna.add_mark(5)
anna.add_mark(4)
print(anna)          # Аня, средний балл 4.5
```

## Счёт

```python
class Account:
    def __init__(self, balance=0):
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("недостаточно средств")
        self.balance -= amount

acc = Account(100)
acc.deposit(50)
acc.withdraw(30)
print(acc.balance)   # 120
```

## Запомните

1. `self` — первый параметр каждого метода; он подставляется автоматически.
2. Атрибуты хранятся в объекте: `self.name = name`.
3. Класс — чертёж, объект — экземпляр, у каждого свои данные.
4. Меняйте состояние через методы, чтобы работали проверки.

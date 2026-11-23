from lib import *

begin()
scenes = [
 S("intro", "Классы на основе других классов", """
  Допустим, нам нужны классы собаки и кошки. У обоих есть имя, оба умеют издавать звук и оба едят. Копировать общий код в каждый
  класс — значит дублировать его, а дублирование всегда рано или поздно приводит к ошибкам. Наследование решает эту проблему:
  мы описываем общее поведение в базовом классе, а в дочерних классах добавляем или меняем только отличия. Дочерний
  класс получает всё от родителя бесплатно. Ещё одна важная идея — полиморфизм, и сегодня мы разберём обе.""",
  nt("**Наследование** — дочерний класс получает атрибуты и методы родителя", at="Наследование решает")),
 S("inherit", "Наследование", """
  Базовый класс Animal хранит имя и умеет представляться. В скобках после имени дочернего класса указываем родителя: Dog
  от Animal. Класс Dog не содержит ни одной строки кода, но уже умеет всё, что умеет Animal. Создадим собаку и вызовем метод
  родителя. А функция isinstance проверяет, принадлежит ли объект классу: собака считается и Dog, и Animal.""",
  clr(), t('class Animal:\n    def __init__(self, name):\n        self.name = name\n\n    def intro(self):\n        return f"Я {self.name}"\n\n', at="Базовый класс"),
  t("class Dog(Animal):\n    pass\n\n", at="В скобках"),
  t('rex = Dog("Рекс")\nprint(rex.intro())\nprint(isinstance(rex, Dog), isinstance(rex, Animal))\n', at="Создадим собаку"), run("А функция")),
 S("override", "Переопределение методов", """
  Дочерний класс может заменить метод родителя своим. Добавим в Animal метод speak, который возвращает неопределённый звук, а в
  Dog и Cat переопределим его: собака говорит гав, кошка — мяу. Если при этом нужно вызвать и родительский код, используют
  функцию super. Например, метод intro у собаки может сначала взять родительское представление, а затем добавить к нему слово
  «и я лаю».""",
  clr(), t('class Animal:\n    def __init__(self, name):\n        self.name = name\n\n    def speak(self):\n        return "..."\n\n    def intro(self):\n        return f"Я {self.name}"\n\n', at="Добавим в Animal"),
  t('class Dog(Animal):\n    def speak(self):\n        return "Гав"\n\n    def intro(self):\n        return super().intro() + " и я лаю"\n\n', at="переопределим"),
  t('class Cat(Animal):\n    def speak(self):\n        return "Мяу"\n\n', at="переопределим"),
  t('print(Dog("Рекс").speak(), Cat("Мурка").speak(), Animal("Зверь").speak())\nprint(Dog("Рекс").intro())\n', at="Например"), run("лаю")),
 S("poly", "Полиморфизм", """
  Полиморфизм — это возможность работать с разными объектами одинаково. У собаки, кошки и просто животного есть метод speak, и
  нам неважно, какой именно перед нами объект: мы просто вызываем метод, а каждый объект отвечает по-своему. Соберём всех в
  один список и пройдём циклом. Код цикла не знает о конкретных классах, и когда вы добавите птицу, переписывать цикл не
  придётся. Именно так устроены большие программы.""",
  t('\nzoo = [Dog("Рекс"), Cat("Мурка"), Animal("Зверь")]\nfor animal in zoo:\n    print(animal.name, animal.speak())\n', at="Соберём"), run("Именно так")),
 S("init", "Конструктор у потомка", """
  Если дочернему классу нужны дополнительные данные, он определяет свой init, и в нём обязательно нужно вызвать init родителя через
  super. Иначе атрибуты, которые создаёт родитель, не появятся, и вы получите странные ошибки. Класс Student добавляет к
  имени ещё и школу. Попробуем создать студента и посмотреть оба атрибута.""",
  clr(), t('class Person:\n    def __init__(self, name):\n        self.name = name\n\n', at="Если дочернему"),
  t('class Student(Person):\n    def __init__(self, name, school):\n        super().__init__(name)\n        self.school = school\n\n', at="Класс Student"),
  t('s = Student("Аня", "Гимназия 5")\nprint(s.name, s.school)\n', at="Попробуем"), run("Попробуем")),
 S("dataclass", "Dataclass: класс без рутины", """
  Для классов, которые просто хранят данные, есть декоратор dataclass из модуля dataclasses. Достаточно перечислить поля с типами,
  и Python сам напишет init, красивое строковое представление и сравнение. Опишем транзакцию в программе учёта: название и
  сумма. Печать объекта сразу показывает все поля, а две транзакции с одинаковыми данными считаются равными.""",
  clr(), t("from dataclasses import dataclass\n\n@dataclass\nclass Transaction:\n    title: str\n    amount: float\n\n", at="Достаточно"),
  t('a = Transaction("кофе", -150)\nb = Transaction("кофе", -150)\nprint(a)\nprint(a == b, a.amount)\n', at="Печать объекта"), run("Печать объекта")),
 S("summary", "Итог", """
  Подведём итог. Дочерний класс наследует всё от родителя и объявляется с указанием родителя в скобках. Методы можно
  переопределять, а родительскую версию вызывать через super. Полиморфизм позволяет работать с разными объектами через общий
  интерфейс. Если у потомка свой init, обязательно вызывайте init родителя. А dataclass избавляет от шаблонного кода в
  классах-хранилищах данных. Не злоупотребляйте наследованием: иногда достаточно простого объекта с нужными методами.""",
  nt("`class Child(Parent)` · `super()` · `isinstance` · `@dataclass`", at="Подведём итог")),
]

notes = """
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
"""

SHAPES = "import math\n\n\nclass Shape:\n    def area(self):\n        return 0\n\n\nclass Circle(Shape):\n    def __init__(self, r):\n        self.r = r\n\n    def area(self):\n        return math.pi * self.r ** 2\n\n\nclass Rectangle(Shape):\n    def __init__(self, w, h):\n        self.w = w\n        self.h = h\n\n    def area(self):\n        return self.w * self.h\n\n\nclass Square(Rectangle):\n    def __init__(self, a):\n        super().__init__(a, a)\n\n\n"

a1 = fn_task("a1-speak", "Хор животных", "Напишите классы `Animal` (метод `speak()` возвращает `\"...\"`), `Dog` (`\"Гав\"`), `Cat` (`\"Мяу\"`) и функцию `chorus(kinds)`: для каждого названия из списка (`\"dog\"`, `\"cat\"` или любое другое) создайте животное соответствующего класса (для неизвестных — `Animal`) и верните список их звуков.\n\nПример: `chorus([\"dog\", \"cat\", \"cow\"])` → `[\"Гав\", \"Мяу\", \"...\"]`.",
  "chorus", 'class Animal:\n    def speak(self):\n        return "..."\n\n\nclass Dog(Animal):\n    def speak(self):\n        return "Гав"\n\n\nclass Cat(Animal):\n    def speak(self):\n        return "Мяу"\n\n\ndef chorus(kinds):\n    classes = {"dog": Dog, "cat": Cat}\n    return [classes.get(kind, Animal)().speak() for kind in kinds]\n',
  [[["dog", "cat", "cow"]], [[]], ([["cat", "cat"]], True), ([["fish", "dog", "dog"]], True)],
  [('class Animal:\n    def speak(self):\n        return "..."\n\n\nclass Dog(Animal):\n    def speak(self):\n        return "Гав"\n\n\nclass Cat(Animal):\n    pass\n\n\ndef chorus(kinds):\n    classes = {"dog": Dog, "cat": Cat}\n    return [classes.get(kind, Animal)().speak() for kind in kinds]\n', "Cat не переопределяет speak и говорит «...» вместо «Мяу»."),
   ('class Animal:\n    def speak(self):\n        return "..."\n\n\nclass Dog(Animal):\n    def speak(self):\n        return "Гав"\n\n\nclass Cat(Animal):\n    def speak(self):\n        return "Мяу"\n\n\ndef chorus(kinds):\n    return ["Гав" if k == "dog" else "Мяу" for k in kinds]\n', "Классы не используются, и неизвестные животные получают «Мяу» вместо «...»."),
   ('class Animal:\n    def speak(self):\n        return "..."\n\n\nclass Dog(Animal):\n    def speak(self):\n        return "Гав"\n\n\nclass Cat(Animal):\n    def speak(self):\n        return "Мяу"\n\n\ndef chorus(kinds):\n    classes = {"dog": Dog, "cat": Cat}\n    return [classes.get(kind, Animal) for kind in kinds]\n', "Не созданы объекты и не вызван speak: возвращаются сами классы.")],
  hints("Каждое животное — объект своего класса, звук зависит от класса.", "Родитель Animal отвечает «...», потомки переопределяют speak.", "Сопоставьте названия классам в словаре: «dog» → Dog.", "classes.get(kind, Animal) вернёт класс (Animal, если названия нет в словаре).", "Создайте объект вызовом класса и вызовите speak: classes.get(kind, Animal)().speak()."),
  "Полиморфизм: один вызов speak() у объектов разных классов даёт разные ответы; словарь заменяет цепочку if.")

a2 = fn_task("a2-areas", "Общая площадь фигур", "Заготовлены классы `Shape` → `Circle(r)`, `Rectangle(w, h)` и `Square(a)` (наследует Rectangle). Напишите функцию `total_area(shapes)`: `shapes` — список `[\"circle\", r]`, `[\"rect\", w, h]` или `[\"square\", a]`; верните сумму площадей, округлённую до 2 знаков (`round`).\n\nПример: `total_area([[\"rect\", 2, 3], [\"square\", 2]])` → `10`.",
  "total_area", SHAPES + 'def total_area(shapes):\n    total = 0\n    for kind, *args in shapes:\n        if kind == "circle":\n            shape = Circle(*args)\n        elif kind == "rect":\n            shape = Rectangle(*args)\n        else:\n            shape = Square(*args)\n        total += shape.area()\n    return round(total, 2)\n',
  [[[["rect", 2, 3], ["square", 2]]], [[]], ([[["circle", 1]]], True), ([[["circle", 2], ["rect", 1, 1], ["square", 3]]], True), ([[["square", 5]]], True)],
  [(SHAPES.replace("super().__init__(a, a)", "self.w = a\n        self.h = 1") + 'def total_area(shapes):\n    total = 0\n    for kind, *args in shapes:\n        if kind == "circle":\n            shape = Circle(*args)\n        elif kind == "rect":\n            shape = Rectangle(*args)\n        else:\n            shape = Square(*args)\n        total += shape.area()\n    return round(total, 2)\n', "Квадрат создан неверно: высота равна 1, а не стороне."),
   (SHAPES + 'def total_area(shapes):\n    total = 0\n    for kind, *args in shapes:\n        if kind == "circle":\n            shape = Circle(*args)\n        elif kind == "rect":\n            shape = Rectangle(*args)\n        else:\n            shape = Square(*args)\n        total += shape.area()\n    return total\n', "Сумма не округлена до двух знаков."),
   (SHAPES + 'def total_area(shapes):\n    return round(sum(s[1] ** 2 for s in shapes), 2)\n', "Площадь считается как квадрат первого числа, классы не использованы.")],
  hints("Для каждого вида фигуры есть свой класс с методом area().", "Сначала по первому элементу выберите класс и создайте объект, передав остальные элементы.", "*args собирает оставшиеся элементы списка: kind, *args = shape.", "Складывайте shape.area() для каждой фигуры.", "return round(total, 2)."),
  "Все фигуры одинаково отвечают на area(), поэтому цикл не зависит от вида фигуры; Square переиспользует Rectangle через super().",
  starter=SHAPES + "def total_area(shapes):\n    # создайте фигуры и сложите площади\n    pass\n", type="complete", tolerance=1e-9)

a3 = fn_task("a3-transactions", "Транзакции на dataclass", "Опишите `@dataclass class Transaction` с полями `title: str` и `amount: float`. Функция `summary(items)` получает список пар `[название, сумма]`, создаёт из них транзакции и возвращает список `[итого, название самой крупной по модулю суммы]`. Для пустого списка верните `[0, None]`.\n\nПример: `summary([[\"кофе\", -150], [\"зарплата\", 5000], [\"такси\", -400]])` → `[4450, \"зарплата\"]`.",
  "summary", "from dataclasses import dataclass\n\n\n@dataclass\nclass Transaction:\n    title: str\n    amount: float\n\n\ndef summary(items):\n    transactions = [Transaction(title, amount) for title, amount in items]\n    if not transactions:\n        return [0, None]\n    biggest = max(transactions, key=lambda t: abs(t.amount))\n    return [sum(t.amount for t in transactions), biggest.title]\n",
  [[[["кофе", -150], ["зарплата", 5000], ["такси", -400]]], [[]], ([[["долг", -900], ["аванс", 300]]], True), ([[["а", 1]]], True), ([[["р", 10], ["с", -10]]], True)],
  [("from dataclasses import dataclass\n\n\n@dataclass\nclass Transaction:\n    title: str\n    amount: float\n\n\ndef summary(items):\n    transactions = [Transaction(title, amount) for title, amount in items]\n    if not transactions:\n        return [0, None]\n    biggest = max(transactions, key=lambda t: t.amount)\n    return [sum(t.amount for t in transactions), biggest.title]\n", "Крупнейшая сумма выбрана без модуля: большой расход не учтён."),
   ("from dataclasses import dataclass\n\n\n@dataclass\nclass Transaction:\n    title: str\n    amount: float\n\n\ndef summary(items):\n    transactions = [Transaction(title, amount) for title, amount in items]\n    biggest = max(transactions, key=lambda t: abs(t.amount))\n    return [sum(t.amount for t in transactions), biggest.title]\n", "Для пустого списка max вызывает ошибку.")],
  hints("Сначала превратите пары в объекты Transaction.", "Декоратор @dataclass сам создаст __init__ по полям с типами.", "Итого — сумма атрибутов amount.", "Самая крупная по модулю: max(..., key=lambda t: abs(t.amount)).", "Не забудьте обработать пустой список заранее."),
  "dataclass убирает шаблонный код; max с key по модулю суммы выбирает самую крупную операцию независимо от знака.")

a4 = predict_task("a4-super", "Цепочка super", 'class A:\n    def hello(self):\n        return "A"\n\nclass B(A):\n    def hello(self):\n        return "B" + super().hello()\n\nclass C(B):\n    pass\n\nprint(C().hello(), isinstance(C(), A), isinstance(A(), B))\n',
  [("B True True\n", "Метод B вызывает super().hello() и добавляет «A»; а объект A не является B."),
   ("BA True True\n", "Родитель не знает о потомках: isinstance(A(), B) — False.")],
  hints("C не переопределяет hello, значит, берётся метод B.", "Метод B возвращает «B» плюс результат родителя.", "Родитель A возвращает «A».", "isinstance(C(), A): C наследует от B, а B — от A.", "isinstance(A(), B): объект родителя не является экземпляром потомка."),
  "Поиск метода идёт вверх по цепочке C → B → A. Объект потомка является экземпляром родителя, но не наоборот.")

a5 = fn_task("a5-fix-super", "Забытый super", "Класс `Student` не вызывает `__init__` родителя, поэтому `card(name, school)` падает с `AttributeError`. Исправьте класс; `card` возвращает строку вида `Аня (Гимназия 5)`.",
  "card", 'class Person:\n    def __init__(self, name):\n        self.name = name\n\n\nclass Student(Person):\n    def __init__(self, name, school):\n        super().__init__(name)\n        self.school = school\n\n\ndef card(name, school):\n    s = Student(name, school)\n    return f"{s.name} ({s.school})"\n',
  [["Аня", "Гимназия 5"], ["Борис", "Лицей"], (["Вера", "Школа 1"], True), (["Ёж", "Н"], True)],
  [('class Person:\n    def __init__(self, name):\n        self.name = name\n\n\nclass Student(Person):\n    def __init__(self, name, school):\n        super().__init__(school)\n        self.school = school\n\n\ndef card(name, school):\n    s = Student(name, school)\n    return f"{s.name} ({s.school})"\n', "Родителю передана школа вместо имени.")],
  hints("Атрибут name создаёт конструктор родителя.", "Если у потомка свой __init__, родительский не вызывается автоматически.", "Родителя вызывают через функцию super().", "Вызов должен передать имя.", "super().__init__(name) — первой строкой в __init__ потомка."),
  "Без вызова super().__init__(name) атрибут name не создаётся, а при обращении к s.name возникает AttributeError.",
  type="fix", starter='class Person:\n    def __init__(self, name):\n        self.name = name\n\n\nclass Student(Person):\n    def __init__(self, name, school):\n        self.school = school\n\n\ndef card(name, school):\n    s = Student(name, school)\n    return f"{s.name} ({s.school})"\n')

mistakes = [
 {"mistake": "Не вызывают super().__init__() в конструкторе потомка", "fix": "Вызывайте init родителя первой строкой.", "errorType": "AttributeError"},
 {"mistake": "Строят глубокие цепочки наследования ради повторного использования кода", "fix": "Если связь не «является», рассмотрите композицию: объект внутри объекта."},
 {"mistake": "Проверяют тип через type(x) == Dog", "fix": "Используйте isinstance(x, Dog): он учитывает потомков."},
 {"mistake": "Забывают про типы в dataclass", "fix": "Поля dataclass объявляются с аннотацией: title: str."}]

finish("py-21-inheritance", "Наследование и dataclass", "Создавать классы-потомки, переопределять методы, пользоваться super и dataclass.",
  {"python.oop.inheritance": "Наследование", "python.oop.polymorphism": "Полиморфизм", "python.oop.dataclass": "Dataclass"},
  ["py-20-classes"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="python-core")

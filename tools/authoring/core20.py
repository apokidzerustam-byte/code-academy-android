from lib import *

begin()
scenes = [
 S("intro", "Объекты: данные и поведение вместе", """
  До сих пор данные у нас лежали отдельно, а функции отдельно. Но в реальном мире вещи объединяют и то, и другое. У банковского
  счёта есть баланс — это данные, и есть действия: пополнить, снять — это поведение. Объектно-ориентированное программирование
  позволяет описать такую вещь один раз в виде класса, а потом создавать сколько угодно её экземпляров. Класс — это чертёж,
  а объект — построенный по нему дом. У всех домов один чертёж, но у каждого свои жильцы.""",
  nt("**Класс** — чертёж · **объект** — экземпляр класса · **атрибуты** — данные · **методы** — действия", at="Класс — это")),
 S("class", "Первый класс", """
  Класс объявляется словом class и именем с большой буквы. Внутри особый метод init, который вызывается при создании
  объекта и заполняет его начальные данные. Первый параметр любого метода называется self — это сам объект, с которым
  работаем. Через self записывают атрибуты: self точка name. Создадим двух студентов. Каждый хранит свои собственные данные,
  и изменение одного никак не влияет на другого.""",
  clr(), t("class Student:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n\n", at="Класс объявляется"),
  t('anna = Student("Аня", 20)\nboris = Student("Борис", 22)\n', at="Создадим двух"),
  t("anna.age = 21\nprint(anna.name, anna.age)\nprint(boris.name, boris.age)\n", at="Каждый хранит"), run("изменение одного")),
 S("methods", "Методы", """
  Методы — это функции внутри класса. Они всегда принимают self первым параметром и получают доступ ко всем атрибутам объекта.
  Добавим студенту оценки и метод для вычисления среднего балла. Вызываем метод через точку у конкретного объекта, а self
  подставляется автоматически, о нём при вызове думать не нужно. Один и тот же метод у разных объектов даёт разные
  результаты, потому что работает с их собственными данными.""",
  clr(), t("class Student:\n    def __init__(self, name):\n        self.name = name\n        self.marks = []\n\n", at="Добавим студенту"),
  t("    def add_mark(self, mark):\n        self.marks.append(mark)\n\n    def average(self):\n        return sum(self.marks) / len(self.marks)\n\n", at="Добавим студенту"),
  t('anna = Student("Аня")\nanna.add_mark(5)\nanna.add_mark(4)\nprint(anna.average())\n', at="Вызываем метод"), run("Один и тот же")),
 S("str", "Красивый вывод: __str__", """
  Если напечатать объект, Python покажет что-то вроде «объект класса Student в такой-то ячейке памяти». Это бесполезно. Чтобы
  объект умел красиво представлять себя, определяют метод str с двойными подчёркиваниями по бокам. Он возвращает строку, и
  именно её увидит print. Такие методы с двойными подчёркиваниями называют специальными: Python вызывает их сам, в нужный
  момент.""",
  clr(), t('class Student:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n\n', at="Если напечатать"),
  t('    def __str__(self):\n        return f"{self.name}, {self.age} лет"\n\n', at="Чтобы"),
  t('print(Student("Аня", 20))\n', at="именно её"), run("Такие методы")),
 S("account", "Пример: банковский счёт", """
  Соберём всё вместе в классе счёта. Баланс хранится в атрибуте, а пополнение и снятие — методы. Снять больше, чем есть на счёте,
  нельзя: в этом случае метод вызывает исключение. Так класс сам защищает свои данные от неверных действий, и ошибки не
  размазываются по всей программе. Это тот самый учёт расходов, который мы будем развивать в проекте курса.""",
  clr(), t("class Account:\n    def __init__(self, balance=0):\n        self.balance = balance\n\n", at="Соберём"),
  t("    def deposit(self, amount):\n        self.balance += amount\n\n", at="Баланс хранится"),
  t("    def withdraw(self, amount):\n        if amount > self.balance:\n            raise ValueError(\"недостаточно средств\")\n        self.balance -= amount\n\n", at="Снять больше"),
  t("acc = Account(100)\nacc.deposit(50)\nacc.withdraw(30)\nprint(acc.balance)\n", at="Так класс"),
  t("try:\n    acc.withdraw(500)\nexcept ValueError as e:\n    print(\"ошибка:\", e)\n", at="Это тот самый"), run("Это тот самый")),
 S("convention", "Соглашения об именах", """
  В Python нет настоящих приватных атрибутов, но есть договорённость: имя, начинающееся с подчёркивания, считается внутренним, и
  снаружи его трогать не принято. Изменять баланс нужно через методы, а не присваивая его напрямую, иначе обходятся все
  проверки. Имена классов пишут с большой буквы в стиле «каждое слово с большой», а имена методов и атрибутов — строчными
  буквами с подчёркиваниями.""",
  nt("`_internal` — «не трогать снаружи» · `ClassName` · `method_name` · `attribute_name`", at="В Python нет")),
 S("summary", "Итог", """
  Подведём итог. Класс описывает чертёж: какие данные хранит объект и что умеет делать. Метод init создаёт начальное
  состояние, self — это сам объект. У каждого экземпляра свои атрибуты. Методы работают с данными объекта, а специальный метод
  str отвечает за красивый вывод. Класс может защищать свои данные, проверяя действия и вызывая исключения. В следующем уроке
  разберём наследование: как создавать классы на основе других.""",
  nt("`class` · `__init__(self, …)` · `self.attr` · методы · `__str__`", at="Подведём итог")),
]

notes = """
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
"""

a1 = fn_task("a1-rectangle", "Класс «Прямоугольник»", "Напишите класс `Rectangle` с конструктором `Rectangle(width, height)` и методами `area()` и `perimeter()`. Затем функцию `rect_info(width, height)`, которая создаёт прямоугольник и возвращает список `[площадь, периметр]`.\n\nПример: `rect_info(3, 4)` → `[12, 14]`.",
  "rect_info", "class Rectangle:\n    def __init__(self, width, height):\n        self.width = width\n        self.height = height\n\n    def area(self):\n        return self.width * self.height\n\n    def perimeter(self):\n        return 2 * (self.width + self.height)\n\n\ndef rect_info(width, height):\n    r = Rectangle(width, height)\n    return [r.area(), r.perimeter()]\n",
  [[3, 4], [1, 1], ([10, 2], True), ([0, 5], True), ([2.5, 4], True)],
  [("class Rectangle:\n    def __init__(self, width, height):\n        self.width = width\n        self.height = height\n\n    def area(self):\n        return self.width * self.height\n\n    def perimeter(self):\n        return self.width + self.height\n\n\ndef rect_info(width, height):\n    r = Rectangle(width, height)\n    return [r.area(), r.perimeter()]\n", "Периметр посчитан как сумма двух сторон вместо удвоенной суммы."),
   ("class Rectangle:\n    def __init__(self, width, height):\n        self.width = width\n        self.height = height\n\n    def area(self):\n        return self.width + self.height\n\n    def perimeter(self):\n        return 2 * (self.width + self.height)\n\n\ndef rect_info(width, height):\n    r = Rectangle(width, height)\n    return [r.area(), r.perimeter()]\n", "Площадь посчитана как сумма сторон."),
   ("class Rectangle:\n    def __init__(self, width, height):\n        self.width = width\n        self.height = height\n\n    def area(self):\n        return self.width * self.height\n\n    def perimeter(self):\n        return 2 * (self.width + self.height)\n\n\ndef rect_info(width, height):\n    r = Rectangle(width, height)\n    return [r.perimeter(), r.area()]\n", "Значения возвращены в обратном порядке.")],
  hints("Класс хранит ширину и высоту, а методы вычисляют по ним результаты.", "В __init__ сохраните параметры в атрибуты self.width и self.height.", "Методы area и perimeter принимают только self и читают атрибуты.", "Площадь — произведение сторон, периметр — удвоенная сумма.", "rect_info создаёт Rectangle(width, height) и возвращает [r.area(), r.perimeter()]."),
  "Методы читают данные объекта через self. Функция rect_info — обёртка, которая создаёт экземпляр и использует его методы.")

a2 = fn_task("a2-account", "Класс «Счёт»", "Напишите класс `Account` (начальный баланс 0) с методами `deposit(amount)` и `withdraw(amount)`; снятие больше баланса вызывает `ValueError`. Затем функцию `run(operations)`: `operations` — список пар `[\"d\" или \"w\", сумма]`. Верните итоговый баланс, а если какая-то операция вызвала ошибку — строку `\"ошибка\"`.\n\nПример: `run([[\"d\", 100], [\"w\", 30]])` → `70`, `run([[\"w\", 5]])` → `\"ошибка\"`.",
  "run", "class Account:\n    def __init__(self, balance=0):\n        self.balance = balance\n\n    def deposit(self, amount):\n        self.balance += amount\n\n    def withdraw(self, amount):\n        if amount > self.balance:\n            raise ValueError(\"недостаточно средств\")\n        self.balance -= amount\n\n\ndef run(operations):\n    acc = Account()\n    try:\n        for kind, amount in operations:\n            if kind == \"d\":\n                acc.deposit(amount)\n            else:\n                acc.withdraw(amount)\n    except ValueError:\n        return \"ошибка\"\n    return acc.balance\n",
  [[[["d", 100], ["w", 30]]], [[["w", 5]]], ([[]], True), ([[["d", 50], ["w", 50]]], True), ([[["d", 10], ["w", 11]]], True), ([[["d", 5], ["d", 5], ["w", 3]]], True)],
  [("class Account:\n    def __init__(self, balance=0):\n        self.balance = balance\n\n    def deposit(self, amount):\n        self.balance += amount\n\n    def withdraw(self, amount):\n        self.balance -= amount\n\n\ndef run(operations):\n    acc = Account()\n    try:\n        for kind, amount in operations:\n            if kind == \"d\":\n                acc.deposit(amount)\n            else:\n                acc.withdraw(amount)\n    except ValueError:\n        return \"ошибка\"\n    return acc.balance\n", "Нет проверки: баланс уходит в минус, ошибка не возникает."),
   ("class Account:\n    def __init__(self, balance=0):\n        self.balance = balance\n\n    def deposit(self, amount):\n        self.balance += amount\n\n    def withdraw(self, amount):\n        if amount >= self.balance:\n            raise ValueError(\"недостаточно средств\")\n        self.balance -= amount\n\n\ndef run(operations):\n    acc = Account()\n    try:\n        for kind, amount in operations:\n            if kind == \"d\":\n                acc.deposit(amount)\n            else:\n                acc.withdraw(amount)\n    except ValueError:\n        return \"ошибка\"\n    return acc.balance\n", "Снять ровно весь баланс разрешено, а проверка с >= это запрещает.")],
  hints("Состояние счёта — это баланс, а операции — методы.", "В __init__ создайте self.balance.", "В withdraw сравните сумму с балансом и вызовите ValueError, если денег не хватает.", "В run создайте счёт и примените операции в цикле; ValueError перехватите.", "Если исключение возникло — верните «ошибка», иначе acc.balance."),
  "Класс сам проверяет допустимость операций и сообщает о нарушении исключением; функция run только применяет операции и обрабатывает ошибку.")

a3 = stdout_task("a3-todo", "Список дел", "Реализуйте класс `Todo` с методами `add(text)`, `done(index)` (отметить дело с номером `index`, нумерация с 0) и `pending()` (список невыполненных дел). Программа читает `n` команд: `add текст` или `done номер`, а в конце выводит невыполненные дела, каждое на новой строке, или `все дела сделаны`.\n\nВвод:\n```\n3\nadd хлеб\nadd молоко\ndone 0\n```\nВывод:\n```\nмолоко\n```",
  'class Todo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, text):\n        self.items.append([text, False])\n\n    def done(self, index):\n        self.items[index][1] = True\n\n    def pending(self):\n        return [text for text, ok in self.items if not ok]\n\n\ntodo = Todo()\nfor _ in range(int(input())):\n    command, arg = input().split(" ", 1)\n    if command == "add":\n        todo.add(arg)\n    else:\n        todo.done(int(arg))\nrest = todo.pending()\nprint("\\n".join(rest) if rest else "все дела сделаны")\n',
  ["3\nadd хлеб\nadd молоко\ndone 0\n", ("2\nadd а\ndone 0\n", True), ("0\n", True), ("4\nadd один\nadd два\nadd три\ndone 1\n", True), ("5\nadd а\nadd б\nadd в\ndone 0\ndone 1\n", True)],
  [('class Todo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, text):\n        self.items.append([text, False])\n\n    def done(self, index):\n        self.items.pop(index)\n\n    def pending(self):\n        return [text for text, ok in self.items if not ok]\n\n\ntodo = Todo()\nfor _ in range(int(input())):\n    command, arg = input().split(" ", 1)\n    if command == "add":\n        todo.add(arg)\n    else:\n        todo.done(int(arg))\nrest = todo.pending()\nprint("\\n".join(rest) if rest else "все дела сделаны")\n', "done удаляет дело, поэтому номера следующих дел сдвигаются."),
   ('class Todo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, text):\n        self.items.append([text, False])\n\n    def done(self, index):\n        self.items[index][1] = True\n\n    def pending(self):\n        return [text for text, ok in self.items if not ok]\n\n\ntodo = Todo()\nfor _ in range(int(input())):\n    command, arg = input().split(" ", 1)\n    if command == "add":\n        todo.add(arg)\n    else:\n        todo.done(int(arg))\nprint("\\n".join(todo.pending()))\n', "Если все дела сделаны, выводится пустая строка вместо сообщения.")],
  hints("Состояние — список дел; у каждого дела есть признак «сделано».", "Храните пары [текст, сделано] в атрибуте items.", "done меняет признак у дела с номером index, но не удаляет его.", "pending возвращает тексты дел, у которых признак ложен.", "В конце: если список пуст — сообщение, иначе дела через перевод строки."),
  "Класс скрывает устройство списка: программа вызывает add, done и pending и не думает о парах внутри.")

a4 = predict_task("a4-objects", "Кто на кого ссылается", 'class Box:\n    def __init__(self):\n        self.items = []\n\n    def add(self, x):\n        self.items.append(x)\n        return self\n\na = Box()\nb = Box()\na.add(1).add(2)\nb.add(3)\nc = a\nc.add(4)\nprint(a.items, b.items, c is a)\n',
  [("[1, 2] [3] False\n", "Переменная c — не копия, а вторая ссылка на тот же объект a."),
   ("[1, 2, 4] [3, 1, 2, 4] True\n", "У каждого объекта свой список items: b не связан с a.")],
  hints("Выполняйте строки по порядку.", "a и b — два разных объекта, у каждого свой список.", "a.add(1).add(2): метод возвращает self, поэтому вызовы можно цепочкой.", "c = a — не копирование, а вторая ссылка на тот же объект.", "Изменение через c видно и через a."),
  "Присваивание объекта создаёт ссылку, а не копию. Поэтому c.add(4) меняет тот же объект, на который указывает a.")

a5 = fn_task("a5-fix-self", "Исправь класс", "В классе `Counter` забыты `self`, и `counter_after(n)` падает с `TypeError`. Исправьте класс. Функция `counter_after(n)` создаёт счётчик, вызывает `increment()` ровно `n` раз и возвращает значение.",
  "counter_after", "class Counter:\n    def __init__(self):\n        self.value = 0\n\n    def increment(self):\n        self.value += 1\n\n\ndef counter_after(n):\n    c = Counter()\n    for _ in range(n):\n        c.increment()\n    return c.value\n",
  [[3], [0], ([10], True), ([1], True)],
  [("class Counter:\n    def __init__(self):\n        self.value = 0\n\n    def increment(self):\n        self.value += 2\n\n\ndef counter_after(n):\n    c = Counter()\n    for _ in range(n):\n        c.increment()\n    return c.value\n", "Шаг счётчика равен 2, а не 1."),
   ("class Counter:\n    def __init__(self):\n        self.value = 1\n\n    def increment(self):\n        self.value += 1\n\n\ndef counter_after(n):\n    c = Counter()\n    for _ in range(n):\n        c.increment()\n    return c.value\n", "Начальное значение 1, а не 0.")],
  hints("Сообщение TypeError говорит, что методу передан лишний аргумент.", "Каждый метод класса получает объект первым параметром.", "Этот параметр принято называть self.", "Добавьте self в объявления __init__ и increment.", "def __init__(self): self.value = 0; def increment(self): self.value += 1."),
  "Python автоматически передаёт объект первым аргументом метода; параметр self принимает его. Без self вызов c.increment() передаёт на один аргумент больше, чем объявлено.",
  type="fix", starter="class Counter:\n    def __init__():\n        value = 0\n\n    def increment():\n        value += 1\n\n\ndef counter_after(n):\n    c = Counter()\n    for _ in range(n):\n        c.increment()\n    return c.value\n")

mistakes = [
 {"mistake": "Забывают self в объявлении метода", "fix": "Первый параметр любого метода — self.", "errorType": "TypeError"},
 {"mistake": "Пишут value вместо self.value внутри метода", "fix": "Атрибуты объекта доступны только через self.", "errorType": "NameError"},
 {"mistake": "Думают, что b = a делает копию объекта", "fix": "Присваивание создаёт вторую ссылку на тот же объект."},
 {"mistake": "Меняют баланс напрямую, обходя проверки", "fix": "Меняйте состояние через методы класса."}]

finish("py-20-classes", "Классы и объекты", "Объявлять классы с атрибутами и методами, создавать объекты и защищать их данные проверками.",
  {"python.oop.class": "Классы и объекты", "python.oop.methods": "Методы и self", "python.oop.str": "Специальный метод __str__"},
  ["py-19-modules"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="python-core")

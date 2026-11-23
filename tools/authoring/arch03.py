from lib import *

begin()
scenes = [
 S("intro", "Зависимости", """
  Если функция или класс использует что-то внешнее, это его зависимость: хранилище, текущее время, отправка сообщений. Есть два
  способа получить зависимость. Можно создать её внутри, и тогда код намертво связан с конкретной реализацией. Или принять
  снаружи, как параметр: тогда реализацию можно подменить. Этот приём называется внедрением зависимостей. Он нужен
  не для красоты, а чтобы код можно было проверять и менять.""",
  nt("**Внедрение зависимостей:** не создавать внутри, а принимать снаружи", at="Или принять")),
 S("hard", "Зависимость зашита внутрь", """
  Посмотрим на сервис, который сам создаёт хранилище. Работать он будет, но проверить его на других данных нельзя, а заменить
  хранилище придётся правкой самого сервиса. К тому же зависимость от времени делает результат непредсказуемым: функция
  проверки просрочки, которая вызывает текущую дату, вернёт разное в разные дни, и тест на неё написать трудно.""",
  clr(), t("class ListRepo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, item):\n        self.items.append(item)\n\n\nclass HardService:\n    def __init__(self):\n        self.repo = ListRepo()\n\n    def add(self, item):\n        self.repo.add(item)\n\n\n", at="Посмотрим"),
  t("service = HardService()\nservice.add(\"молоко\")\nprint(service.repo.items)\n", at="Работать"), run("К тому же")),
 S("inject", "Принимаем снаружи", """
  Исправим это одной строкой: хранилище передаётся в конструктор. Теперь сервис не знает, какое именно хранилище ему дали, лишь бы
  у него был нужный метод. Для проверки можно подставить поддельное хранилище, которое просто запоминает вызовы. Тест
  становится быстрым и не требует ни файлов, ни базы данных.""",
  clr(), t("class Service:\n    def __init__(self, repo):\n        self.repo = repo\n\n    def add(self, item):\n        self.repo.add(item.strip().lower())\n\n\nclass FakeRepo:\n    def __init__(self):\n        self.saved = []\n\n    def add(self, item):\n        self.saved.append(item)\n\n\n", at="Исправим"),
  t("fake = FakeRepo()\nService(fake).add(\"  Молоко \")\nprint(fake.saved)\n", at="Для проверки"), run("Тест")),
 S("clock", "Время как зависимость", """
  Время — типичная скрытая зависимость. Если функции нужна сегодняшняя дата, не вызывайте её внутри, а принимайте параметром.
  Тогда функция чистая: в тесте мы передаём любую дату и получаем предсказуемый результат. А настоящую дату подставляет
  самый верхний слой программы. Проверим просрочку задач для трёх разных «сегодня».""",
  clr(), t("def is_overdue(due_day, today):\n    return today > due_day\n\n\n", at="Тогда"),
  t("for today in (9, 10, 11):\n    print(today, is_overdue(10, today))\n", at="Проверим"), run("Проверим")),
 S("root", "Где всё собирается", """
  Кто-то всё же должен создать настоящее хранилище и передать его сервису. Это делают в одном месте, которое называют
  корнем композиции: обычно в начале главной функции. Только там программа знает, какие реализации выбраны. Остальные части
  принимают зависимости и не заботятся об их происхождении. Заменить базу данных на файл теперь можно одной строкой в корне.""",
  nt("Корень композиции: `main()` создаёт реализации и передаёт их внутрь", at="Кто-то")),
 S("summary", "Итог", """
  Подведём итог. Зависимость — это то, что код использует снаружи. Принимайте зависимости параметрами, а не создавайте внутри.
  Так вы сможете подставлять поддельные реализации в проверках и менять настоящие без правок логики. Время, случайные
  числа и обращения к сети — типичные зависимости, которые стоит передавать явно. Собирайте всё в корне композиции.""",
  nt("хранилище · время · случайность · сеть → передавать параметрами", at="Время")),
]

notes = """
# Внедрение зависимостей

```python
class Service:
    def __init__(self, repo):
        self.repo = repo

    def add(self, item):
        self.repo.add(item.strip().lower())


class FakeRepo:
    def __init__(self):
        self.saved = []

    def add(self, item):
        self.saved.append(item)


fake = FakeRepo()
Service(fake).add("  Молоко ")
print(fake.saved)
```

## Правила

1. Не создавайте зависимость внутри — принимайте снаружи.
2. Для проверок подставляйте поддельные реализации.
3. Время и случайность — тоже зависимости: `today` параметром.
4. Всё собирается в одном месте — корне композиции (`main`).
"""

a1 = predict_task("a1-fake", "Поддельное хранилище",
  'class Service:\n    def __init__(self, repo):\n        self.repo = repo\n\n    def add(self, name):\n        if name.strip():\n            self.repo.add(name.strip().title())\n\n\nclass FakeRepo:\n    def __init__(self):\n        self.saved = []\n\n    def add(self, item):\n        self.saved.append(item)\n\n\nfake = FakeRepo()\nservice = Service(fake)\nfor name in ["анна", "  ", " борис  ", ""]:\n    service.add(name)\nprint(fake.saved)\nprint(len(fake.saved))\n',
  [("['Анна', 'Борис']\n4", "Пустые имена не сохраняются: всего два."), ("['анна', 'борис']\n2", "Имена приводятся к виду с заглавной буквы.")],
  hints("Сервис пропускает пустые имена.", "Для остальных вызывает strip и title.", "«анна» → «Анна», « борис  » → «Борис».", "Пробельная и пустая строки не сохраняются.", "Сохранено два имени."),
  "Поддельное хранилище запоминает вызовы, поэтому по его содержимому видно, что именно сделал сервис.")

a2 = fn_task("a2-overdue", "Просроченные задачи",
  "Напишите `overdue(tasks, today)`: `tasks` — список пар `[название, срок]` (срок и `today` — номера дней). Верните названия задач, срок которых **строго меньше** `today`, отсортированные по алфавиту. Текущую дату вы не вызываете — она приходит параметром.",
  "overdue", "def overdue(tasks, today):\n    return sorted(name for name, due in tasks if due < today)\n",
  [[[["сдать отчёт", 5], ["позвонить", 12], ["оплатить", 8]], 10], [[], 3], ([[["а", 5]], 5], True), ([[["б", 4], ["а", 1]], 9], True), ([[["x", 10]], 9], True)],
  [("def overdue(tasks, today):\n    return sorted(name for name, due in tasks if due <= today)\n", "Задача со сроком «сегодня» ещё не просрочена."),
   ("def overdue(tasks, today):\n    return [name for name, due in tasks if due < today]\n", "Результат не отсортирован.")],
  hints("Для каждой задачи сравните срок с today.", "Просрочена — срок меньше сегодняшнего дня.", "Из пар нужны только названия.", "Отсортируйте результат.", "Строгое сравнение: срок равен today — не просрочено."),
  "Функция зависит только от аргументов: подставив любое `today`, мы получаем предсказуемый результат.")

a3 = stdout_task("a3-inject", "Внедрите хранилище",
  "Сервис сам создаёт список внутри, поэтому программа падает при выборе хранилища. Исправьте: пусть `Service` **принимает** хранилище в конструкторе и вызывает его методы. Хранилище выбирается входной строкой: `list` — обычный порядок, `sorted` — по возрастанию.",
  "class ListRepo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, item):\n        self.items.append(item)\n\n    def all(self):\n        return list(self.items)\n\n\nclass SortedRepo(ListRepo):\n    def all(self):\n        return sorted(self.items)\n\n\nclass Service:\n    def __init__(self, repo):\n        self.repo = repo\n\n    def add(self, value):\n        self.repo.add(value)\n\n    def show(self):\n        print(self.repo.all())\n\n\nrepo = {\"list\": ListRepo, \"sorted\": SortedRepo}[input().strip()]()\nservice = Service(repo)\nfor v in (3, 1, 2):\n    service.add(v)\nservice.show()\n",
  ["list\n", ("sorted\n", True)],
  [("class ListRepo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, item):\n        self.items.append(item)\n\n    def all(self):\n        return list(self.items)\n\n\nclass SortedRepo(ListRepo):\n    def all(self):\n        return sorted(self.items)\n\n\nclass Service:\n    def __init__(self, repo):\n        self.repo = ListRepo()\n\n    def add(self, value):\n        self.repo.add(value)\n\n    def show(self):\n        print(self.repo.all())\n\n\nrepo = {\"list\": ListRepo, \"sorted\": SortedRepo}[input().strip()]()\nservice = Service(repo)\nfor v in (3, 1, 2):\n    service.add(v)\nservice.show()\n", "Переданное хранилище игнорируется: всегда используется список.")],
  hints("Запустите программу: сообщение об ошибке укажет на создание Service.", "Конструктор Service не принимает хранилище.", "Добавьте параметр repo в __init__.", "Сохраните его в self.repo.", "Остальные методы уже обращаются к self.repo."),
  "Хранилище, переданное в конструктор, определяет поведение сервиса: подменив его, мы поменяли результат без правок логики.",
  type="fix", starter="class ListRepo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, item):\n        self.items.append(item)\n\n    def all(self):\n        return list(self.items)\n\n\nclass SortedRepo(ListRepo):\n    def all(self):\n        return sorted(self.items)\n\n\nclass Service:\n    def __init__(self):\n        self.repo = ListRepo()\n\n    def add(self, value):\n        self.repo.add(value)\n\n    def show(self):\n        print(self.repo.all())\n\n\nrepo = {\"list\": ListRepo, \"sorted\": SortedRepo}[input().strip()]()\nservice = Service(repo)\nfor v in (3, 1, 2):\n    service.add(v)\nservice.show()\n")

a4 = fn_task("a4-greeting", "Приветствие по времени",
  "Напишите `greeting(hour)`: при `hour` от 5 до 11 включительно — `Доброе утро`, от 12 до 17 — `Добрый день`, от 18 до 22 — `Добрый вечер`, иначе — `Доброй ночи`. Час передаётся параметром, а не берётся из часов компьютера.",
  "greeting", "def greeting(hour):\n    if 5 <= hour <= 11:\n        return \"Доброе утро\"\n    if 12 <= hour <= 17:\n        return \"Добрый день\"\n    if 18 <= hour <= 22:\n        return \"Добрый вечер\"\n    return \"Доброй ночи\"\n",
  [[8], [20], ([4], True), ([5], True), ([11], True), ([12], True), ([17], True), ([18], True), ([22], True), ([23], True), ([0], True)],
  [("def greeting(hour):\n    if 5 < hour < 11:\n        return \"Доброе утро\"\n    if 12 <= hour <= 17:\n        return \"Добрый день\"\n    if 18 <= hour <= 22:\n        return \"Добрый вечер\"\n    return \"Доброй ночи\"\n", "Границы утра исключены.")],
  hints("Четыре диапазона часов.", "Границы включительно.", "Проверяйте в порядке возрастания.", "Всё остальное — ночь.", "Цепочка условий с return в каждой ветке."),
  "Зависимость от времени вынесена в параметр: функцию можно проверить на любом часе, включая границы.")

a5 = predict_task("a5-sender", "Отправитель как параметр",
  'def notify(users, send):\n    for user in users:\n        send(f"Привет, {user}!")\n\n\nsent = []\nnotify(["Аня", "Боря"], sent.append)\nprint(sent)\nnotify([], print)\nnotify(["Вера"], print)\nprint(len(sent))\n',
  [("['Привет, Аня!', 'Привет, Боря!']\nПривет, Вера!\n3", "Отправка через print не добавляет сообщения в список: их по-прежнему два."), ("['Привет, Аня!', 'Привет, Боря!']\n2", "Третий вызов печатает приветствие для Веры.")],
  hints("send — любая функция: sent.append или print.", "Первый вызов добавляет два сообщения в список sent.", "Второй вызов — пустой список, ничего не происходит.", "Третий вызов печатает «Привет, Вера!».", "Список sent при этом не меняется: в нём два элемента."),
  "Функция принимает способ отправки параметром: в проверке это append в список, в программе — print или реальная отправка.")

mistakes = [
 {"mistake": "Создают хранилище или соединение внутри логики", "fix": "Принимайте его параметром."},
 {"mistake": "Вызывают текущее время внутри функций", "fix": "Передавайте дату или час аргументом."},
 {"mistake": "Подменяют зависимости «магически» в тестах", "fix": "Явная передача проще и надёжнее."},
 {"mistake": "Передают зависимость слишком глубоко через много слоёв", "fix": "Собирайте объекты в корне композиции."}]

finish("arch-03-dependencies", "Внедрение зависимостей", "Принимать зависимости снаружи, подменять их в проверках и собирать программу в корне композиции.",
  {"arch.di": "Внедрение зависимостей", "arch.fake": "Поддельные реализации", "arch.root": "Корень композиции"},
  ["arch-02-layers"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="architecture")

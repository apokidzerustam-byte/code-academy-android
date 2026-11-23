from lib import *

LAYERS = '''class ListRepo:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def all(self):
        return list(self.items)


class FinanceService:
    def __init__(self, repo):
        self.repo = repo

    def add(self, kind, amount):
        if kind not in ("income", "expense"):
            raise ValueError("неизвестный тип")
        if amount <= 0:
            raise ValueError("сумма должна быть положительной")
        self.repo.add((kind, amount))

    def balance(self):
        return sum(a if k == "income" else -a for k, a in self.repo.all())


'''

begin()
scenes = [
 S("intro", "Слои приложения", """
  Когда программа вырастает, функций становится слишком много, чтобы держать их в голове. Тогда их группируют в слои. Обычно
  выделяют три. Верхний слой — интерфейс: то, что видит и делает пользователь. Средний — логика: правила предметной
  области, например что нельзя потратить отрицательную сумму. Нижний — данные: хранение в списке, файле или базе. Главное
  правило: верхние слои знают о нижних, но не наоборот, и интерфейс не лезет напрямую в хранилище.""",
  nt("Интерфейс → логика → данные · зависимости направлены **вниз**", at="Главное правило")),
 S("data", "Слой данных", """
  Начнём снизу. Хранилище, которое по-английски называют репозиторием, умеет только сохранять и отдавать записи. Никаких
  правил, никаких проверок. Наше хранилище держит записи в списке в памяти, но снаружи это неважно: позже его можно
  заменить файлом или базой данных, и остальная программа ничего не заметит.""",
  clr(), t("class ListRepo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, item):\n        self.items.append(item)\n\n    def all(self):\n        return list(self.items)\n\n\n", at="Начнём снизу"),
  t("repo = ListRepo()\nrepo.add((\"income\", 1000))\nprint(repo.all())\n", at="Наше хранилище"), run("позже")),
 S("service", "Слой логики", """
  Над хранилищем строится сервис. Он знает правила: допустимые типы операций, положительные суммы, как считать баланс. Сервис
  получает хранилище при создании и обращается к нему только через два метода. Если правило нарушено, он возбуждает
  ошибку и ничего не сохраняет. Всё, что касается денег и их смысла, живёт здесь, а не в интерфейсе.""",
  clr(), t(LAYERS, at="Над хранилищем"),
  t("service = FinanceService(ListRepo())\nservice.add(\"income\", 1000)\nservice.add(\"expense\", 300)\nprint(service.balance())\ntry:\n    service.add(\"expense\", -5)\nexcept ValueError as e:\n    print(\"ошибка:\", e)\n", at="Если правило"), run("Всё, что касается")),
 S("ui", "Слой интерфейса", """
  Интерфейс принимает команды пользователя, вызывает сервис и показывает результат. Он не считает баланс сам и не трогает
  список записей. Здесь это цикл, читающий команды из заготовленного списка. Обратите внимание, что при ошибке
  интерфейс просто показывает сообщение, а решение о том, что ошибка — это логика сервиса.""",
  clr(), t(LAYERS, at="Интерфейс принимает"),
  t('service = FinanceService(ListRepo())\ncommands = ["income 500", "expense 120", "balance", "expense 0"]\nfor command in commands:\n    parts = command.split()\n    try:\n        if parts[0] == "balance":\n            print("баланс:", service.balance())\n        else:\n            service.add(parts[0], int(parts[1]))\n    except ValueError as e:\n        print("ошибка:", e)\n', at="Здесь это"), run("Обратите внимание")),
 S("patterns", "MVC, MVVM, чистая архитектура", """
  У слоёв есть известные названия. В схеме модель, представление и контроллер — MVC — модель хранит данные и правила,
  представление рисует, а контроллер связывает их. В Android чаще используют схему MVVM: представление наблюдает за
  моделью представления, а та работает с данными. В чистой архитектуре зависимости направлены к центру: логика ничего не знает
  ни об интерфейсе, ни о базе данных. Идея везде одна — разделить ответственности и направить зависимости.""",
  nt("**MVC:** модель — представление — контроллер · **MVVM:** View ← ViewModel ← Model · **Clean:** зависимости к центру", at="В схеме")),
 S("summary", "Итог", """
  Подведём итог. Приложение делят на интерфейс, логику и данные. Логика хранится в сервисе и не знает, как устроен интерфейс.
  Хранилище умеет лишь сохранять и отдавать. Зависимости направлены вниз, поэтому любой слой можно заменить, не ломая остальные.
  В следующем уроке разберём, как передавать зависимости и благодаря этому легко тестировать логику.""",
  nt("UI → сервис → хранилище · правила — в сервисе · хранилище заменяемо", at="Подведём итог")),
]

notes = """
# Слои приложения

```python
class ListRepo:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def all(self):
        return list(self.items)


class FinanceService:
    def __init__(self, repo):
        self.repo = repo

    def add(self, kind, amount):
        if kind not in ("income", "expense"):
            raise ValueError("неизвестный тип")
        if amount <= 0:
            raise ValueError("сумма должна быть положительной")
        self.repo.add((kind, amount))

    def balance(self):
        return sum(a if k == "income" else -a for k, a in self.repo.all())
```

## Слои

1. **Интерфейс** — ввод и вывод, никаких правил.
2. **Логика (сервис)** — правила предметной области.
3. **Данные (репозиторий)** — сохранить и отдать.

Зависимости направлены вниз. Варианты схем: MVC, MVVM, чистая архитектура.
"""

PROG = '''class ListRepo:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def all(self):
        return list(self.items)


class FinanceService:
    def __init__(self, repo):
        self.repo = repo

    def add(self, kind, amount):
{ADD}
    def balance(self):
{BAL}

service = FinanceService(ListRepo())
for _ in range(int(input())):
    parts = input().split()
    try:
        if parts[0] == "balance":
            print("баланс:", service.balance())
        else:
            service.add(parts[0], int(parts[1]))
    except ValueError as e:
        print("ошибка:", e)
'''
def prog(add, bal): return PROG.replace("{ADD}\n", add).replace("{BAL}\n", bal)
ADD_OK = '        if kind not in ("income", "expense"):\n            raise ValueError("неизвестный тип")\n        if amount <= 0:\n            raise ValueError("сумма должна быть положительной")\n        self.repo.add((kind, amount))\n'
BAL_OK = '        return sum(a if k == "income" else -a for k, a in self.repo.all())\n'

a1 = predict_task("a1-layers", "Что напечатает интерфейс",
  LAYERS + 'service = FinanceService(ListRepo())\nfor kind, amount in [("income", 100), ("expense", 30), ("gift", 10), ("expense", 0), ("expense", 20)]:\n    try:\n        service.add(kind, amount)\n    except ValueError as e:\n        print("ошибка:", e)\nprint(service.balance())\n',
  [("ошибка: неизвестный тип\nошибка: сумма должна быть положительной\n50", "Баланс: 100 − 30 − 20 = 50 — верно, но порядок сообщений другой? (проверьте внимательно)"), ("ошибка: неизвестный тип\nошибка: неизвестный тип\n50", "Для нулевой суммы выдаётся другое сообщение."), ("ошибка: неизвестный тип\nошибка: сумма должна быть положительной\n40", "Баланс считается как 100 − 30 − 20 = 50.")][1:],
  hints("Для каждой операции сервис проверяет тип, затем сумму.", "(\"gift\", 10): тип неизвестен — первая ошибка.", "(\"expense\", 0): тип верный, сумма не положительна — вторая ошибка.", "Остальные три операции сохраняются.", "Баланс: доход минус два расхода."),
  "Сервис сначала проверяет тип, потом сумму; неверные операции не сохраняются, поэтому баланс считается только по принятым.")

a2 = stdout_task("a2-service", "Допишите слой логики",
  "Интерфейс и хранилище готовы. Допишите методы `add` и `balance` сервиса: `add(kind, amount)` проверяет, что `kind` — `income` или `expense` (иначе `ValueError(\"неизвестный тип\")`) и что `amount` больше нуля (иначе `ValueError(\"сумма должна быть положительной\")`), затем сохраняет пару `(kind, amount)` в хранилище; `balance()` возвращает доходы минус расходы.",
  prog(ADD_OK, BAL_OK),
  ["5\nincome 500\nexpense 120\nbalance\nexpense 0\nbalance\n", ("3\nincome 10\nincome 20\nbalance\n", True), ("2\ngift 5\nbalance\n", True), ("3\nexpense 40\nexpense -1\nbalance\n", True)],
  [(prog('        self.repo.add((kind, amount))\n', BAL_OK), "Правила не проверяются."),
   (prog(ADD_OK, '        return sum(a for k, a in self.repo.all())\n'), "Расходы прибавляются к балансу.")],
  hints("Метод add сначала проверяет, потом сохраняет.", "Допустимые типы: income и expense.", "Нарушение правила — raise ValueError с нужным текстом.", "Сохранение — через self.repo.add.", "Баланс: доход прибавляется, расход вычитается."),
  "Все правила — в одном слое. Интерфейс лишь печатает сообщение об ошибке, а хранилище ничего не проверяет.",
  starter=prog('        pass\n', '        return 0\n'), type="complete")

a3 = fn_task("a3-validate", "Правила в одном месте",
  "Напишите `validate(kind, amount)`: верните `\"\"` (пустую строку), если операция допустима, иначе текст ошибки. Типы — `income` и `expense`. Сначала проверяется тип (`неизвестный тип`), затем сумма (`сумма должна быть положительной`).",
  "validate", "def validate(kind, amount):\n    if kind not in (\"income\", \"expense\"):\n        return \"неизвестный тип\"\n    if amount <= 0:\n        return \"сумма должна быть положительной\"\n    return \"\"\n",
  [["income", 100], ["gift", 5], (["expense", 0], True), (["expense", -3], True), (["gift", -1], True), (["income", 1], True)],
  [("def validate(kind, amount):\n    if amount <= 0:\n        return \"сумма должна быть положительной\"\n    if kind not in (\"income\", \"expense\"):\n        return \"неизвестный тип\"\n    return \"\"\n", "Порядок проверок: для неизвестного типа с неверной суммой должно быть сообщение о типе.")],
  hints("Две проверки подряд.", "Первая — тип.", "Вторая — сумма.", "Для допустимой операции верните пустую строку.", "Порядок проверок важен для сообщения."),
  "Когда правила собраны в одной функции, их легко проверить и менять.")

a4 = fn_task("a4-balance", "Баланс по записям",
  "Напишите `balance_of(records)`: `records` — список пар `[kind, amount]`. Доходы (`income`) прибавляются, расходы (`expense`) вычитаются. Верните итог.",
  "balance_of", "def balance_of(records):\n    return sum(a if k == \"income\" else -a for k, a in records)\n",
  [[[["income", 500], ["expense", 120]]], [[]], ([[["expense", 10]]], True), ([[["income", 1], ["income", 2], ["expense", 3]]], True)],
  [("def balance_of(records):\n    return sum(a for k, a in records)\n", "Расходы не вычитаются.")],
  hints("Каждая запись — пара: тип и сумма.", "Доход прибавляется.", "Расход вычитается.", "Можно сделать сумму по генератору.", "Для пустого списка — 0."),
  "Вычисление баланса — логика предметной области, поэтому оно живёт в сервисе, а не в интерфейсе.")

a5 = predict_task("a5-swap", "Замена хранилища",
  'class ListRepo:\n    def __init__(self):\n        self.items = []\n\n    def add(self, item):\n        self.items.append(item)\n\n    def all(self):\n        return list(self.items)\n\n\nclass SortedRepo(ListRepo):\n    def all(self):\n        return sorted(self.items)\n\n\nclass Service:\n    def __init__(self, repo):\n        self.repo = repo\n\n    def add(self, value):\n        self.repo.add(value)\n\n    def values(self):\n        return self.repo.all()\n\n\nfor repo in (ListRepo(), SortedRepo()):\n    service = Service(repo)\n    for v in (3, 1, 2):\n        service.add(v)\n    print(service.values())\n',
  [("[1, 2, 3]\n[1, 2, 3]", "ListRepo возвращает записи в порядке добавления."), ("[3, 1, 2]\n[3, 1, 2]", "SortedRepo сортирует при выдаче.")],
  hints("Сервис одинаков для обоих хранилищ.", "Добавляются значения 3, 1, 2.", "ListRepo отдаёт в порядке добавления: 3, 1, 2.", "SortedRepo отдаёт отсортированными.", "Результаты двух циклов разные."),
  "Сервис работает с любым хранилищем, у которого есть add и all: заменив хранилище, мы изменили поведение, не трогая сервис.")

mistakes = [
 {"mistake": "Правила проверки пишут прямо в интерфейсе", "fix": "Вынесите их в сервис: тогда они одни для любого интерфейса."},
 {"mistake": "Интерфейс обращается к хранилищу напрямую", "fix": "Только через сервис."},
 {"mistake": "Хранилище содержит бизнес-правила", "fix": "Хранилище только сохраняет и отдаёт."},
 {"mistake": "Слишком много слоёв для маленькой программы", "fix": "Слои вводят, когда есть что разделять; начните с функций."}]

finish("arch-02-layers", "Слои приложения", "Разделять приложение на интерфейс, логику и данные.",
  {"arch.layers": "Слои приложения", "arch.repo": "Репозиторий", "arch.service": "Сервис"},
  ["arch-01-responsibility"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="architecture")

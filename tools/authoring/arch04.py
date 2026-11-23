from lib import *

BUS = '''handlers = {}


def subscribe(event, handler):
    handlers.setdefault(event, []).append(handler)


def publish(event, payload):
{PUB}

'''
BUS_MAIN = '''
def on_added(item):
    print("добавлено:", item)


def on_any_change(item):
    print("журнал:", item)


subscribe("added", on_added)
subscribe("added", on_any_change)
subscribe("removed", on_any_change)
for _ in range(int(input())):
    event, item = input().split()
    publish(event, item)
'''
PUB_OK = "    for handler in handlers.get(event, []):\n        handler(payload)\n"
def bus(pub): return BUS.replace("{PUB}\n", pub) + BUS_MAIN

begin()
scenes = [
 S("intro", "SOLID и здравый смысл", """
  Пять принципов, объединённых словом SOLID, формулируют, как писать код, который легко развивать. Мы уже встречали два из них.
  Единственная ответственность — одна причина для изменения. Инверсия зависимостей — логика зависит от абстракций, а не от
  конкретных реализаций. Сегодня разберём принцип открытости и закрытости, посмотрим на подстановку Лисков и посмотрим
  два полезных приёма: стратегию и наблюдателя. И запомним главное: принципы служат здравому смыслу, а не наоборот.""",
  nt("**S**ingle responsibility · **O**pen/closed · **L**iskov · **I**nterface segregation · **D**ependency inversion", at="Пять принципов")),
 S("chain", "Цепочка условий", """
  Допустим, магазин считает цену со скидкой. Сначала это условие для двух видов скидок. Через месяц добавляют третий, потом
  четвёртый. Каждый раз правится одна и та же функция, и каждый раз можно сломать уже работающее. Принцип открытости и
  закрытости говорит: код должен быть открыт для расширения, но закрыт для изменения. Добавление нового варианта не должно
  требовать правки старых.""",
  clr(), t('def price_with(kind, price):\n    if kind == "none":\n        return price\n    if kind == "percent10":\n        return price * 9 // 10\n    raise ValueError("неизвестная скидка")\n\n\n', at="Допустим"),
  t('print(price_with("none", 200))\nprint(price_with("percent10", 200))\n', at="Каждый раз"), run("Добавление")),
 S("strategy", "Стратегия", """
  Приём называется стратегией. Каждый вариант поведения — отдельная маленькая функция, а выбор варианта делается по таблице:
  словарь, где ключ — название, а значение — функция. Новый вид скидки — это новая функция и одна запись в словаре. Код
  выбора не меняется вообще. Заодно у нас появляется проверка: если ключа нет, возбуждаем ошибку.""",
  clr(), t('DISCOUNTS = {\n    "none": lambda price: price,\n    "percent10": lambda price: price * 9 // 10,\n    "minus50": lambda price: max(0, price - 50),\n}\n\n\ndef price_with(kind, price):\n    if kind not in DISCOUNTS:\n        raise ValueError("неизвестная скидка")\n    return DISCOUNTS[kind](price)\n\n\n', at="Приём"),
  t('for kind in ["none", "percent10", "minus50"]:\n    print(kind, price_with(kind, 200))\n', at="Новый вид"), run("Заодно")),
 S("observer", "Наблюдатель", """
  Другой полезный приём — наблюдатель, или подписка на события. Когда в системе что-то происходит, например добавлена
  запись, заинтересованные части должны узнать об этом, но источник события не должен знать, кто они. Реализуем шину
  событий: подписчики регистрируются на событие по имени, а публикация вызывает все подписанные функции. Добавить нового
  подписчика можно, не меняя код публикации.""",
  clr(), t('handlers = {}\n\n\ndef subscribe(event, handler):\n    handlers.setdefault(event, []).append(handler)\n\n\ndef publish(event, payload):\n    for handler in handlers.get(event, []):\n        handler(payload)\n\n\n', at="Реализуем"),
  t('subscribe("added", lambda x: print("письмо про", x))\nsubscribe("added", lambda x: print("журнал:", x))\npublish("added", "молоко")\npublish("removed", "хлеб")\n', at="Добавить"), run("Добавить")),
 S("liskov", "Подстановка Лисков", """
  Принцип подстановки Лисков требует, чтобы объект подкласса можно было использовать везде, где ожидается объект базового
  класса, не ломая программу. Если у птицы есть метод «лететь», а в подклассе пингвин он бросает исключение, то любой код,
  работающий с птицами, внезапно упадёт на пингвине. Такая иерархия спроектирована неверно: пингвин не должен наследовать
  способность летать.""",
  clr(), t('class Bird:\n    def fly(self):\n        return "летит"\n\n\nclass Penguin(Bird):\n    def fly(self):\n        raise NotImplementedError("пингвины не летают")\n\n\n', at="Если у птицы"),
  t('for bird in [Bird(), Penguin()]:\n    try:\n        print(bird.fly())\n    except NotImplementedError as e:\n        print("сломалось:", e)\n', at="Такая иерархия"), run("Такая иерархия")),
 S("summary", "Итог", """
  Подведём итог. Не наращивайте цепочки условий: вынесите варианты в таблицу функций. Для оповещения о событиях используйте
  подписку. Следите, чтобы подклассы честно выполняли контракт родителя. И не усложняйте заранее: если программе хватает
  пяти строк, не нужно строить для неё фабрику фабрик. Принципы помогают, когда код начинает расти.""",
  nt("таблица стратегий · подписчики · подкласс не нарушает контракт · не усложнять заранее", at="Подведём итог")),
]

notes = """
# SOLID и приёмы

```python
DISCOUNTS = {
    "none": lambda price: price,
    "percent10": lambda price: price * 9 // 10,
}

def price_with(kind, price):
    if kind not in DISCOUNTS:
        raise ValueError("неизвестная скидка")
    return DISCOUNTS[kind](price)
```

## Принципы

- **S** — у модуля одна причина изменения.
- **O** — расширять добавлением, а не правкой.
- **L** — подкласс заменяет родителя без поломок.
- **I** — маленькие интерфейсы вместо одного огромного.
- **D** — зависеть от абстракций (принимать зависимости снаружи).

## Приёмы

- Стратегия: словарь «название → функция».
- Наблюдатель: подписка на события, источник не знает подписчиков.

Не усложняйте заранее: принципы нужны, когда код растёт.
"""

a1 = predict_task("a1-strategy", "Таблица стратегий",
  'RULES = {\n    "double": lambda x: x * 2,\n    "square": lambda x: x * x,\n    "neg": lambda x: -x,\n}\n\nfor name in ["square", "neg", "double", "cube"]:\n    action = RULES.get(name)\n    print(name, action(7) if action else "нет такой")\n',
  [("square 14\nneg -7\ndouble 49\ncube нет такой", "Квадрат семи — 49, а удвоение — 14."), ("square 49\nneg -7\ndouble 14\ncube 343", "Ключа cube в таблице нет.")],
  hints("Таблица связывает название с функцией.", "square(7) = 49.", "neg(7) = −7.", "double(7) = 14.", "cube в таблице нет: get вернёт None."),
  "Выбор по таблице заменяет цепочку if: .get вернул None для неизвестного названия, и мы вывели запасной текст.")

a2 = fn_task("a2-discounts", "Скидки таблицей",
  "Напишите `price_with(kind, price)`: `none` — цена без изменений; `percent10` — цена минус 10 % (целое: `price * 9 // 10`); `minus50` — цена минус 50, но не ниже 0. Для другого названия — `ValueError`. Реализуйте через **словарь функций**.",
  "price_with", "DISCOUNTS = {\n    \"none\": lambda price: price,\n    \"percent10\": lambda price: price * 9 // 10,\n    \"minus50\": lambda price: max(0, price - 50),\n}\n\n\ndef price_with(kind, price):\n    if kind not in DISCOUNTS:\n        raise ValueError(\"неизвестная скидка\")\n    return DISCOUNTS[kind](price)\n",
  [["none", 200], ["percent10", 200], (["minus50", 200], True), (["minus50", 30], True), {"args": ["vip", 100], "expected_error": "ValueError", "hidden": True}, (["percent10", 99], True)],
  [("def price_with(kind, price):\n    if kind == \"none\":\n        return price\n    if kind == \"percent10\":\n        return price * 9 // 10\n    raise ValueError(\"неизвестная скидка\")\n", "Нет скидки minus50."),
   ("DISCOUNTS = {\"none\": lambda p: p, \"percent10\": lambda p: p * 9 // 10, \"minus50\": lambda p: p - 50}\n\n\ndef price_with(kind, price):\n    if kind not in DISCOUNTS:\n        raise ValueError(\"неизвестная скидка\")\n    return DISCOUNTS[kind](price)\n", "Цена может стать отрицательной.")],
  hints("Каждый вид скидки — маленькая функция.", "Соберите их в словарь: название → функция.", "Для минус 50 используйте max, чтобы не уйти ниже нуля.", "Если названия нет в словаре — ValueError.", "Иначе вызовите функцию из словаря."),
  "Новая скидка = новая запись в словаре. Код выбора не меняется: он закрыт для изменения и открыт для расширения.")

a3 = fn_task("a3-shipping", "Добавьте вариант доставки",
  "Функция `shipping(kind, weight)` считает стоимость: `standard` — `5 + вес`, `fast` — `10 + 2 × вес`. Нужно **добавить** `express` — `20 + 3 × вес`, не ломая остальные. Для неизвестного вида — `ValueError`.",
  "shipping", "RATES = {\n    \"standard\": lambda weight: 5 + weight,\n    \"fast\": lambda weight: 10 + 2 * weight,\n    \"express\": lambda weight: 20 + 3 * weight,\n}\n\n\ndef shipping(kind, weight):\n    if kind not in RATES:\n        raise ValueError(\"неизвестная доставка\")\n    return RATES[kind](weight)\n",
  [["standard", 3], ["express", 2], (["fast", 4], True), (["express", 0], True), {"args": ["drone", 1], "expected_error": "ValueError", "hidden": True}, (["standard", 0], True)],
  [("def shipping(kind, weight):\n    if kind == \"standard\":\n        return 5 + weight\n    if kind == \"fast\":\n        return 10 + 2 * weight\n    raise ValueError(\"неизвестная доставка\")\n", "Express не добавлен."),
   ("def shipping(kind, weight):\n    if kind == \"standard\":\n        return 5 + weight\n    if kind == \"fast\":\n        return 10 + 2 * weight\n    if kind == \"express\":\n        return 20 + 2 * weight\n    raise ValueError(\"неизвестная доставка\")\n", "Неверный коэффициент express.")],
  hints("Сейчас вид доставки выбирается цепочкой условий.", "Соберите тарифы в словарь: вид → функция от веса.", "Для express: 20 + 3 × вес.", "Неизвестный вид — ValueError.", "Тариф вызывается как RATES[kind](weight)."),
  "Тарифы лежат в таблице, поэтому новый вариант — одна новая запись.",
  type="complete", starter="def shipping(kind, weight):\n    if kind == \"standard\":\n        return 5 + weight\n    if kind == \"fast\":\n        return 10 + 2 * weight\n    raise ValueError(\"неизвестная доставка\")\n")

a4 = stdout_task("a4-bus", "Шина событий",
  "Подписчики уже зарегистрированы. Допишите функцию `publish(event, payload)`: она вызывает **все** обработчики, подписанные на событие `event`, передавая им `payload`. Если подписчиков нет — ничего не происходит. Во входных данных `n` строк `событие предмет`.",
  bus(PUB_OK), ["3\nadded молоко\nremoved хлеб\nupdated чай\n", ("1\nadded сыр\n", True), ("2\nremoved a\nremoved b\n", True), ("0\n", True)],
  [(bus("    for handler in handlers.get(event, [])[:1]:\n        handler(payload)\n"), "Вызывается только первый подписчик."),
   (bus("    handlers[event](payload)\n"), "Событие без подписчиков вызывает KeyError; несколько подписчиков не поддерживаются.")],
  hints("Подписчики лежат в словаре handlers: событие → список функций.", "Если событие не зарегистрировано, списка нет.", "Метод get с пустым списком по умолчанию решает вопрос.", "Обойдите список в цикле.", "Каждому обработчику передайте payload."),
  "Источник события не знает подписчиков: он лишь обходит список и вызывает каждого.",
  starter=bus("    pass\n"), type="complete")

a5 = predict_task("a5-liskov", "Подстановка не сработала",
  'class Shape:\n    def area(self):\n        return 0\n\n\nclass Square(Shape):\n    def __init__(self, side):\n        self.side = side\n\n    def area(self):\n        return self.side ** 2\n\n\nclass Broken(Shape):\n    def area(self):\n        raise NotImplementedError\n\n\ntotal = 0\nfor shape in [Square(2), Shape(), Broken(), Square(3)]:\n    try:\n        total += shape.area()\n    except NotImplementedError:\n        print("пропущена фигура")\nprint(total)\n',
  [("13", "Сообщение о пропущенной фигуре тоже печатается."), ("пропущена фигура\n13\n", "")][:1] + [("пропущена фигура\n9", "Квадрат со стороной 2 даёт 4, со стороной 3 — 9: всего 13.")],
  hints("Для каждой фигуры вызывается area().", "Square(2): 4.", "Shape(): 0.", "Broken(): исключение — печатается «пропущена фигура».", "Square(3): 9. Сумма: 4 + 0 + 9."),
  "Подкласс Broken нарушает контракт Shape (метод area обязан вернуть число), поэтому коду приходится его обходить.")

mistakes = [
 {"mistake": "Каждый новый вариант — ещё одна ветка if в той же функции", "fix": "Словарь стратегий: новый вариант — новая запись."},
 {"mistake": "Подкласс бросает NotImplementedError в унаследованном методе", "fix": "Не наследуйте то, что подкласс не умеет."},
 {"mistake": "Источник события вызывает конкретных получателей", "fix": "Публикуйте событие, подписчики регистрируются сами."},
 {"mistake": "Применяют все приёмы сразу «на вырост»", "fix": "Начинайте просто, усложняйте, когда появится причина."}]

finish("arch-04-solid", "SOLID и приёмы проектирования", "Применять принципы открытости, подстановки и приёмы «стратегия» и «наблюдатель».",
  {"arch.solid": "Принципы SOLID", "arch.strategy": "Паттерн «Стратегия»", "arch.observer": "Паттерн «Наблюдатель»"},
  ["arch-03-dependencies"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="architecture")

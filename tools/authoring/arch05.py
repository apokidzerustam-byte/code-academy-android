from lib import *

MIX = '''items = []


def handle(command):
    action, _, argument = command.partition(" ")
    if action == "add":
        items.append({"title": argument, "done": False})
    elif action == "done":
        items[int(argument) - 1]["done"] = True
    for number, item in enumerate(items, 1):
        print(f"{number}. [{'x' if item['done'] else ' '}] {item['title']}")


handle("add Молоко")
handle("add Хлеб")
handle("done 1")
'''

MODEL = '''class TodoModel:
    def __init__(self):
        self.items = []

    def add(self, title):
        self.items.append({"title": title, "done": False})

    def toggle(self, index):
        self.items[index]["done"] = not self.items[index]["done"]


'''
VIEW = '''def render(items):
    for number, item in enumerate(items, 1):
        mark = "x" if item["done"] else " "
        print(f"{number}. [{mark}] {item['title']}")


'''
CTRL = '''def handle(model, command):
    action, _, argument = command.partition(" ")
    if action == "add":
        model.add(argument)
    elif action == "done":
        model.toggle(int(argument) - 1)
    render(model.items)


model = TodoModel()
for _ in range(int(input())):
    handle(model, input())
'''

VM = '''class TodoViewModel:
    def __init__(self):
        self.state = {"items": []}
        self.listeners = []

    def observe(self, listener):
        self.listeners.append(listener)
        listener(self.state)

    def _set(self, state):
        self.state = state
        for listener in self.listeners:
            listener(state)

    def add(self, title):
        items = self.state["items"] + [{"title": title, "done": False}]
        self._set({"items": items})

    def toggle(self, index):
        items = [dict(item) for item in self.state["items"]]
        items[index]["done"] = not items[index]["done"]
        self._set({"items": items})


'''
VVIEW = '''def view(state):
    print("--- экран ---")
    for number, item in enumerate(state["items"], 1):
        mark = "x" if item["done"] else " "
        print(f"{number}. [{mark}] {item['title']}")


'''
VMAIN = '''vm = TodoViewModel()
vm.observe(view)
vm.add("Молоко")
vm.add("Хлеб")
vm.toggle(0)
'''

IMM_A = '''old = {"count": 1, "log": ["+1"]}
changed = old
changed["count"] = 2
print(old["count"])
'''
IMM_B = '''
old = {"count": 1, "log": ["+1"]}
new = {"count": old["count"] + 1, "log": old["log"] + ["+1"]}
print(old["count"], new["count"])
'''

DER = '''def active_count(state):
    return sum(1 for item in state["items"] if not item["done"])


def visible(state):
    items = state["items"]
    if state["filter"] == "active":
        return [item for item in items if not item["done"]]
    if state["filter"] == "done":
        return [item for item in items if item["done"]]
    return items


'''
DER_MAIN = '''state = {"filter": "active", "items": [
    {"title": "Молоко", "done": True},
    {"title": "Хлеб", "done": False},
    {"title": "Чай", "done": False},
]}
print(active_count(state))
print([item["title"] for item in visible(state)])
'''

begin()
scenes = [
 S("intro", "Три роли и состояние", """
  Приложение с экраном делает три дела: хранит данные, решает, что с ними делать, и показывает результат. Если всё это перемешать в одной
  функции, любая правка становится рискованной: поправили вывод и случайно сломали вычисления. Поэтому появились шаблоны, которые разделяют
  роли. Два самых известных называются MVC и MVVM. В обоих первая буква M означает модель: данные и правила работы с ними. Буква V означает вид,
  то есть то, что видит пользователь. А третья часть, это посредник между ними: контроллер в MVC и вью-модель в MVVM. Отдельное понятие мы
  будем использовать всё время: состояние. Состояние, это все данные, от которых зависит, что сейчас на экране. Хорошая архитектура отвечает на два
  вопроса: где живёт состояние и кто имеет право его менять. Представьте будильник. Время и список сигналов, это состояние. Кнопка
  «добавить сигнал», это событие. А циферблат, это вид. Если каждый из них отвечает за своё, будильник легко менять: можно перерисовать циферблат,
  не трогая логику сигналов.""",
  nt("**Модель** — данные и правила · **Вид** — что видит пользователь · **Посредник** — контроллер (MVC) или вью-модель (MVVM)", at="Два самых известных"),
  nt("**Состояние** — все данные, от которых зависит экран", at="Состояние, это все данные")),
 S("mix", "Когда всё перемешано", """
  Сначала посмотрим на код, где ничего не разделено. Это список дел. Функция handle получает команду, меняет список и тут же печатает его.
  Работает? Работает. Но попробуйте сказать, где здесь правила, а где вывод. Если захочется показать список иначе, например на экране телефона,
  придётся переписывать всё. А проверить сами правила, не напечатав ничего, нельзя. Именно эту проблему и решают шаблоны.""",
  clr(), t(MIX, at="Сначала посмотрим"), hl([5, 6, 7, 8, 9], at="Функция handle"), hl([10, 11], at="Но попробуйте сказать"), run("Именно эту проблему")),
 S("mvc", "MVC: контроллер связывает", """
  Разделим по ролям. Модель знает только про данные: она умеет добавить дело и отметить его выполненным, и ничего не печатает. Вид, функция
  render, умеет только показывать список, и ничего не решает. А контроллер, функция handle, разбирает команду, вызывает нужный метод модели и
  просит вид перерисоваться. Теперь вид можно заменить, не трогая правила, а правила проверить без вывода. Запустим тот же сценарий: добавим два дела
  и отметим первое. Результат тот же, но код стал честнее. Заметьте, что модель можно запустить и
  проверить без единого print: достаточно добавить дело и посмотреть на список. Раньше для этого пришлось бы читать вывод глазами. А в
  будущем для этой же модели можно написать совсем другой вид, например окно на телефоне, и ничего в правилах не менять.""",
  clr(), t(MODEL, at="Разделим по ролям"), t(VIEW, at="Вид, функция"), t(CTRL, at="А контроллер"), hl([18, 19, 20, 21, 22, 23, 24], at="А контроллер"),
  run("Запустим тот же", stdin="3\nadd Молоко\nadd Хлеб\ndone 1\n")),
 S("mvvm", "MVVM: вид подписывается на состояние", """
  В MVVM связь устроена иначе. Вью-модель хранит состояние и даёт виду подписаться на него. Вид объявляет: сообщи мне, когда состояние
  изменится. Когда логика что-то меняет, вью-модель сама уведомляет всех подписчиков, а вид просто рисует то, что пришло. Контроллеру не нужно помнить
  вызвать перерисовку. Смотрите на метод observe: он запоминает вид и сразу показывает ему текущее состояние. Метод set подставляет новое
  состояние и обходит подписчиков. Запустим: вид рисуется при подписке и после каждого изменения, и в коде для этого нет ни одного
  явного вызова. Это и есть главное удобство MVVM: можно подключить сколько угодно видов, например список и счётчик на другом экране, и все они
  будут показывать одно и то же состояние. Вью-модель не знает, сколько видов за ней наблюдают и как они выглядят.""",
  clr(), t(VM, at="В MVVM связь"), t(VVIEW, at="а вид просто рисует"), hl([6, 7, 8], at="Смотрите на метод observe"), hl([10, 11, 12, 13], at="Метод set"),
  t(VMAIN, at="Запустим"), run("Запустим")),
 S("immutable", "Новое состояние вместо правки старого", """
  Заметьте приём в этом коде: мы не правим старое состояние, а строим новое. Почему так? Во-первых, вид получает целый снимок и просто
  перерисовывается. Во-вторых, старые состояния остаются целыми, и можно сделать отмену. В-третьих, нет скрытых изменений: никто не поменяет
  данные у вас за спиной. Проверим на примере. Если присвоить состояние другой переменной и изменить, то старое тоже изменится, потому что
  это один и тот же объект. А если построить новый словарь, старый остаётся нетронутым, и мы видим оба значения. На практике это правило экономит часы
  отладки: когда что-то пошло не так, достаточно посмотреть на цепочку состояний, и сразу видно, на каком шаге значение стало неверным. Старое
  состояние при этом никто не испортил.""",
  clr(), t(IMM_A, at="Проверим на примере"), run("это один и тот же объект"), clr(), t(IMM_B.lstrip("\n"), at="А если построить"), run("мы видим оба значения")),
 S("derived", "Производное состояние", """
  Следующее правило: не храните одно и то же в двух местах. Если у вас есть список дел и отдельно число невыполненных, они рано или поздно
  разойдутся: добавили дело и забыли обновить число. Число лучше вычислять из списка каждый раз. Такие значения называют производным
  состоянием. Здесь функция active count считает невыполненные, а функция visible выбирает дела по фильтру: все, невыполненные или выполненные.
  Фильтр лежит в состоянии, а видимый список вычисляется. Для фильтра «невыполненные» получим два дела. Если пользователь переключит фильтр, нам
  достаточно поменять одно поле, а список пересчитается сам. Не нужно помнить, что обновить ещё, и забыть что-то невозможно.""",
  clr(), t(DER, at="Следующее правило"), hl([1, 2], at="Здесь функция active count"), hl([5, 6, 7, 8, 9, 10, 11], at="а функция visible"), t(DER_MAIN, at="Фильтр лежит"), run("Для фильтра")),
 S("android", "На Android всё так же", """
  На Android устроено то же самое. Вью-модель хранит состояние экрана в потоке StateFlow, а экран на Compose подписывается на него и
  перерисовывается при каждом новом значении. Вью-модель переживает поворот экрана, а сам экран нет, поэтому состояние не теряется. События идут
  от экрана к вью-модели, а состояние от вью-модели к экрану. Такой поток данных в одну сторону называется однонаправленным, и он сильно
  упрощает поиск ошибок: всегда понятно, откуда пришло значение. В этом уроке на Android ничего не запускается: мы
  изучаем сам шаблон на Питоне, и тот же шаблон потом пригодится в приложениях на Kotlin.""",
  nt("Событие (нажатие) ↑ вью-модель → новое состояние ↓ экран перерисовывается", at="События идут"),
  nt("```kotlin\nclass TodoViewModel : ViewModel() {\n    private val _state = MutableStateFlow(TodoState())\n    val state: StateFlow<TodoState> = _state\n}\n```\n(показано для знакомства, в уроке не запускается)", at="Вью-модель хранит")),
 S("mistakes", "Типичные ошибки", """
  Четыре типичные ошибки. Первая: вид, который сам решает, что делать с данными. Тогда правила невозможно проверить без экрана. Вторая: изменять состояние
  на месте, когда подписчики и история ждут новый объект. Третья: хранить одно и то же в двух местах. Четвёртая: контроллер или вью-модель,
  которые знают, как выглядит экран. Тогда вид нельзя заменить.""",
  nt("Ошибка 1: логика в виде.", at="Первая"), nt("Ошибка 2: изменение состояния на месте.", at="Вторая"),
  nt("Ошибка 3: одно и то же в двух местах.", at="Третья"), nt("Ошибка 4: вью-модель знает про оформление экрана.", at="Четвёртая")),
 S("summary", "Итог", """
  Подведём итог. Приложение делят на модель, вид и посредника. В MVC посредник, контроллер, вызывает вид сам. В MVVM вью-модель хранит состояние,
  а вид на него подписывается. Состояние лучше не править, а заменять новым, и не дублировать данные, которые можно вычислить. В заданиях вы
  предскажете работу подписчиков, напишете контроллер и вью-модель, исправите ошибку с изменением состояния на месте и напишете функцию
  производного состояния. Критерий прохождения: решить не меньше четырёх заданий из пяти.""",
  nt("Модель · Вид · Контроллер/ВьюМодель · новое состояние вместо правки · производное считаем, а не храним", at="Подведём итог")),
]

notes = """
# MVC, MVVM и состояние

Приложение делят на роли:

| Роль | Задача |
|---|---|
| **Модель** | данные и правила; ничего не знает про экран |
| **Вид** | показывает состояние; не решает |
| **Контроллер** (MVC) | разбирает событие, вызывает модель, просит вид перерисоваться |
| **Вью-модель** (MVVM) | хранит состояние; вид **подписывается** на него и перерисовывается сам |

**Состояние** — все данные, от которых зависит, что на экране.

## Правила работы с состоянием

1. Не правьте состояние на месте — стройте **новое**: так работают подписчики и отмена.
2. Не храните дважды то, что можно вычислить (число невыполненных — из списка).
3. Поток данных в одну сторону: событие вверх, состояние вниз.

```py
state = {"items": []}
new_state = {"items": state["items"] + ["Молоко"]}   # старое не изменено
```

## На Android

Вью-модель держит состояние в `StateFlow`, экран на Compose подписывается и перерисовывается при каждом новом значении. В этом уроке на Android ничего не запускается: паттерн показан на Python.
"""

a1 = predict_task("a1-observers", "Кто и когда получает состояние",
  '''class CounterViewModel:
    def __init__(self):
        self.state = 0
        self.listeners = []

    def observe(self, listener):
        self.listeners.append(listener)
        listener(self.state)

    def increment(self):
        self.state += 1
        for listener in self.listeners:
            listener(self.state)

    def reset(self):
        self.state = 0
        for listener in self.listeners:
            listener(self.state)


vm = CounterViewModel()
vm.observe(lambda s: print("экран A:", s))
vm.increment()
vm.observe(lambda s: print("экран B:", s))
vm.increment()
vm.reset()
''',
  [("экран A: 1\nэкран A: 2\nэкран B: 2\nэкран A: 0\nэкран B: 0", "При подписке слушатель сразу получает текущее состояние: сначала A: 0, затем B: 1."),
   ("экран A: 0\nэкран A: 1\nэкран B: 1\nэкран A: 2\nэкран B: 2\nэкран A: 0", "Сброс уведомляет всех подписчиков, в том числе экран B.")],
  hints("Метод observe не только запоминает слушателя, но и сразу вызывает его.", "Первый вызов observe печатает «экран A: 0».", "increment меняет состояние и уведомляет всех, кто уже подписан.",
        "Второй observe подключает B: он сразу получает текущее состояние 1, а не 0.", "После подписки B каждое изменение (increment, reset) печатает две строки: сначала A, потом B."),
  "observe сразу показывает слушателю текущее состояние, а затем слушатель получает каждое изменение. После подписки B все изменения печатают по две строки, A и B.")

CT = ('class TodoModel:\n    def __init__(self):\n        self.items = []\n\n    def add(self, title):\n        self.items.append({"title": title, "done": False})\n\n'
      '    def toggle(self, index):\n        self.items[index]["done"] = not self.items[index]["done"]\n\n    def remove(self, index):\n        del self.items[index]\n\n\n'
      'def render(items):\n    if not items:\n        print("(пусто)")\n    for number, item in enumerate(items, 1):\n        mark = "x" if item["done"] else " "\n        print(f"{number}. [{mark}] {item[\'title\']}")\n\n\n')
CT_MAIN = 'model = TodoModel()\nfor _ in range(int(input())):\n    handle(model, input())\n'
CT_SOL_H = ('def handle(model, command):\n    action, _, argument = command.partition(" ")\n    if action == "add":\n        model.add(argument)\n    elif action == "done":\n        model.toggle(int(argument) - 1)\n'
            '    elif action == "remove":\n        model.remove(int(argument) - 1)\n    render(model.items)\n\n\n')
CT_SOL = CT + CT_SOL_H + CT_MAIN
CT_START = CT + 'def handle(model, command):\n    # Разберите команду, вызовите метод модели и перерисуйте список\n    pass\n\n\n' + CT_MAIN
a2 = stdout_task("a2-controller", "Контроллер списка дел",
  "Модель `TodoModel` и вид `render` готовы. Допишите **контроллер** `handle(model, command)`: команды `add <название>`, `done <номер>` (отметить или снять отметку) и `remove <номер>`; номера считаются с **единицы**. "
  "После каждой команды вид должен перерисовать список. Первая строка ввода — число команд.",
  CT_SOL, ["3\nadd Молоко\nadd Хлеб\ndone 1\n", ("4\nadd А\nremove 1\nadd Б\ndone 1\n", True), ("1\nadd X\n", True), ("3\nadd Я\ndone 1\ndone 1\n", True), ("2\nadd Я\nremove 1\n", True)],
  [(CT_START, "Заготовка: контроллер ничего не делает и не перерисовывает вид."),
   (CT_SOL.replace("    render(model.items)\n\n\nmodel", "\n\nmodel"), "После команды вид не перерисовывается."),
   (CT_SOL.replace("model.toggle(int(argument) - 1)", "model.toggle(int(argument))").replace("model.remove(int(argument) - 1)", "model.remove(int(argument))"), "Номера считаются с единицы: индекс списка на единицу меньше."),
   (CT_SOL.replace('    elif action == "remove":\n        model.remove(int(argument) - 1)\n', ''), "Команда remove не обработана.")],
  hints("Команду делят на слово и аргумент: command.partition(\" \").", "Для add передайте аргумент как название дела.", "Для done и remove аргумент — номер с единицы: индекс в модели на единицу меньше.",
        "Контроллер не печатает список сам: он вызывает готовую функцию render.", "В конце handle — render(model.items), и он выполняется после любой команды."),
  "Контроллер разбирает команду, вызывает метод модели и просит вид перерисоваться. Правила остаются в модели, а вывод — в виде.",
  type="complete", starter=CT_START, goal="Связать модель и вид контроллером.", criteria=["Три команды обработаны.", "Индексы с единицы.", "После каждой команды список перерисован."])

ST_BAD = ('class Store:\n    def __init__(self):\n        self.state = {"count": 0, "log": []}\n        self.history = []\n\n    def increment(self):\n        self.history.append(self.state)\n'
          '        self.state["count"] += 1\n        self.state["log"].append("+1")\n\n    def undo(self):\n        if self.history:\n            self.state = self.history.pop()\n\n\n'
          'store = Store()\nfor _ in range(int(input())):\n    store.increment()\nfor _ in range(int(input())):\n    store.undo()\nprint(store.state["count"], store.state["log"])\n')
ST_SOL = ST_BAD.replace('        self.history.append(self.state)\n        self.state["count"] += 1\n        self.state["log"].append("+1")\n',
                         '        self.history.append(self.state)\n        self.state = {"count": self.state["count"] + 1, "log": self.state["log"] + ["+1"]}\n')
assert ST_SOL != ST_BAD
a3 = stdout_task("a3-undo", "Отмена, которая не работает",
  "В хранилище `Store` каждое увеличение должно сохранять прежнее состояние в `history`, а `undo` — возвращать его. Но после трёх увеличений и двух отмен программа печатает `3 ['+1', '+1', '+1']` вместо `1 ['+1']`. "
  "Найдите причину и исправьте `increment`: первая строка ввода — число увеличений, вторая — число отмен.",
  ST_SOL, ["3\n2\n", ("1\n1\n", True), ("4\n1\n", True), ("2\n0\n", True), ("5\n3\n", True)],
  [(ST_BAD, "Исходная версия: в истории лежит один и тот же словарь, который меняют на месте."),
   (ST_BAD.replace('        self.history.append(self.state)\n        self.state["count"] += 1\n        self.state["log"].append("+1")\n',
                   '        self.history.append(self.state)\n        self.state = dict(self.state)\n        self.state["count"] += 1\n        self.state["log"].append("+1")\n'),
    "Копия поверхностная: список log по-прежнему общий для всех состояний.")],
  hints("В истории хранятся не копии, а ссылки на один и тот же словарь.", "Изменение на месте меняет и то, что лежит в history.", "Нужно не править состояние, а создавать новое.",
        "Новый словарь строят из старых значений: счётчик плюс один.", "Список log тоже нужен новый: старый список плюс новая запись, без append."),
  "Если менять состояние на месте, все записи в истории указывают на один объект. Чтобы отмена работала, каждое изменение строит новое состояние, в том числе новый список.",
  type="fix", starter=ST_BAD, goal="Сделать состояние неизменяемым для отмены.", criteria=["История хранит разные состояния.", "Отмена возвращает прежнее значение и журнал."])

SUM_SOL = ('def summary(state):\n    items = state["items"]\n    total = len(items)\n    done = sum(1 for item in items if item["done"])\n    percent = round(100 * done / total) if total else 0\n'
           '    return {"left": total - done, "total": total, "percent": percent}\n')
SUM_START = 'def summary(state):\n    # Вычислите left, total и percent из списка state["items"]\n    pass\n'
def items(*flags): return {"items": [{"title": f"дело {i}", "done": f} for i, f in enumerate(flags, 1)]}
a4 = fn_task("a4-summary", "Сводка по списку дел",
  "Состояние хранит только список дел `state[\"items\"]`: у каждого есть поле `done` (выполнено или нет). Напишите функцию `summary(state)`, которая **вычисляет** сводку и возвращает словарь "
  "`{\"left\": …, \"total\": …, \"percent\": …}`: сколько дел осталось, сколько всего и какой процент выполнен (`round(100 * выполнено / всего)`; для пустого списка — 0).",
  "summary", SUM_SOL,
  [[items(True, False, False)], [items(True, True, False)], ([items()], False), ([items(True, True)], True), ([items(False, False, False, False, False, False)], True), ([items(True, False, False, False, False, False)], True), ([items(True, True, True, True, True, False)], True)],
  [('def summary(state):\n    items = state["items"]\n    total = len(items)\n    done = sum(1 for item in items if item["done"])\n    percent = 100 * done // total if total else 0\n    return {"left": total - done, "total": total, "percent": percent}\n',
    "Целочисленное деление отбрасывает дробную часть: 2 из 3 даёт 66, а нужно 67."),
   ('def summary(state):\n    items = state["items"]\n    total = len(items)\n    done = sum(1 for item in items if item["done"])\n    percent = round(100 * done / total)\n    return {"left": total - done, "total": total, "percent": percent}\n',
    "Пустой список: деление на ноль."),
   ('def summary(state):\n    items = state["items"]\n    total = len(items)\n    done = sum(1 for item in items if item["done"])\n    percent = round(100 * done / total) if total else 0\n    return {"left": done, "total": total, "percent": percent}\n',
    "В left должны попасть невыполненные дела, а не выполненные.")],
  hints("Ничего не храним: сводка вычисляется из списка при каждом вызове.", "Выполненные дела — те, у которых done истинно; их можно посчитать генератором внутри sum.", "Невыполненных — всего минус выполненных.",
        "Процент: 100 умножить на выполненные и разделить на всего, затем round.", "Если дел нет, делить нельзя: верните 0."),
  "Производное состояние не хранят, а вычисляют из основного: так значения не могут разойтись. Особый случай — пустой список: делить на ноль нельзя.",
  type="write", starter=SUM_START, goal="Вычислить производное состояние.", criteria=["left, total и percent верны.", "Пустой список даёт 0 процентов."])

LV_START = ('class ListViewModel:\n    def __init__(self):\n        self.state = {"items": []}\n        self.listeners = []\n\n    def observe(self, listener):\n        # Запомните слушателя и сразу покажите ему текущее состояние\n        pass\n\n'
            '    def add(self, title):\n        # Создайте НОВОЕ состояние с добавленным делом и сообщите всем слушателям\n        pass\n\n\n'
            'def view(state):\n    print("экран:", ", ".join(state["items"]) or "пусто")\n\n\nvm = ListViewModel()\nvm.observe(view)\nfor _ in range(int(input())):\n    vm.add(input())\n')
LV_SOL = LV_START.replace('        # Запомните слушателя и сразу покажите ему текущее состояние\n        pass\n', '        self.listeners.append(listener)\n        listener(self.state)\n').replace(
    '        # Создайте НОВОЕ состояние с добавленным делом и сообщите всем слушателям\n        pass\n',
    '        self.state = {"items": self.state["items"] + [title]}\n        for listener in self.listeners:\n            listener(self.state)\n')
a5 = stdout_task("a5-viewmodel", "Вью-модель с подписчиками",
  "Допишите вью-модель. Метод `observe(listener)` запоминает слушателя и **сразу** вызывает его с текущим состоянием. Метод `add(title)` строит **новое** состояние с добавленным делом и вызывает всех слушателей. "
  "Вид `view` уже написан и печатает список. Первая строка ввода — число дел, далее по одному на строку.",
  LV_SOL, ["2\nМолоко\nХлеб\n", ("0\n", True), ("1\nЧай\n", True), ("3\nА\nБ\nВ\n", True)],
  [(LV_START, "Заготовка: подписка и добавление ничего не делают."),
   (LV_SOL.replace("        self.listeners.append(listener)\n        listener(self.state)\n", "        self.listeners.append(listener)\n"), "При подписке слушатель не получает текущее состояние: нет первой строки «пусто»."),
   (LV_SOL.replace("        for listener in self.listeners:\n            listener(self.state)\n", ""), "Слушатели не уведомляются об изменении."),
   (LV_SOL.replace('        self.state = {"items": self.state["items"] + [title]}\n        for listener in self.listeners:\n            listener(self.state)\n',
                   '        for listener in self.listeners:\n            listener(self.state)\n        self.state = {"items": self.state["items"] + [title]}\n'), "Слушатели уведомляются до замены состояния и получают старое.")],
  hints("Подписчиков хранит список self.listeners.", "observe: добавьте слушателя в список и сразу вызовите его с self.state.", "add: сначала постройте новое состояние, потом уведомляйте.",
        "Новое состояние — словарь с новым списком: старый список плюс новый элемент, без append.", "Для каждого слушателя в self.listeners вызовите его с новым состоянием."),
  "Вью-модель владеет состоянием и рассылает его подписчикам. Новое состояние строится до рассылки, а подписчик при подключении сразу получает текущее.",
  type="complete", starter=LV_START, goal="Реализовать подписку и уведомление.", criteria=["Слушатель сразу получает состояние.", "Каждое добавление уведомляет всех.", "Состояние заменяется новым."])

mistakes = [
 {"mistake": "Вид сам решает, что делать с данными", "fix": "Логику держите в модели и посреднике: так её можно проверить без экрана."},
 {"mistake": "Состояние меняют на месте", "fix": "Стройте новое состояние: подписчики и история получают целый снимок."},
 {"mistake": "Одни и те же данные хранятся в двух местах", "fix": "Производное (число невыполненных, фильтр списка) вычисляйте из основного состояния."},
 {"mistake": "Посредник знает про оформление экрана", "fix": "Вью-модель и контроллер не должны знать, как нарисован экран."}]

finish("arch-05-mvc-mvvm", "MVC, MVVM и управление состоянием", "Разделять приложение на модель, вид и посредника и управлять состоянием: новое вместо правки, производное вычислять.",
  {"arch.mvc": "MVC: модель, вид, контроллер", "arch.mvvm": "MVVM: вью-модель и подписка", "arch.state": "Управление состоянием"},
  ["arch-04-solid"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="architecture", min_pass=4)

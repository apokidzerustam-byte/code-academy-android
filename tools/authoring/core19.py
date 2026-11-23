from lib import *

begin()
scenes = [
 S("intro", "Не изобретайте велосипед", """
  Python называют языком с «батарейками в комплекте»: вместе с ним поставляется огромная стандартная библиотека. Математика, даты,
  случайные числа, подсчёт частот, работа с файлами и сетью — всё это уже написано и проверено миллионами программистов.
  Каждая такая возможность лежит в отдельном модуле, то есть в файле с готовым кодом. Чтобы им воспользоваться, модуль нужно
  подключить командой import. В этом уроке разберём три способа импорта и самые полезные модули.""",
  nt("**Модуль** — файл с готовым кодом. Подключается командой `import`", at="Чтобы им")),
 S("import", "Три способа импорта", """
  Первый способ: import и имя модуля. Тогда к функциям обращаются через точку: math точка sqrt. Второй способ: from модуль import
  имя — нужную функцию можно вызывать без приставки. Третий способ: переименование через as, чтобы сократить длинное имя.
  Звёздочку в импорте лучше не использовать, потому что непонятно, откуда взялись имена. Посмотрим на модуль math: корень,
  число пи и округление вверх и вниз.""",
  clr(), t("import math\nprint(math.sqrt(49), math.pi)\n", at="Первый способ"),
  t("from math import floor, ceil\nprint(floor(2.7), ceil(2.1))\n", at="Второй способ"),
  t("import math as m\nprint(m.hypot(3, 4))\n", at="Третий способ"), run("Посмотрим")),
 S("random", "Случайные числа", """
  Модуль random нужен для игр, жребия и тестов. Функция choice выбирает случайный элемент списка, randint — случайное целое в
  диапазоне включительно, shuffle перемешивает список, а sample берёт несколько разных элементов. Результат каждый раз новый,
  поэтому мы проверим не конкретные числа, а свойства: выбранный элемент действительно из списка, а число попало в диапазон.
  Для воспроизводимых результатов, например в тестах, есть функция seed.""",
  clr(), t("import random\n\ncolors = [\"красный\", \"синий\", \"зелёный\"]\n", at="Функция choice"),
  t("print(random.choice(colors) in colors)\nprint(1 <= random.randint(1, 6) <= 6)\nprint(len(random.sample(range(100), 5)))\n", at="поэтому мы проверим"), run("Для воспроизводимых")),
 S("datetime", "Даты и время", """
  Модуль datetime работает с датами. Объект date создаётся из года, месяца и дня. Вычитание двух дат даёт разницу, у которой есть
  количество дней. Прибавив timedelta, можно перейти на несколько дней вперёд или назад. Метод weekday возвращает номер
  дня недели: ноль — понедельник, шесть — воскресенье. А метод fromisoformat разбирает дату из строки привычного вида
  год, месяц, день через дефис.""",
  clr(), t("from datetime import date, timedelta\n\n", at="Модуль datetime"),
  t("a = date(2026, 11, 23)\nb = date.fromisoformat(\"2026-12-31\")\nprint((b - a).days)\n", at="Вычитание"),
  t("print(a + timedelta(days=10), a.weekday())\n", at="Прибавив"), run("А метод fromisoformat")),
 S("collections", "Counter и defaultdict", """
  Модуль collections содержит специализированные словари. Counter считает элементы: передаём ему список или строку и получаем
  словарь «элемент: сколько раз». Метод most_common возвращает самые частые. Defaultdict избавляет от проверок «есть ли
  ключ»: если ключа нет, значение создаётся автоматически. Сгруппируем слова по первой букве: для каждой буквы заведётся свой
  пустой список.""",
  clr(), t("from collections import Counter, defaultdict\n\n", at="Модуль collections"),
  t('counts = Counter("абракадабра")\nprint(counts.most_common(2))\n', at="Counter считает"),
  t('groups = defaultdict(list)\nfor word in ["арбуз", "банан", "абрикос", "вишня", "ананас"]:\n    groups[word[0]].append(word)\nprint(dict(groups))\n', at="Сгруппируем"), run("пустой список")),
 S("own", "Свои модули", """
  Модулем может стать любой ваш файл с расширением py. Если в одной папке лежат файлы tools точка py и main точка py, то в main
  можно написать import tools и пользоваться его функциями. Так большие программы делят на части: в одном файле работа с
  данными, в другом расчёты, в третьем интерфейс. Чтобы код файла не запускался при импорте, служебные действия
  принято прятать под проверкой имени модуля равно main. В учебных проектах приложения мы будем делать именно так.""",
  nt("```python\n# tools.py\ndef square(x):\n    return x * x\n\n# main.py\nimport tools\nprint(tools.square(5))\n```", at="Если в одной папке")),
 S("summary", "Итог", """
  Подведём итог. Модуль подключается через import, from import или import as. Модуль math — математика, random — случайность,
  datetime — даты, collections — удобные счётчики и словари. Для чужих библиотек есть менеджер пакетов pip, но на телефоне без
  интернета мы пользуемся тем, что есть в стандартной библиотеке — а её достаточно для большинства задач. Свои файлы с кодом
  тоже можно импортировать. Дальше нас ждёт объектно-ориентированное программирование.""",
  nt("`math` · `random` · `datetime` · `collections` · `json` — стандартная библиотека", at="Подведём итог")),
]

notes = """
# Модули и стандартная библиотека

```python
import math
print(math.sqrt(49), math.pi)

from math import floor, ceil
print(floor(2.7), ceil(2.1))

import math as m
print(m.hypot(3, 4))
```

## Случайные числа

```python
import random

colors = ["красный", "синий", "зелёный"]
print(random.choice(colors) in colors)        # True
print(1 <= random.randint(1, 6) <= 6)         # True
random.seed(1)                                # воспроизводимость
```

## Даты

```python
from datetime import date, timedelta

a = date(2026, 11, 23)
b = date.fromisoformat("2026-12-31")
print((b - a).days)               # 38
print(a + timedelta(days=10))     # 2026-12-03
print(a.weekday())                # 0 — понедельник
```

## collections

```python
from collections import Counter, defaultdict

print(Counter("абракадабра").most_common(2))   # [('а', 5), ('б', 2)]

groups = defaultdict(list)
for word in ["арбуз", "банан", "абрикос"]:
    groups[word[0]].append(word)
print(dict(groups))
```

## Запомните

1. `import модуль` → вызов `модуль.функция()`.
2. `from модуль import имя` → вызов без приставки.
3. Свой файл `tools.py` импортируется как `import tools`.
"""

a1 = fn_task("a1-circle", "Площадь круга", "Напишите функцию `circle_area(r)`, которая возвращает площадь круга радиуса `r` (используйте `math.pi`).",
  "circle_area", "import math\n\ndef circle_area(r):\n    return math.pi * r ** 2\n",
  [[1], [2.5], ([0], True), ([10], True), ([0.1], True)],
  [("def circle_area(r):\n    return 3 * r ** 2\n", "Приближённое число пи 3 даёт заметную погрешность."),
   ("import math\n\ndef circle_area(r):\n    return 2 * math.pi * r\n", "Это длина окружности, а не площадь."),
   ("import math\n\ndef circle_area(r):\n    return math.pi * r * 2\n", "Радиус умножен на 2 вместо возведения в квадрат.")],
  hints("Площадь круга — число пи на квадрат радиуса.", "Число пи есть в модуле math.", "Модуль подключается в начале файла командой import с именем модуля.", "Квадрат радиуса — r ** 2.", "return math.pi * r ** 2."),
  "math.pi даёт число пи с точностью до 15 знаков; оператор ** возводит радиус в квадрат.", tolerance=1e-6)

a2 = fn_task("a2-days-between", "Дней между датами", "Напишите функцию `days_between(first, second)`: обе даты — строки `ГГГГ-ММ-ДД`; верните количество дней от первой до второй (может быть отрицательным).\n\nПример: `days_between(\"2026-11-23\", \"2026-12-31\")` → `38`.",
  "days_between", "from datetime import date\n\ndef days_between(first, second):\n    return (date.fromisoformat(second) - date.fromisoformat(first)).days\n",
  [["2026-11-23", "2026-12-31"], ["2026-01-01", "2026-01-01"], (["2026-03-01", "2026-02-01"], True), (["2024-02-28", "2024-03-01"], True), (["2020-12-31", "2021-01-01"], True)],
  [("from datetime import date\n\ndef days_between(first, second):\n    return (date.fromisoformat(first) - date.fromisoformat(second)).days\n", "Даты вычтены в обратном порядке: знак результата неверный."),
   ("def days_between(first, second):\n    return int(second[-2:]) - int(first[-2:])\n", "Сравниваются только числа месяца, а не полные даты."),
   ("from datetime import date\n\ndef days_between(first, second):\n    return date.fromisoformat(second) - date.fromisoformat(first)\n", "Возвращён объект timedelta, а не число дней.")],
  hints("Подойдёт модуль datetime.", "Из строки вида ГГГГ-ММ-ДД получают дату методом date.fromisoformat.", "Разность двух дат — объект timedelta.", "Количество дней хранится в атрибуте days.", "return (date.fromisoformat(second) - date.fromisoformat(first)).days."),
  "Вычитание дат учитывает разную длину месяцев и високосные годы, а .days отдаёт число дней.")

a3 = fn_task("a3-top-words", "Самые частые слова", "Напишите функцию `top_words(text, n)`: верните список из `n` самых частых слов (в нижнем регистре) в виде пар `[слово, количество]`, от самых частых. При равенстве частот слова идут в порядке первого появления в тексте.\n\nПример: `top_words(\"да нет Да нет да ой\", 2)` → `[[\"да\", 3], [\"нет\", 2]]`.",
  "top_words", "from collections import Counter\n\ndef top_words(text, n):\n    counts = Counter(text.lower().split())\n    return [[w, c] for w, c in counts.most_common(n)]\n",
  [["да нет Да нет да ой", 2], ["а б в", 5], (["", 3], True), (["к к л л м", 2], True), (["Кот кот КОТ пёс Пёс", 1], True)],
  [("from collections import Counter\n\ndef top_words(text, n):\n    counts = Counter(text.split())\n    return [[w, c] for w, c in counts.most_common(n)]\n", "Регистр не приведён к нижнему."),
   ("from collections import Counter\n\ndef top_words(text, n):\n    counts = Counter(text.lower().split())\n    return [[w, c] for w, c in counts.most_common()]\n", "Возвращаются все слова, а не n самых частых."),
   ("from collections import Counter\n\ndef top_words(text, n):\n    counts = Counter(text.lower().split())\n    return [w for w, c in counts.most_common(n)]\n", "Возвращены только слова без количества.")],
  hints("Для подсчёта частот в стандартной библиотеке есть готовый инструмент.", "Нужен Counter из модуля collections.", "Передайте ему список слов: text.lower().split().", "Метод most_common(n) возвращает n самых частых пар.", "return [[w, c] for w, c in counts.most_common(n)]."),
  "Counter считает элементы, most_common сортирует по убыванию частоты, сохраняя порядок первого появления при равенстве.")

a4 = predict_task("a4-math-date", "Математика и даты", 'import math\nfrom datetime import date, timedelta\n\nprint(math.floor(2.7), math.ceil(2.1), round(math.sqrt(49)))\nd = date(2026, 12, 31) + timedelta(days=1)\nprint(d, d.weekday())\nprint((date(2027, 3, 1) - date(2027, 2, 1)).days)\n',
  [("2 3 7\n2027-01-01 5\n28\n", "1 января 2027 — пятница, у неё номер 4 (понедельник — 0)."),
   ("3 3 7\n2027-01-01 4\n28\n", "floor округляет вниз: 2.7 → 2.")],
  hints("Разберите строки по очереди.", "floor округляет вниз, ceil — вверх.", "31 декабря + 1 день — 1 января следующего года.", "Дни недели: понедельник 0, вторник 1, среда 2, четверг 3, пятница 4.", "Февраль 2027 года — 28 дней."),
  "Функции модуля math и арифметика дат дают предсказуемые результаты: 2 3 7, затем 2027-01-01 (пятница, номер 4) и 28 дней в феврале 2027.")

a5 = fn_task("a5-group", "Группировка по первой букве", "Напишите функцию `group_by_letter(words)`: верните словарь «первая буква → список слов» (слова в исходном порядке, буквы как в слове). Используйте `defaultdict(list)` и верните обычный `dict`.\n\nПример: `group_by_letter([\"арбуз\", \"банан\", \"абрикос\"])` → `{\"а\": [\"арбуз\", \"абрикос\"], \"б\": [\"банан\"]}`.",
  "group_by_letter", "from collections import defaultdict\n\ndef group_by_letter(words):\n    groups = defaultdict(list)\n    for w in words:\n        groups[w[0]].append(w)\n    return dict(groups)\n",
  [[["арбуз", "банан", "абрикос"]], [[]], ([["кот"]], True), ([["дом", "дым", "лес", "лук", "дно"]], True)],
  [("from collections import defaultdict\n\ndef group_by_letter(words):\n    groups = defaultdict(list)\n    for w in words:\n        groups[w[0]] = w\n    return dict(groups)\n", "Слово заменяет предыдущее вместо добавления в список."),
   ("def group_by_letter(words):\n    return {w[0]: [w] for w in words}\n", "Слова на одну букву перезаписывают друг друга."),
   ("from collections import defaultdict\n\ndef group_by_letter(words):\n    groups = defaultdict(list)\n    for w in words:\n        groups[w[-1]].append(w)\n    return dict(groups)\n", "Группировка по последней букве вместо первой.")],
  hints("Для каждой буквы нужен свой список слов.", "defaultdict(list) сам создаёт пустой список для нового ключа.", "Первая буква слова — w[0].", "Добавляйте слово в список методом append.", "groups[w[0]].append(w); в конце return dict(groups)."),
  "defaultdict избавляет от проверки «есть ли ключ»: для новой буквы список создаётся автоматически.")

mistakes = [
 {"mistake": "Файл назвали так же, как модуль (random.py, math.py)", "fix": "Не называйте свои файлы именами стандартных модулей: импорт подхватит ваш файл.", "errorType": "ImportError"},
 {"mistake": "Забыли import перед использованием модуля", "fix": "Подключите модуль в начале файла.", "errorType": "NameError"},
 {"mistake": "from module import * в большом файле", "fix": "Импортируйте конкретные имена — так видно, откуда они."},
 {"mistake": "Рассчитывают на конкретные случайные числа в тестах", "fix": "Проверяйте свойства результата или фиксируйте random.seed()."}]

finish("py-19-modules", "Модули и стандартная библиотека", "Подключать модули тремя способами и пользоваться math, random, datetime и collections.",
  {"python.modules": "Модули и import", "python.stdlib.math": "Модуль math", "python.stdlib.datetime": "Модуль datetime", "python.stdlib.collections": "Counter и defaultdict"},
  ["py-18-json"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="python-core")

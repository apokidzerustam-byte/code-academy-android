from lib import *

begin()
scenes = [
 S("intro", "JSON — язык обмена данными", """
  Программам постоянно нужно передавать данные друг другу: приложению — серверу, серверу — браузеру, программе — файлу на диске.
  Для этого придумали формат JSON. Это обычный текст, который выглядит почти как словари и списки Python: фигурные скобки,
  ключи в кавычках, значения через двоеточие. Его понимают все языки программирования, поэтому JSON стал стандартом для
  веб-программирования и настроек приложений. В Python для работы с ним есть встроенный модуль json.""",
  nt("**JSON** — текстовый формат данных: объекты `{}`, массивы `[]`, строки, числа, `true`, `false`, `null`", at="Это обычный текст")),
 S("dumps", "Из Python в JSON", """
  Функция dumps превращает объект Python в строку JSON. Названия функций легко запомнить: s в конце означает строку. Возьмём
  словарь с именем, возрастом и списком оценок. Обратите внимание на преобразования: True превращается в маленькое true,
  None — в null, а кортеж — в массив. По умолчанию русские буквы записываются кодами, как слэш u и четыре цифры. Чтобы
  текст остался читаемым, добавляем ensure_ascii равно False, а для красивых отступов — indent.""",
  clr(), t("import json\n\n", at="Функция dumps"),
  t('person = {"name": "Аня", "age": 25, "marks": [5, 4], "active": True, "phone": None}\n', at="Возьмём"),
  t("print(json.dumps(person))\n", at="Обратите внимание"),
  t("print(json.dumps(person, ensure_ascii=False))\nprint(json.dumps(person, ensure_ascii=False, indent=2))\n", at="Чтобы"), run("Чтобы")),
 S("loads", "Из JSON в Python", """
  Обратное действие выполняет функция loads: она принимает строку JSON и возвращает словарь или список. Дальше с ними работают
  как с обычными объектами: читают по ключам, перебирают, считают. Посмотрите на пример: приходит строка с товарами, а мы
  получаем список словарей и считаем общую стоимость. Именно так программы разбирают ответы серверов.""",
  clr(), t("import json\n\n", at="Обратное действие"),
  t('text = \'[{"name": "хлеб", "price": 40, "qty": 2}, {"name": "сыр", "price": 350, "qty": 1}]\'\n', at="Посмотрите"),
  t('items = json.loads(text)\nprint(type(items), items[0]["name"])\nprint(sum(i["price"] * i["qty"] for i in items))\n', at="Посмотрите"), run("Именно так")),
 S("files", "JSON и файлы", """
  Для работы с файлами есть пара функций без буквы s: dump записывает объект в открытый файл, а load читает его. Сохраним настройки
  приложения в файл, а потом загрузим обратно и убедимся, что получили то же самое. Это самый простой способ дать программе
  память между запусками: тему оформления, последний открытый урок, список задач.""",
  clr(), t("import json\n\nsettings = {\"theme\": \"тёмная\", \"font\": 18, \"sound\": True}\n", at="Для работы с файлами"),
  t('with open("settings.json", "w", encoding="utf-8") as f:\n    json.dump(settings, f, ensure_ascii=False, indent=2)\n', at="dump записывает"),
  t('with open("settings.json", encoding="utf-8") as f:\n    loaded = json.load(f)\nprint(loaded == settings, loaded["theme"])\n', at="а потом загрузим"), run("Это самый простой")),
 S("errors", "Некорректный JSON", """
  Строка, пришедшая снаружи, может оказаться неверной: потеряна кавычка, лишняя запятая, обрезан конец. Тогда loads вызывает
  исключение JSONDecodeError. Это подвид ValueError, поэтому его можно перехватить через except ValueError. Всегда
  обрабатывайте такие ошибки, когда читаете данные из внешнего источника: файла, ответа сервера или текста, который вставил
  пользователь. Также помните, что JSON не умеет хранить множества и даты напрямую: их придётся преобразовать.""",
  clr(), t('import json\n\nfor text in [\'{"a": 1}\', \'{"a": 1,}\']:\n    try:\n        print(json.loads(text))\n    except ValueError:\n        print("некорректный JSON")\n', at="Тогда loads"), run("Всегда")),
 S("summary", "Итог", """
  Подведём итог. JSON — универсальный текстовый формат для обмена данными. Функция dumps превращает объект в строку, loads —
  строку в объект. Функции dump и load делают то же самое с файлами. Параметр ensure_ascii равно False сохраняет русский
  текст читаемым, а indent добавляет отступы. Некорректный JSON даёт ошибку, которую нужно перехватывать. В веб-разработке
  вы будете работать с JSON постоянно.""",
  nt("`dumps` ↔ `loads` (строка) · `dump` ↔ `load` (файл) · `ensure_ascii=False`", at="Подведём итог")),
]

notes = """
# JSON

```python
import json

person = {"name": "Аня", "age": 25, "marks": [5, 4], "active": True, "phone": None}
print(json.dumps(person, ensure_ascii=False))
print(json.dumps(person, ensure_ascii=False, indent=2))
```

| Python | JSON |
| --- | --- |
| `dict` | объект `{}` |
| `list`, `tuple` | массив `[]` |
| `str` | строка |
| `int`, `float` | число |
| `True` / `False` | `true` / `false` |
| `None` | `null` |

## Из JSON в Python

```python
import json

text = '[{"name": "хлеб", "price": 40, "qty": 2}, {"name": "сыр", "price": 350, "qty": 1}]'
items = json.loads(text)
print(sum(i["price"] * i["qty"] for i in items))   # 430
```

## Файлы

```python
import json

settings = {"theme": "тёмная", "font": 18, "sound": True}
with open("settings.json", "w", encoding="utf-8") as f:
    json.dump(settings, f, ensure_ascii=False, indent=2)
with open("settings.json", encoding="utf-8") as f:
    print(json.load(f) == settings)    # True
```

## Ошибки

```python
import json

try:
    json.loads('{"a": 1,}')
except ValueError:
    print("некорректный JSON")
```

## Запомните

1. `s` в имени — работа со строкой, без `s` — с файлом.
2. `ensure_ascii=False` сохраняет кириллицу читаемой.
3. Всегда обрабатывайте `JSONDecodeError` (это `ValueError`) для внешних данных.
"""

a1 = fn_task("a1-to-json", "В читаемый JSON", "Напишите функцию `to_json(data)`, которая возвращает строку JSON: русские буквы **не** экранируются, ключи отсортированы (`sort_keys=True`), отступов нет.\n\nПример: `to_json({\"имя\": \"Аня\", \"b\": 1, \"a\": [1, 2]})` → `'{\"a\": [1, 2], \"b\": 1, \"имя\": \"Аня\"}'`.",
  "to_json", "import json\n\ndef to_json(data):\n    return json.dumps(data, ensure_ascii=False, sort_keys=True)\n",
  [[{"имя": "Аня", "b": 1, "a": [1, 2]}], [[]], ([{"z": None, "y": True}], True), ([{"город": "Москва"}], True), ([[1, "два", 3.5]], True)],
  [("import json\n\ndef to_json(data):\n    return json.dumps(data, sort_keys=True)\n", "Русские буквы экранированы кодами \\uXXXX."),
   ("import json\n\ndef to_json(data):\n    return json.dumps(data, ensure_ascii=False)\n", "Ключи не отсортированы."),
   ("def to_json(data):\n    return str(data)\n", "str() даёт запись Python (одинарные кавычки, True/None), а не JSON.")],
  hints("Для преобразования в JSON есть модуль json.", "Нужна функция dumps — она возвращает строку.", "Параметр ensure_ascii=False сохраняет русские буквы.", "Параметр sort_keys=True упорядочивает ключи.", "return json.dumps(data, ensure_ascii=False, sort_keys=True)."),
  "dumps превращает объект в строку JSON; два параметра делают результат читаемым и предсказуемым.")

a2 = fn_task("a2-total", "Стоимость заказа из JSON", "Функция `order_total(text)` получает строку JSON — список объектов с полями `price` и `qty` — и возвращает общую стоимость (сумму `price * qty`).\n\nПример: `order_total('[{\"price\": 40, \"qty\": 2}, {\"price\": 350, \"qty\": 1}]')` → `430`.",
  "order_total", "import json\n\ndef order_total(text):\n    items = json.loads(text)\n    return sum(i[\"price\"] * i[\"qty\"] for i in items)\n",
  [['[{"price": 40, "qty": 2}, {"price": 350, "qty": 1}]'], ["[]"], (['[{"price": 10, "qty": 0}]'], True), (['[{"price": 2.5, "qty": 4}, {"price": 1, "qty": 1}]'], True), (['[{"price": 7, "qty": 3, "name": "х"}]'], True)],
  [("import json\n\ndef order_total(text):\n    items = json.loads(text)\n    return sum(i[\"price\"] for i in items)\n", "Количество не учтено."),
   ("import json\n\ndef order_total(text):\n    return sum(i[\"price\"] * i[\"qty\"] for i in text)\n", "Строка не разобрана: перебираются символы текста."),
   ("import json\n\ndef order_total(text):\n    items = json.loads(text)\n    return len(items)\n", "Возвращено число позиций, а не стоимость.")],
  hints("Текст нужно превратить в список, а затем посчитать сумму.", "Функция loads разбирает строку JSON.", "Получится список словарей: читайте поля по ключам.", "Стоимость позиции — price * qty.", "return sum(i['price'] * i['qty'] for i in json.loads(text))."),
  "loads возвращает список словарей, к которым применимы обычные приёмы: обращение по ключу и sum с генератором.")

a3 = fn_task("a3-safe-parse", "Безопасный разбор", "Напишите функцию `safe_parse(text)`: возвращает объект, разобранный из JSON, а для некорректного JSON — `None`.",
  "safe_parse", "import json\n\ndef safe_parse(text):\n    try:\n        return json.loads(text)\n    except ValueError:\n        return None\n",
  [['{"a": 1}'], ['{"a": 1,}'], (["[1, 2, 3]"], True), (["не json"], True), (["null"], True), (["{"], True)],
  [("import json\n\ndef safe_parse(text):\n    return json.loads(text)\n", "Ошибка разбора не перехватывается."),
   ("import json\n\ndef safe_parse(text):\n    try:\n        return json.loads(text)\n    except ValueError:\n        return {}\n", "Для ошибки возвращается пустой словарь вместо None.")],
  hints("Некорректный JSON приводит к исключению.", "Разбор нужно поместить в try.", "JSONDecodeError — подвид ValueError.", "В except верните None.", "try: return json.loads(text); except ValueError: return None."),
  "Перехватывая ValueError, мы обрабатываем и JSONDecodeError. Заметьте: корректная строка «null» разбирается в None — это не ошибка.")

a4 = stdout_task("a4-average", "Среднее по JSON", "Во вводе одна строка с JSON-объектом вида `{\"name\": \"Аня\", \"marks\": [5, 4, 5]}`. Выведите `имя: среднее`, среднее округлите до двух знаков.\n\nВвод:\n```\n{\"name\": \"Аня\", \"marks\": [5, 4, 5]}\n```\nВывод:\n```\nАня: 4.67\n```",
  'import json\n\ndata = json.loads(input())\nprint(f"{data[\'name\']}: {sum(data[\'marks\']) / len(data[\'marks\']):.2f}")\n',
  ['{"name": "Аня", "marks": [5, 4, 5]}\n', ('{"name": "Борис", "marks": [3]}\n', True), ('{"marks": [4, 4, 5, 5], "name": "Вера"}\n', True)],
  [('import json\n\ndata = json.loads(input())\nprint(f"{data[\'name\']}: {sum(data[\'marks\']) / len(data[\'marks\'])}")\n', "Среднее не округлено до двух знаков."),
   ('import json\n\ndata = json.loads(input())\nprint(f"{data[\'name\']}: {sum(data[\'marks\']):.2f}")\n', "Выведена сумма вместо среднего.")],
  hints("Ввод — это строка JSON, её нужно разобрать.", "Для разбора строки используйте json.loads.", "Имя лежит по ключу name, оценки — по ключу marks.", "Среднее — сумма на количество.", "f-строка с :.2f округляет до двух знаков."),
  "Порядок ключей в JSON не важен: данные берутся по именам полей.")

a5 = predict_task("a5-types", "Типы после JSON", 'import json\n\ndata = {"a": (1, 2), "b": None, "c": True, "d": 1.0}\ntext = json.dumps(data)\nprint(text)\nback = json.loads(text)\nprint(back["a"], back["b"], back["c"])\nprint(type(back["a"]).__name__)\n',
  [('{"a": [1, 2], "b": null, "c": true, "d": 1.0}\n[1, 2] None True\ntuple\n', "После loads массив становится списком, а не кортежем."),
   ('{"a": (1, 2), "b": null, "c": true, "d": 1.0}\n(1, 2) None True\ntuple\n', "В JSON нет кортежей: они становятся массивами, а после загрузки — списками.")],
  hints("Подумайте, как JSON записывает Python-значения.", "None → null, True → true, кортеж → массив.", "Обратите внимание: в строке JSON после двоеточия и запятых стоят пробелы.", "После loads массив становится списком.", "Типы: back['a'] — list."),
  "JSON знает только объекты, массивы, строки, числа, true/false/null — поэтому кортеж превращается в массив и возвращается как список.")

mistakes = [
 {"mistake": "Путают dumps/loads и dump/load", "fix": "С буквой s — строки (string), без неё — файлы."},
 {"mistake": "JSON с одинарными кавычками или хвостовой запятой", "fix": "В JSON только двойные кавычки и нет запятой после последнего элемента.", "errorType": "JSONDecodeError"},
 {"mistake": "Русские буквы превращаются в \\u0420…", "fix": "Передайте ensure_ascii=False."},
 {"mistake": "Ждут, что кортеж вернётся кортежем", "fix": "JSON не различает кортежи и списки: после load получится список."}]

finish("py-18-json", "JSON", "Преобразовывать данные Python в JSON и обратно, сохранять их в файл и обрабатывать некорректный JSON.",
  {"python.json": "Модуль json: dumps и loads", "python.json.files": "JSON и файлы: dump и load", "python.json.errors": "Ошибки разбора JSON"},
  ["py-17-files"], scenes, notes, [a1, a2, a3, a4], mistakes, pack="python-core")

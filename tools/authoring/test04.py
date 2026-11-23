from lib import *

begin()
scenes = [
 S("intro", "Как искать ошибки", """
  Отладка — это поиск причины, по которой программа ведёт себя не так, как вы ожидали. Новички часто меняют код наугад в
  надежде, что ошибка пропадёт. Опытные разработчики действуют иначе, как учёные. Сначала воспроизводят ошибку на
  минимальном примере. Затем строят гипотезу, почему так происходит. Проверяют её, печатая промежуточные значения. Исправляют
  причину, а не симптом. И в конце записывают тест, чтобы ошибка не вернулась.""",
  nt("Воспроизвести → гипотеза → проверить → исправить → тест", at="Сначала воспроизводят")),
 S("errors", "Читаем сообщение об ошибке", """
  Сообщение об ошибке — лучшая подсказка. Читать его нужно с последней строки: там тип ошибки и причина. Покажем частые
  ошибки одну за другой. Обращение к несуществующему индексу даёт IndexError, к несуществующему ключу словаря — KeyError,
  неверное преобразование строки — ValueError, а вызов метода у значения None — AttributeError. Название сразу сужает поиск.""",
  clr(), t('checks = [\n    lambda: [1, 2][5],\n    lambda: {"a": 1}["b"],\n    lambda: int("x1"),\n    lambda: None.upper(),\n]\nfor check in checks:\n    try:\n        check()\n    except Exception as e:\n        print(type(e).__name__, "-", e)\n', at="Покажем"), run("Название")),
 S("prints", "Отладка печатью", """
  Самый простой инструмент — печать промежуточных значений. Функция должна находить сумму положительных чисел, но
  возвращает не то. Добавим печать внутри цикла: видим, что число минус три тоже попало в сумму. Причина найдена:
  условие проверяет не то. Не забывайте подписывать выводимые значения, иначе в длинном выводе легко запутаться.""",
  clr(), t("def sum_positive(numbers):\n    total = 0\n    for n in numbers:\n        if n != 0:\n            total += n\n            print(\"взяли\", n, \"сумма\", total)\n    return total\n\n", at="Функция должна"),
  t("print(sum_positive([4, -3, 2]))\n", at="Добавим"), run("Причина найдена")),
 S("logging", "Модуль logging", """
  Печать удобна, но потом её приходится удалять. Для постоянной диагностики есть модуль logging. У сообщений есть уровни
  важности: debug для подробностей, info для обычных событий, warning для предупреждений и error для ошибок. Настройка
  задаёт минимальный уровень: всё, что ниже, не показывается. Поставим уровень debug и увидим все четыре сообщения. А в
  рабочей программе уровень повышают, и подробности пропадают без изменения кода.""",
  clr(), t('import logging\nimport sys\n\nlogging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="%(levelname)s: %(message)s")\n\n', at="Для постоянной"),
  t('logging.debug("подробность: x=5")\nlogging.info("программа запущена")\nlogging.warning("диск почти полон")\nlogging.error("не удалось открыть файл")\n', at="Поставим"), run("А в")),
 S("bisect", "Сужаем поиск", """
  Если ошибка где-то в цепочке шагов, помогает деление пополам. Цепочка: очистить текст, разбить на слова, посчитать длины. Мы
  печатаем результат после каждого шага и сразу видим, на каком из них данные становятся неверными. Это быстрее, чем
  читать весь код подряд. Так же можно искать и неверную строку входного файла: проверить первую половину, потом вторую.""",
  clr(), t('text = "  Привет,  мир!  "\nstep1 = text.strip()\nprint("1:", repr(step1))\nstep2 = step1.split(" ")\nprint("2:", step2)\nstep3 = [len(w) for w in step2]\nprint("3:", step3)\n', at="Мы"), run("Это быстрее")),
 S("classics", "Классические ловушки", """
  Несколько ошибок встречаются постоянно. Первая — граница диапазона: range пять даёт числа от нуля до четырёх, пятёрки в нём
  нет. Вторая — изменяемое значение по умолчанию. Если написать список как значение параметра, он создаётся один раз и
  сохраняется между вызовами функции. Решение — указать None и создавать список внутри. Покажем обе.""",
  clr(), t("print(list(range(5)))\n\n", at="Первая"),
  t("def add(item, bag=[]):\n    bag.append(item)\n    return bag\n\nprint(add(1))\nprint(add(2))\n", at="Вторая"), run("Покажем обе")),
 S("summary", "Итог", """
  Подведём итог. Не угадывайте: воспроизведите ошибку, прочитайте сообщение с последней строки, выясните значения
  переменных печатью или logging и сузьте поиск. Исправляйте причину, а не симптом, и записывайте тест, чтобы ошибка не
  вернулась. Знание классических ловушек сильно ускоряет работу.""",
  nt("Читайте ошибку снизу · печатайте значения · logging вместо print · после исправления — тест", at="Подведём итог")),
]

notes = """
# Отладка

## Типы ошибок

- `IndexError` — индекс вне списка
- `KeyError` — нет ключа в словаре
- `ValueError` — неверное значение (например, `int("x1")`)
- `AttributeError` — у значения нет такого метода (часто `None`)

## logging

```python
import logging, sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="%(levelname)s: %(message)s")
logging.info("запуск")
logging.warning("предупреждение")
```

Уровни по возрастанию: DEBUG, INFO, WARNING, ERROR.

## Классические ловушки

- `range(5)` даёт 0…4
- значение по умолчанию `[]` общее для всех вызовов: используйте `None`
- изменение списка во время обхода

## Метод

Воспроизвести → гипотеза → проверить → исправить → написать тест.
"""

a1 = predict_task("a1-logging", "Что покажет logging",
  'import logging\nimport sys\n\nlogging.basicConfig(level=logging.WARNING, stream=sys.stdout, format="%(levelname)s: %(message)s")\n\nlogging.debug("шаг 1")\nlogging.info("шаг 2")\nlogging.warning("шаг 3")\nlogging.error("шаг 4")\n',
  [("DEBUG: шаг 1\nINFO: шаг 2\nWARNING: шаг 3\nERROR: шаг 4", "Уровень WARNING скрывает debug и info."), ("WARNING: шаг 3", "Сообщение error тоже выше порога — оно будет показано.")],
  hints("Порог — WARNING: ниже его сообщения не показываются.", "debug и info ниже порога.", "warning равно порогу — показывается.", "error выше порога — показывается.", "Формат: УРОВЕНЬ: текст."),
  "Показываются сообщения уровня не ниже заданного: WARNING и ERROR.")

a2 = predict_task("a2-errors", "Тип ошибки",
  'tests = [\n    lambda: [10, 20][2],\n    lambda: {"x": 1}["y"],\n    lambda: int("12.5"),\n    lambda: None.strip(),\n]\nfor t in tests:\n    try:\n        t()\n    except Exception as e:\n        print(type(e).__name__)\n',
  [("IndexError\nKeyError\nTypeError\nAttributeError", "int(\"12.5\") даёт ValueError, а не TypeError."), ("IndexError\nValueError\nKeyError\nAttributeError", "Порядок строк соответствует порядку проверок.")],
  hints("Четыре проверки — четыре строки вывода.", "Индекс 2 в списке из двух элементов: IndexError.", "Ключа «y» нет: KeyError.", "int из строки с точкой: ValueError.", "Метод у None: AttributeError."),
  "Тип ошибки подсказывает причину: индекс, ключ, значение или отсутствующий атрибут.")

a3 = stdout_task("a3-mutable", "Общий список",
  "Функция `add_item(item, items=[])` добавляет элемент в список и возвращает его. Программа должна напечатать `['a']` и `['b']`, но печатает `['a']` и `['a', 'b']`. Найдите причину и исправьте функцию.",
  "def add_item(item, items=None):\n    if items is None:\n        items = []\n    items.append(item)\n    return items\n\n\nprint(add_item(\"a\"))\nprint(add_item(\"b\"))\n",
  [""],
  [("def add_item(item, items=[]):\n    items = items[:]\n    items.append(item)\n    return items\n\n\nprint(add_item(\"a\"))\nprint(add_item(\"b\"))\n", "Работает, но копирует список: не то, что требуется? (этот вариант тоже корректен)")][:0] or [("def add_item(item, items=[]):\n    items.append(item)\n    return items\n\n\nprint(add_item(\"a\"))\nprint(add_item(\"b\"))\n", "Исходная версия: список общий для всех вызовов.")],
  hints("Значение по умолчанию создаётся один раз — при определении функции.", "Список-значение по умолчанию общий для всех вызовов.", "Нужно создавать новый список при каждом вызове без аргумента.", "Типичный приём: значение по умолчанию None.", "Внутри: если items равно None — создать пустой список."),
  "Значение по умолчанию вычисляется один раз. Изменяемое значение разделяется между вызовами; безопасно использовать None и создавать объект внутри.",
  type="fix", starter="def add_item(item, items=[]):\n    items.append(item)\n    return items\n\n\nprint(add_item(\"a\"))\nprint(add_item(\"b\"))\n")

a4 = fn_task("a4-sum-to", "Сумма от 1 до n",
  "Функция должна вернуть сумму чисел от 1 до `n` включительно. Сейчас результат всегда меньше нужного. Найдите ошибку границы и исправьте.",
  "sum_to", "def sum_to(n):\n    total = 0\n    for i in range(1, n + 1):\n        total += i\n    return total\n",
  [[5], [1], ([0], True), ([10], True), ([100], True)],
  [("def sum_to(n):\n    total = 0\n    for i in range(1, n):\n        total += i\n    return total\n", "Последнее число n не попадает в сумму.")],
  hints("Проверьте вручную: сумма от 1 до 5 равна 15.", "Что даёт range(1, 5)?", "Конец диапазона не включается.", "Чтобы включить n, конец должен быть на единицу больше.", "range(1, n + 1)."),
  "range(a, b) не включает b. Чтобы включить n, конец диапазона — n + 1.",
  type="fix", starter="def sum_to(n):\n    total = 0\n    for i in range(1, n):\n        total += i\n    return total\n")

a5 = stdout_task("a5-log-negative", "Журнал предупреждений",
  "Первая строка ввода — `n`, далее `n` целых чисел (каждое в своей строке). Настройка `logging` уже сделана. Для каждого отрицательного числа запишите предупреждение `WARNING: пропущено X` (через `logging.warning`), остальные числа сложите. В конце выведите через `logging.info` строку `INFO: сумма S`.",
  'import logging\nimport sys\n\nlogging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s: %(message)s", force=True)\n\nn = int(input())\ntotal = 0\nfor _ in range(n):\n    value = int(input())\n    if value < 0:\n        logging.warning("пропущено %d", value)\n    else:\n        total += value\nlogging.info("сумма %d", total)\n',
  ["3\n4\n-2\n5\n", ("2\n-1\n-7\n", True), ("1\n0\n", True), ("0\n", True)],
  [('import logging\nimport sys\n\nlogging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s: %(message)s", force=True)\n\nn = int(input())\ntotal = 0\nfor _ in range(n):\n    value = int(input())\n    total += value\nlogging.info("сумма %d", total)\n', "Отрицательные числа не пропускаются и не журналируются.")],
  hints("Прочитайте n, затем в цикле по n чисел.", "Для отрицательного числа вызовите logging.warning.", "Остальные числа добавляйте в сумму.", "Текст предупреждения: пропущено и число.", "После цикла — logging.info с суммой."),
  "logging.warning и logging.info печатают строки с уровнем. Формат задан в basicConfig, поэтому достаточно написать только текст.",
  starter='import logging\nimport sys\n\nlogging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s: %(message)s", force=True)\n\nn = int(input())\n# ваш код\n', type="complete")

mistakes = [
 {"mistake": "Меняют код наугад", "fix": "Сначала воспроизведите ошибку и сформулируйте гипотезу."},
 {"mistake": "Читают traceback сверху", "fix": "Смотрите на последнюю строку: там тип и причина."},
 {"mistake": "Оставляют отладочные print в коде", "fix": "Используйте logging: уровнем управляют настройкой."},
 {"mistake": "Лечат симптом, а не причину", "fix": "Найдите, почему значение стало неверным, и добавьте тест."}]

finish("test-04-debugging", "Отладка и logging", "Читать сообщения об ошибках, находить причину печатью и logging, избегать классических ловушек.",
  {"debug.traceback": "Чтение ошибок", "debug.logging": "logging", "debug.traps": "Классические ловушки"},
  ["test-03-edge-cases"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="testing-debugging")

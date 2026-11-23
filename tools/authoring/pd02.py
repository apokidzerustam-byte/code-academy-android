from lib import *

begin()
scenes = [
 S("intro", "Что такое рефакторинг", """
  Рефакторинг — это улучшение структуры кода без изменения его поведения. Вы не добавляете функции и не чините ошибки, а
  наводите порядок: убираете повторы, упрощаете условия, даёте понятные имена. Главное правило: после рефакторинга программа
  должна делать ровно то же, что и до него. Чтобы это гарантировать, нужны тесты или хотя бы сравнение старой и новой версий.""",
  nt("**Рефакторинг** = та же работа, лучше устроенный код · тесты — страховка", at="Главное правило")),
 S("dup", "Убираем повторы", """
  Когда один и тот же кусок кода скопирован в нескольких местах, любую правку придётся вносить везде, и одно место легко
  забыть. Здесь два раза считается цена со скидкой: копия на копии. Вынесите повторяющуюся часть в функцию discounted, и
  результат не изменится.""",
  clr(), t('def before(price_a, price_b):\n    a = price_a - price_a * 10 / 100\n    b = price_b - price_b * 10 / 100\n    return a + b\n\n\n', at="Здесь два раза"),
  t('def discounted(price, percent=10):\n    return price - price * percent / 100\n\n\ndef after(price_a, price_b):\n    return discounted(price_a) + discounted(price_b)\n\n\n', at="Вынесите"),
  t('print(before(100, 50), after(100, 50))\n', at="результат не"), run("результат не")),
 S("dict", "Таблица вместо цепочки if", """
  Длинная цепочка условий, которые отличаются только значением, лучше заменяется словарём. Данные отдельно, логика отдельно:
  чтобы добавить новый тип клиента, достаточно добавить строку в словарь, а функцию трогать не нужно. Метод get с значением
  по умолчанию обрабатывает неизвестный ключ без ошибки.""",
  clr(), t('DISCOUNTS = {"regular": 0, "silver": 5, "gold": 10, "vip": 20}\n\n\ndef discount_for(kind):\n    return DISCOUNTS.get(kind, 0)\n\n\n', at="Данные отдельно"),
  t('print(discount_for("gold"))\nprint(discount_for("unknown"))\n', at="Метод get"), run("Метод get")),
 S("builtin", "Встроенные функции и выражения", """
  Цикл с накоплением часто заменяется встроенной функцией. Подсчёт взрослых, сумма, проверка «есть ли хоть один» — всё это
  записывается одной строкой через sum, any и all с генераторным выражением. Код становится короче и точнее выражает идею.
  Но не жертвуйте читаемостью: если выражение не помещается в одну понятную строку, оставьте обычный цикл.""",
  clr(), t('people = [{"age": 17}, {"age": 30}, {"age": 18}]\n\n\ndef count_adults(items):\n    return sum(1 for p in items if p["age"] >= 18)\n\n\n', at="Подсчёт"),
  t('print(count_adults(people))\nprint(any(p["age"] < 18 for p in people))\nprint(all(p["age"] >= 18 for p in people))\n', at="Но не жертвуйте"), run("Но не жертвуйте")),
 S("safety", "Страховка: сравнение версий", """
  Как убедиться, что рефакторинг ничего не сломал? Запустите старую и новую версии на множестве входных данных и сравните
  результаты. Если они совпали везде, поведение сохранилось. Это простой, но мощный приём, особенно когда нет готовых
  тестов. Не забывайте включить в проверку граничные значения: ноль, отрицательные числа и пустые списки.""",
  clr(), t('def old(n):\n    total = 0\n    for i in range(1, n + 1):\n        total += i\n    return total\n\n\ndef new(n):\n    return n * (n + 1) // 2\n\n\n', at="Запустите"),
  t('print(all(old(n) == new(n) for n in range(0, 100)))\n', at="Если они"), run("Если они")),
 S("summary", "Итог", """
  Подведём итог. Рефакторинг меняет структуру, а не поведение. Повторы выносите в функции, цепочки одинаковых условий
  заменяйте словарями, циклы накопления — sum, any, all. Перед правкой и после неё сравнивайте поведение на разных
  входных данных. Делайте маленькие шаги и после каждого проверяйте результат. Тогда рефакторинг не страшен.""",
  nt("повторы → функция · if-цепочка → словарь · цикл → sum/any/all · проверка до и после", at="Подведём итог")),
]

notes = """
# Рефакторинг

```python
DISCOUNTS = {"regular": 0, "silver": 5, "gold": 10, "vip": 20}

def discounted(price, percent=10):
    return price - price * percent / 100

def discount_for(kind):
    return DISCOUNTS.get(kind, 0)

def count_adults(items):
    return sum(1 for p in items if p["age"] >= 18)

def old(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total

def new(n):
    return n * (n + 1) // 2

print(all(old(n) == new(n) for n in range(100)))
```

Маленькие шаги · проверка после каждого шага · граничные значения.
"""

a1 = predict_task("a1-compare", "Совпадают ли версии",
  'def old(items):\n    for x in items:\n        if x > 10:\n            return True\n    return False\n\n\ndef new(items):\n    return any(x > 10 for x in items)\n\n\ndef broken(items):\n    return all(x > 10 for x in items)\n\n\nfor data in ([], [5], [20], [5, 20]):\n    print(old(data) == new(data), old(data) == broken(data))\n',
  [("True True\nTrue True\nTrue True\nTrue True", "Версия broken отличается на пустом списке и смешанных данных."), ("True False\nTrue True\nTrue False\nTrue False", "На списке [20] версии all и old совпадают.")],
  hints("old и new — одно и то же; broken другая.", "Первое сравнение всегда True.", "Для [] old даёт False, а all([]) даёт True.", "Для [5] обе версии дают False.", "Для [20] — True; для [5, 20] old даёт True, all даёт False."),
  "all для пустого списка истинен, any — ложен: на пустых данных версии легко различаются.")

a2 = fn_task("a2-discount-table", "Скидка по таблице",
  "Перепишите `discount_percent(kind)` без цепочки `if`: словарь `regular=0`, `silver=5`, `gold=10`, `vip=20`; для неизвестного типа верните 0.",
  "discount_percent", "DISCOUNTS = {\"regular\": 0, \"silver\": 5, \"gold\": 10, \"vip\": 20}\n\n\ndef discount_percent(kind):\n    return DISCOUNTS.get(kind, 0)\n",
  [["gold"], ["unknown"], (["regular"], True), (["vip"], True), (["silver"], True), ([""], True)],
  [("DISCOUNTS = {\"regular\": 0, \"silver\": 5, \"gold\": 10, \"vip\": 20}\n\n\ndef discount_percent(kind):\n    return DISCOUNTS[kind]\n", "Неизвестный тип приводит к ошибке."),
   ("DISCOUNTS = {\"regular\": 0, \"silver\": 5, \"gold\": 10, \"vip\": 20}\n\n\ndef discount_percent(kind):\n    return DISCOUNTS.get(kind, 5)\n", "Для неизвестных типов нужен 0.")],
  hints("Данные удобно хранить в словаре.", "Ключ — тип клиента, значение — процент.", "Обычное обращение по ключу падает на неизвестном ключе.", "Метод get принимает значение по умолчанию.", "По умолчанию — ноль."),
  "Словарь превращает цепочку условий в данные; get с умолчанием — защита от неизвестных ключей.",
  type="write", starter="def discount_percent(kind):\n    if kind == \"regular\":\n        return 0\n    elif kind == \"silver\":\n        return 5\n    elif kind == \"gold\":\n        return 10\n    elif kind == \"vip\":\n        return 20\n    return 0\n")

a3 = fn_task("a3-adults", "Подсчёт совершеннолетних",
  "Напишите `count_adults(people)`: сколько людей в списке словарей с ключом `\"age\"` имеют возраст **не меньше 18**. Используйте `sum` с генераторным выражением.",
  "count_adults", "def count_adults(people):\n    return sum(1 for p in people if p[\"age\"] >= 18)\n",
  [[[{"age": 17}, {"age": 30}, {"age": 18}]], [[]], ([[{"age": 18}]], True), ([[{"age": 5}, {"age": 6}]], True), ([[{"age": 40}, {"age": 41}, {"age": 17}]], True)],
  [("def count_adults(people):\n    return sum(1 for p in people if p[\"age\"] > 18)\n", "Восемнадцатилетние не учтены."),
   ("def count_adults(people):\n    return len(people)\n", "Считаются все люди.")],
  hints("Нужно посчитать подходящих людей.", "Условие: возраст не меньше 18.", "Для подсчёта удобно суммировать единицы.", "Для каждого человека — единица, если условие выполнено.", "Для пустого списка получится ноль."),
  "sum(1 for … if …) считает элементы, подходящие под условие, без отдельной переменной-счётчика.")

a4 = fn_task("a4-perimeter", "Периметр",
  "Исправьте `perimeter(shape)`. Фигура — кортеж: `(\"rect\", w, h)` или `(\"square\", side)`. Периметр прямоугольника — `2 * (w + h)`, квадрата — `4 * side`. Уберите повтор: квадрат — частный случай прямоугольника.",
  "perimeter", "def rect_perimeter(w, h):\n    return 2 * (w + h)\n\n\ndef perimeter(shape):\n    if shape[0] == \"square\":\n        return rect_perimeter(shape[1], shape[1])\n    return rect_perimeter(shape[1], shape[2])\n",
  [[["rect", 3, 4]], [["square", 5]], ([["square", 1]], True), ([["rect", 10, 1]], True), ([["square", 0]], True)],
  [("def perimeter(shape):\n    if shape[0] == \"square\":\n        return shape[1] * shape[1]\n    return 2 * (shape[1] + shape[2])\n", "Для квадрата считается площадь."),
   ("def perimeter(shape):\n    if shape[0] == \"square\":\n        return 2 * shape[1]\n    return 2 * (shape[1] + shape[2])\n", "Для квадрата нужно четыре стороны.")],
  hints("Ошибка в формуле для квадрата.", "Периметр — сумма длин всех сторон.", "У квадрата четыре равные стороны.", "Квадрат — это прямоугольник с равными сторонами.", "Вынесите формулу прямоугольника в отдельную функцию."),
  "Квадрат — частный случай прямоугольника: одна формула вместо двух, и исправление в одном месте.",
  type="fix", starter="def perimeter(shape):\n    if shape[0] == \"square\":\n        return shape[1] * shape[1]\n    return 2 * (shape[1] + shape[2])\n")

a5 = fn_task("a5-same", "Тот же результат",
  "Напишите `all_positive(numbers)`: `True`, если **все** числа списка положительные, иначе `False`; для пустого списка — `False`. Используйте `all`, но не забудьте про пустой список.",
  "all_positive", "def all_positive(numbers):\n    return bool(numbers) and all(n > 0 for n in numbers)\n",
  [[[1, 2, 3]], [[1, -2]], ([[]], True), ([[0]], True), ([[5]], True), ([[-1]], True)],
  [("def all_positive(numbers):\n    return all(n > 0 for n in numbers)\n", "Для пустого списка вернётся True."),
   ("def all_positive(numbers):\n    return bool(numbers) and all(n >= 0 for n in numbers)\n", "Ноль не положительное число.")],
  hints("all сам по себе истинен для пустого списка.", "Для пустого списка нужен отдельный ответ.", "Проверьте, что список не пуст.", "Положительное — строго больше нуля.", "Соедините обе проверки логическим «и»."),
  "all([]) — True: при рефакторинге циклов в all важно отдельно обработать пустой ввод.")

mistakes = [
 {"mistake": "Меняют поведение и структуру одновременно", "fix": "Рефакторинг — только структура; ошибки чините отдельным шагом."},
 {"mistake": "Рефакторят без проверки", "fix": "Сравнивайте старую и новую версии на разных данных."},
 {"mistake": "Забывают про пустой ввод в all/any", "fix": "all([]) истинно, any([]) ложно."},
 {"mistake": "Делают выражение слишком хитрым", "fix": "Если трудно прочитать, оставьте обычный цикл."}]

finish("pd-02-refactoring", "Рефакторинг", "Улучшать структуру кода, сохраняя поведение, и проверять это сравнением версий.",
  {"pro.refactoring": "Рефакторинг", "pro.dry": "Устранение повторов", "pro.compare": "Сравнение версий"},
  ["pd-01-readable-code"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="prof-dev")

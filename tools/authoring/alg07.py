from lib import *

begin()
scenes = [
 S("intro", "Мгновенный поиск по ключу", """
  Как найти телефон в списке контактов, если их тысяча? Перебирать все долго. Хеш-таблица позволяет находить значение по ключу
  практически мгновенно, за константное время, независимо от размера данных. Именно так устроены словари dict и множества set
  в Python. Сегодня мы заглянем внутрь: разберёмся, что такое хеш-функция и коллизия, напишем простую таблицу сами и увидим,
  как словари помогают решать задачи подсчёта и поиска пар.""",
  nt("**Хеш-таблица**: ключ → хеш-функция → номер корзины → значение. Поиск за O(1) в среднем", at="Хеш-таблица позволяет")),
 S("hash", "Хеш-функция", """
  Хеш-функция превращает ключ в число. Затем остаток от деления на размер таблицы даёт номер ячейки, или корзины. Возьмём
  самую простую функцию: сумма кодов символов строки. Функция ord возвращает код символа. Для одинаковых ключей результат
  всегда один и тот же, а для разных — обычно разный, но не всегда. Посмотрим, в какие из пяти корзин попадут несколько имён.""",
  clr(), t("def bucket(key, size):\n    return sum(ord(ch) for ch in key) % size\n\n", at="Возьмём"),
  t('for name in ["Аня", "Борис", "Вера", "Глеб"]:\n    print(name, bucket(name, 5))\n', at="Посмотрим"), run("Посмотрим")),
 S("collision", "Коллизии и цепочки", """
  Два разных ключа могут попасть в одну корзину. Такая ситуация называется коллизией, и она неизбежна. Простое решение —
  метод цепочек: каждая корзина хранит список пар «ключ — значение». При поиске мы вычисляем номер корзины и просматриваем
  только короткий список в ней. Если таблица достаточно большая, цепочки остаются короткими, и поиск остаётся быстрым.""",
  clr(), t("def bucket(key, size):\n    return sum(ord(ch) for ch in key) % size\n\n", at="Два разных"),
  t("def put(table, key, value):\n    chain = table[bucket(key, len(table))]\n    for pair in chain:\n        if pair[0] == key:\n            pair[1] = value\n            return\n    chain.append([key, value])\n\n", at="метод цепочек"),
  t("def get(table, key):\n    for k, v in table[bucket(key, len(table))]:\n        if k == key:\n            return v\n    return None\n\n", at="При поиске"),
  t('table = [[] for _ in range(3)]\nfor name, age in [("Аня", 20), ("Борис", 25), ("Вера", 30), ("Аня", 21)]:\n    put(table, name, age)\nprint(table)\nprint(get(table, "Аня"), get(table, "Зоя"))\n', at="Если таблица"), run("Если таблица")),
 S("dict", "Словарь и множество в работе", """
  В реальных программах хеш-таблицу писать не нужно: есть dict и set. Ключи словаря должны быть неизменяемыми: строки, числа,
  кортежи подходят, списки — нет. Множество хранит уникальные значения и позволяет мгновенно проверять наличие элемента.
  Проверка оператором in в множестве работает за константное время, а в списке — за линейное.""",
  clr(), t('ages = {"Аня": 20, "Борис": 25}\nprint("Аня" in ages, ages.get("Зоя", 0))\n', at="Ключи словаря"),
  t("seen = set()\nfor x in [3, 1, 3, 2, 1]:\n    seen.add(x)\nprint(sorted(seen), 2 in seen)\n", at="Множество хранит"), run("Проверка")),
 S("count", "Подсчёт частот", """
  Одна из самых частых задач — посчитать, сколько раз встречается каждый элемент. Заведём словарь и для каждого элемента
  увеличиваем счётчик. Метод get со значением по умолчанию избавляет от проверки наличия ключа. Подсчитаем буквы в слове
  «ананас».""",
  clr(), t('word = "ананас"\ncounts = {}\n', at="Заведём"),
  t("for ch in word:\n    counts[ch] = counts.get(ch, 0) + 1\n", at="Метод get"),
  t("print(counts)\n", at="Подсчитаем"), run("Подсчитаем")),
 S("twosum", "Поиск пары за один проход", """
  Задача: в списке чисел найти два, дающих в сумме заданную цель. Перебор всех пар медленный. Хеш-таблица решает это за один
  проход: запоминаем в словаре, какие числа мы уже видели и на каких индексах. Для текущего числа ищем в словаре
  дополнение — цель минус число. Если оно уже встречалось, пара найдена.""",
  clr(), t("def two_sum(nums, target):\n    seen = {}\n", at="запоминаем"),
  t("    for i, x in enumerate(nums):\n        if target - x in seen:\n            return [seen[target - x], i]\n        seen[x] = i\n    return None\n\n", at="дополнение"),
  t("print(two_sum([2, 7, 11, 15], 9))\n", at="Если оно"), run("Если оно")),
 S("summary", "Итог", """
  Подведём итог. Хеш-таблица превращает ключ в номер корзины с помощью хеш-функции. Коллизии решаются цепочками. В Python
  это dict и set, и они дают поиск за константное время в среднем. Ключами могут быть только неизменяемые объекты. Словари
  отлично подходят для подсчёта, группировки и быстрого поиска. Дальше — иерархические структуры данных: деревья.""",
  nt("`dict`, `set` — O(1) в среднем · ключ должен быть **hashable**", at="Подведём итог")),
]

notes = """
# Хеш-таблицы

```python
def bucket(key, size):
    return sum(ord(ch) for ch in key) % size

def put(table, key, value):
    chain = table[bucket(key, len(table))]
    for pair in chain:
        if pair[0] == key:
            pair[1] = value
            return
    chain.append([key, value])

def get(table, key):
    for k, v in table[bucket(key, len(table))]:
        if k == key:
            return v
    return None
```

## Подсчёт и пары

```python
counts = {}
for ch in "ананас":
    counts[ch] = counts.get(ch, 0) + 1

def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
```

## Запомните

1. Коллизия — разные ключи в одной корзине; решаем цепочками.
2. Ключи `dict` и элементы `set` — только неизменяемые.
3. `x in set` и `dict[key]` — O(1) в среднем; `x in list` — O(n).
"""

TS = 'def two_sum(nums, target):\n    seen = {}\n    for i, x in enumerate(nums):\n        if target - x in seen:\n            return [seen[target - x], i]\n        seen[x] = i\n    return None\n'
a1 = fn_task("a1-twosum", "Пара с заданной суммой", "Напишите `two_sum(nums, target)`: верните индексы `[i, j]` (`i < j`) двух разных элементов с суммой `target`; в тестах такая пара ровно одна. Если пары нет — `None`.\n\nПример: `two_sum([2, 7, 11, 15], 9)` → `[0, 1]`.",
  "two_sum", TS,
  [[[2, 7, 11, 15], 9], [[3, 2, 4], 6], ([[1, 2, 3], 100], True), ([[3, 3], 6], True), ([[5, 1, 8, 4], 12], True), ([[], 1], True)],
  [("def two_sum(nums, target):\n    for x in nums:\n        for y in nums:\n            if x + y == target:\n                return [x, y]\n    return None\n", "Возвращаются значения, а не индексы (и один элемент может быть взят дважды)."),
   ("def two_sum(nums, target):\n    seen = {}\n    for i, x in enumerate(nums):\n        seen[x] = i\n        if target - x in seen:\n            return [seen[target - x], i]\n    return None\n", "Число добавляется в словарь до проверки: может быть использовано само с собой."),
   ("def two_sum(nums, target):\n    seen = {}\n    for i, x in enumerate(nums):\n        if target - x in seen:\n            return [i, seen[target - x]]\n        seen[x] = i\n    return None\n", "Индексы возвращаются в обратном порядке.")],
  hints("Переберите числа и для каждого ищите «дополнение»: target - x.", "Быстрый поиск дополнения — словарь «число → индекс».", "Проверяйте дополнение до записи текущего числа в словарь.", "Нашли дополнение — верните его индекс и текущий.", "Иначе запомните seen[x] = i; в конце верните None."),
  "Словарь превращает поиск дополнения из O(n) в O(1), а всю задачу — в один проход.")

a2 = fn_task("a2-unique", "Первый уникальный символ", "Напишите `first_unique(s)`: верните **первый символ**, который встречается в строке ровно один раз; если такого нет — пустую строку `\"\"`.\n\nПример: `first_unique(\"swiss\")` → `\"w\"`.",
  "first_unique", 'def first_unique(s):\n    counts = {}\n    for ch in s:\n        counts[ch] = counts.get(ch, 0) + 1\n    for ch in s:\n        if counts[ch] == 1:\n            return ch\n    return ""\n',
  [["swiss"], ["aabb"], ([""], True), (["z"], True), (["abcab"], True), (["ааббв"], True)],
  [('def first_unique(s):\n    for ch in sorted(set(s)):\n        if s.count(ch) == 1:\n            return ch\n    return ""\n', "Выбирается первый по алфавиту, а не по порядку в строке."),
   ('def first_unique(s):\n    counts = {}\n    for ch in s:\n        counts[ch] = counts.get(ch, 0) + 1\n    for ch in s:\n        if counts[ch] == 1:\n            return ch\n', "Для строки без уникальных символов возвращается None вместо пустой строки.")],
  hints("Сначала нужно узнать, сколько раз встречается каждый символ.", "Подсчёт: counts[ch] = counts.get(ch, 0) + 1.", "Второй проход — по самой строке, чтобы сохранить порядок.", "Верните первый символ со счётом 1.", "Если такого нет — return ''."),
  "Два прохода: первый считает, второй сохраняет порядок появления. Итоговая сложность O(n).")

a3 = fn_task("a3-anagrams", "Группы анаграмм", "Напишите `group_anagrams(words)`: сгруппируйте слова-анаграммы (одинаковый набор букв). Верните список групп; внутри группы слова по алфавиту, сами группы — по первому слову.\n\nПример: `group_anagrams([\"кот\", \"ток\", \"дом\", \"мод\", \"лес\"])` → `[[\"дом\", \"мод\"], [\"кот\", \"ток\"], [\"лес\"]]`.",
  "group_anagrams", "def group_anagrams(words):\n    groups = {}\n    for word in words:\n        key = \"\".join(sorted(word))\n        groups.setdefault(key, []).append(word)\n    result = [sorted(group) for group in groups.values()]\n    return sorted(result, key=lambda g: g[0])\n",
  [[["кот", "ток", "дом", "мод", "лес"]], [[]], ([["а"]], True), ([["рак", "кар", "арк", "рок"]], True), ([["б", "а", "б"]], True)],
  [("def group_anagrams(words):\n    groups = {}\n    for word in words:\n        key = \"\".join(sorted(word))\n        groups.setdefault(key, []).append(word)\n    return list(groups.values())\n", "Группы и слова внутри групп не отсортированы."),
   ("def group_anagrams(words):\n    return [[w] for w in sorted(words)]\n", "Анаграммы не объединяются."),
   ("def group_anagrams(words):\n    groups = {}\n    for word in words:\n        key = len(word)\n        groups.setdefault(key, []).append(word)\n    result = [sorted(group) for group in groups.values()]\n    return sorted(result, key=lambda g: g[0])\n", "Ключ — длина слова, а не набор букв.")],
  hints("Анаграммы состоят из одних и тех же букв.", "Ключ группы — слово с отсортированными буквами.", "Словарь «ключ → список слов»: groups.setdefault(key, []).append(word).", "Отсортируйте слова в каждой группе.", "Отсортируйте группы по первому слову."),
  "Отсортированные буквы — одинаковый «отпечаток» всех анаграмм; словарь собирает слова с одним отпечатком.")

a4 = fn_task("a4-table", "Своя хеш-таблица", "Напишите `build_table(pairs, size)`: создайте таблицу из `size` пустых корзин (списков) и по очереди добавьте пары `[ключ, значение]` методом цепочек. Номер корзины — `сумма кодов символов ключа % size`. Если ключ уже есть в корзине, обновите значение. Верните список корзин, каждая — список пар `[ключ, значение]` в порядке добавления.",
  "build_table", "def build_table(pairs, size):\n    table = [[] for _ in range(size)]\n    for key, value in pairs:\n        chain = table[sum(ord(ch) for ch in key) % size]\n        for pair in chain:\n            if pair[0] == key:\n                pair[1] = value\n                break\n        else:\n            chain.append([key, value])\n    return table\n",
  [[[["Аня", 20], ["Борис", 25], ["Вера", 30], ["Аня", 21]], 3], [[], 2], ([[["a", 1], ["b", 2]], 1], True), ([[["a", 1], ["a", 2], ["a", 3]], 4], True), ([[["ab", 1], ["ba", 2], ["c", 3]], 5], True)],
  [("def build_table(pairs, size):\n    table = [[] for _ in range(size)]\n    for key, value in pairs:\n        chain = table[sum(ord(ch) for ch in key) % size]\n        chain.append([key, value])\n    return table\n", "Повторяющийся ключ добавляется второй раз вместо обновления."),
   ("def build_table(pairs, size):\n    table = [[] for _ in range(size)]\n    for key, value in pairs:\n        table[sum(ord(ch) for ch in key) % size] = [[key, value]]\n    return table\n", "Коллизии затирают предыдущие пары: нет цепочки."),
   ("def build_table(pairs, size):\n    table = [[] for _ in range(size)]\n    for key, value in pairs:\n        chain = table[len(key) % size]\n        for pair in chain:\n            if pair[0] == key:\n                pair[1] = value\n                break\n        else:\n            chain.append([key, value])\n    return table\n", "Номер корзины считается по длине ключа, а не по сумме кодов.")],
  hints("Таблица — список из size пустых списков.", "Номер корзины: sum(ord(ch) for ch in key) % size.", "Внутри корзины ищите ключ перед добавлением.", "Нашли — обновите значение, не нашли — добавьте пару.", "Конструкция for … else: else выполняется, если не было break."),
  "Цепочка защищает от потери данных при коллизиях; поиск по ключу внутри корзины перебирает короткий список.")

a5 = predict_task("a5-sets", "Множества и словари", 'a = {1, 2, 3}\nb = {3, 4}\nd = {}\nfor w in ["да", "нет", "да", "да"]:\n    d[w] = d.get(w, 0) + 1\nprint(sorted(a | b), a & b, len(a - b))\nprint(d)\n',
  [("[1, 2, 3, 4] {3} 3\n{'да': 3, 'нет': 1}\n", "a - b содержит {1, 2}, длина 2, а не 3."),
   ("[1, 2, 3, 3, 4] {3} 2\n{'да': 3, 'нет': 1}\n", "Объединение множеств не содержит повторов.")],
  hints("a | b — объединение: все элементы без повторов.", "a & b — пересечение: общие элементы.", "a - b — элементы a, которых нет в b.", "Словарь считает слова: «да» — 3 раза, «нет» — 1.", "Ответ: [1, 2, 3, 4] {3} 2."),
  "Множества не хранят повторов; операции |, &, - соответствуют объединению, пересечению и разности.")

mistakes = [
 {"mistake": "Кладут список в качестве ключа словаря", "fix": "Замените на кортеж: список изменяем и не имеет хеша.", "errorType": "TypeError"},
 {"mistake": "Проверяют наличие через список в цикле, хотя нужен быстрый поиск", "fix": "Превратите в set или dict: x in set — O(1)."},
 {"mistake": "Обращаются к отсутствующему ключу dict[key]", "fix": "Используйте dict.get(key, default).", "errorType": "KeyError"},
 {"mistake": "Рассчитывают на порядок элементов множества", "fix": "У set нет порядка; для вывода используйте sorted."}]

finish("alg-07-hash", "Хеш-таблицы", "Понимать устройство хеш-таблиц и использовать dict/set для подсчёта, группировки и поиска пар.",
  {"algo.hash": "Хеш-таблицы", "algo.hash.collision": "Коллизии и цепочки"},
  ["alg-06-stack-queue"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="algorithms")

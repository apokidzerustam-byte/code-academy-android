from lib import *

begin()
scenes = [
 S("intro", "Зачем сортировать", """
  Отсортированные данные удобнее во всём: по ним быстро искать, легко находить минимум и максимум, их приятно читать.
  Список покупок по цене, задачи по сроку, расходы по дате — везде нужна сортировка. В этом уроке мы напишем три простых
  алгоритма, поймём, как они работают шаг за шагом, и узнаем, почему на практике почти всегда используют встроенную
  функцию sorted. Простые алгоритмы медленные, но именно на них хорошо видна сама идея сортировки.""",
  nt("Простые сортировки: пузырьком, выбором, вставками. Все — O(n²)", at="Простые алгоритмы")),
 S("bubble", "Сортировка пузырьком", """
  Идея пузырька такая: идём по списку и сравниваем соседние элементы. Если левый больше правого, меняем их местами. После
  одного прохода самый большой элемент всплывает в конец списка, как пузырёк. Повторяем проходы, пока на очередном проходе
  не останется ни одной перестановки. Обмен значений в Python записывается одной строкой: a запятая b равно b запятая a.
  Проверим на небольшом списке.""",
  clr(), t("def bubble_sort(items):\n    items = list(items)\n    swapped = True\n", at="Идея пузырька"),
  t("    while swapped:\n        swapped = False\n        for i in range(len(items) - 1):\n", at="Повторяем проходы"),
  t("            if items[i] > items[i + 1]:\n                items[i], items[i + 1] = items[i + 1], items[i]\n                swapped = True\n", at="Обмен значений"),
  t("    return items\n\nprint(bubble_sort([5, 2, 9, 1, 7]))\n", at="Проверим"), run("Проверим")),
 S("selection", "Сортировка выбором", """
  Сортировка выбором работает иначе. На каждом шаге мы находим минимальный элемент в ещё не отсортированной части и
  ставим его на нужное место. Сначала ищем минимум среди всех и меняем с первым элементом. Затем минимум среди оставшихся и
  меняем со вторым, и так далее. Перестановок здесь немного, но сравнений всегда много: их число не зависит от того, насколько
  список уже упорядочен.""",
  clr(), t("def selection_sort(items):\n    items = list(items)\n    for i in range(len(items)):\n        smallest = i\n", at="На каждом шаге"),
  t("        for j in range(i + 1, len(items)):\n            if items[j] < items[smallest]:\n                smallest = j\n", at="Сначала ищем"),
  t("        items[i], items[smallest] = items[smallest], items[i]\n    return items\n\nprint(selection_sort([5, 2, 9, 1, 7]))\n", at="меняем с первым"), run("Перестановок")),
 S("insertion", "Сортировка вставками", """
  Сортировка вставками похожа на то, как мы раскладываем карты в руке. Левая часть списка уже отсортирована. Берём очередной
  элемент и сдвигаем его влево, пока он меньше соседа. Для почти отсортированных данных это очень быстро, потому что сдвигов
  почти нет. Поэтому вставки нередко используют внутри более сложных алгоритмов для маленьких кусочков.""",
  clr(), t("def insertion_sort(items):\n    items = list(items)\n    for i in range(1, len(items)):\n        j = i\n", at="Берём очередной"),
  t("        while j > 0 and items[j - 1] > items[j]:\n            items[j - 1], items[j] = items[j], items[j - 1]\n            j -= 1\n    return items\n\n", at="сдвигаем его влево"),
  t("print(insertion_sort([5, 2, 9, 1, 7]))\nprint(insertion_sort([1, 2, 3, 4, 5]))\n", at="Для почти"), run("Для почти")),
 S("sorted", "Встроенная сортировка", """
  В реальных программах свои сортировки не пишут. Встроенная функция sorted возвращает новый отсортированный список, а метод
  sort сортирует список на месте. Они работают очень быстро: используется алгоритм Timsort со сложностью О от эн лог эн.
  Параметр key задаёт, по чему сортировать, а reverse равно True разворачивает порядок. Отсортируем задачи по приоритету, а при
  равенстве — по названию.""",
  clr(), t('tasks = [("отчёт", 2), ("почта", 1), ("звонок", 2), ("зарядка", 1)]\n', at="Встроенная функция"),
  t("print(sorted(tasks, key=lambda t: (t[1], t[0])))\n", at="Параметр key"),
  t("print(sorted(tasks, key=lambda t: t[1], reverse=True))\n", at="reverse"), run("Отсортируем")),
 S("stable", "Устойчивость сортировки", """
  Сортировка называется устойчивой, если равные элементы сохраняют исходный порядок. Встроенная сортировка Python устойчива.
  Посмотрите: мы сортируем только по приоритету, и «отчёт» остаётся перед «звонком», как и в исходном списке. Это
  позволяет сортировать по нескольким критериям последовательно: сначала по второстепенному, потом по главному.""",
  clr(), t('tasks = [("отчёт", 2), ("почта", 1), ("звонок", 2), ("зарядка", 1)]\nprint(sorted(tasks, key=lambda t: t[1]))\n', at="Посмотрите"), run("Это")),
 S("summary", "Итог", """
  Подведём итог. Пузырёк, выбор и вставки — простые алгоритмы со сложностью О от эн в квадрате: на тысяче элементов это
  около миллиона операций. Для учёбы они полезны, а для работы нужна встроенная функция sorted с параметром key. Помните
  про устойчивость: равные элементы сохраняют порядок. Дальше узнаем, как сортировать быстро с помощью рекурсии.""",
  nt("`sorted(items, key=..., reverse=...)` · Timsort · O(n log n) · устойчивая", at="Подведём итог")),
]

notes = """
# Сортировки

## Пузырёк

```python
def bubble_sort(items):
    items = list(items)
    swapped = True
    while swapped:
        swapped = False
        for i in range(len(items) - 1):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = items[i + 1], items[i]
                swapped = True
    return items

print(bubble_sort([5, 2, 9, 1, 7]))
```

## Выбор и вставки

```python
def selection_sort(items):
    items = list(items)
    for i in range(len(items)):
        smallest = i
        for j in range(i + 1, len(items)):
            if items[j] < items[smallest]:
                smallest = j
        items[i], items[smallest] = items[smallest], items[i]
    return items

def insertion_sort(items):
    items = list(items)
    for i in range(1, len(items)):
        j = i
        while j > 0 and items[j - 1] > items[j]:
            items[j - 1], items[j] = items[j], items[j - 1]
            j -= 1
    return items
```

## Встроенная сортировка

```python
tasks = [("отчёт", 2), ("почта", 1), ("звонок", 2), ("зарядка", 1)]
print(sorted(tasks, key=lambda t: (t[1], t[0])))
print(sorted(tasks, key=lambda t: t[1], reverse=True))
```

| Алгоритм | Худший случай | Устойчивый |
|---|---|---|
| Пузырёк | O(n²) | да |
| Выбор | O(n²) | нет |
| Вставки | O(n²) | да |
| `sorted` (Timsort) | O(n log n) | да |
"""

a1 = fn_task("a1-bubble", "Пузырьком", "Напишите функцию `bubble_sort(items)` без использования `sorted` и `sort`: верните **новый** отсортированный по возрастанию список; исходный список менять нельзя.",
  "bubble_sort", "def bubble_sort(items):\n    items = list(items)\n    swapped = True\n    while swapped:\n        swapped = False\n        for i in range(len(items) - 1):\n            if items[i] > items[i + 1]:\n                items[i], items[i + 1] = items[i + 1], items[i]\n                swapped = True\n    return items\n",
  [[[5, 2, 9, 1, 7]], [[]], ([[1]], True), ([[3, 3, 1, 2, 2]], True), ([[9, 8, 7, 6, 5, 4, 3, 2, 1]], True), ([[-1, 5, 0, -7]], True)],
  [("def bubble_sort(items):\n    items = list(items)\n    for i in range(len(items) - 1):\n        if items[i] > items[i + 1]:\n            items[i], items[i + 1] = items[i + 1], items[i]\n    return items\n", "Сделан лишь один проход: список упорядочен не полностью."),
   ("def bubble_sort(items):\n    items = list(items)\n    swapped = True\n    while swapped:\n        swapped = False\n        for i in range(len(items) - 1):\n            if items[i] >= items[i + 1]:\n                items[i], items[i + 1] = items[i + 1], items[i]\n                swapped = True\n    return items\n", "Условие «>=» меняет равные элементы бесконечно (цикл не завершается).")],
  hints("Сравнивайте соседние элементы и меняйте их, если левый больше правого.", "Один проход поднимает самый большой элемент в конец.", "Повторяйте проходы, пока есть хотя бы одна перестановка (флаг swapped).", "Сначала скопируйте список: items = list(items).", "Обмен: items[i], items[i + 1] = items[i + 1], items[i]."),
  "Проходы повторяются, пока список не станет упорядоченным; копия защищает исходные данные.")

a2 = fn_task("a2-swaps", "Сколько перестановок", "Напишите функцию `count_swaps(items)`: выполните сортировку пузырьком и верните **число перестановок** соседних элементов (при равенстве перестановки нет).\n\nПример: `count_swaps([3, 1, 2])` → `2`; `count_swaps([1, 2, 3])` → `0`.",
  "count_swaps", "def count_swaps(items):\n    items = list(items)\n    swaps = 0\n    swapped = True\n    while swapped:\n        swapped = False\n        for i in range(len(items) - 1):\n            if items[i] > items[i + 1]:\n                items[i], items[i + 1] = items[i + 1], items[i]\n                swaps += 1\n                swapped = True\n    return swaps\n",
  [[[3, 1, 2]], [[1, 2, 3]], ([[]], True), ([[5, 4, 3, 2, 1]], True), ([[2, 2, 1]], True), ([[4, 1, 3, 2]], True)],
  [("def count_swaps(items):\n    items = list(items)\n    comparisons = 0\n    swapped = True\n    while swapped:\n        swapped = False\n        for i in range(len(items) - 1):\n            comparisons += 1\n            if items[i] > items[i + 1]:\n                items[i], items[i + 1] = items[i + 1], items[i]\n                swapped = True\n    return comparisons\n", "Считаются сравнения, а не перестановки."),
   ("def count_swaps(items):\n    items = list(items)\n    swaps = 0\n    swapped = True\n    while swapped:\n        swapped = False\n        for i in range(len(items) - 1):\n            if items[i] >= items[i + 1]:\n                items[i], items[i + 1] = items[i + 1], items[i]\n                swaps += 1\n                if items[i] != items[i + 1]:\n                    swapped = True\n    return swaps\n", "Равные элементы тоже считаются перестановкой.")],
  hints("Нужно выполнить саму сортировку и считать обмены.", "Заведите счётчик swaps = 0.", "Увеличивайте его только при реальном обмене.", "При равенстве элементов обмена нет.", "Верните swaps после завершения сортировки."),
  "Число перестановок в пузырьке равно числу инверсий — пар элементов, стоящих в неправильном порядке.")

a3 = fn_task("a3-insertion", "Вставками", "Напишите `insertion_sort(items)`: сортировка вставками без `sorted`/`sort`, возвращает новый список по **убыванию**.",
  "insertion_sort", "def insertion_sort(items):\n    items = list(items)\n    for i in range(1, len(items)):\n        j = i\n        while j > 0 and items[j - 1] < items[j]:\n            items[j - 1], items[j] = items[j], items[j - 1]\n            j -= 1\n    return items\n",
  [[[5, 2, 9, 1, 7]], [[]], ([[1, 2, 3]], True), ([[3, 3, 1]], True), ([[10]], True), ([[1, 5, 2, 5, 0]], True)],
  [("def insertion_sort(items):\n    items = list(items)\n    for i in range(1, len(items)):\n        j = i\n        while j > 0 and items[j - 1] > items[j]:\n            items[j - 1], items[j] = items[j], items[j - 1]\n            j -= 1\n    return items\n", "Сортирует по возрастанию, а нужно по убыванию."),
   ("def insertion_sort(items):\n    items = list(items)\n    for i in range(1, len(items)):\n        j = i\n        if j > 0 and items[j - 1] < items[j]:\n            items[j - 1], items[j] = items[j], items[j - 1]\n    return items\n", "Элемент сдвигается не до конца (if вместо while).")],
  hints("Левая часть списка всегда уже отсортирована.", "Берите элементы по очереди, начиная со второго.", "Сдвигайте элемент влево, пока он больше левого соседа (для убывания).", "Нужен именно while: сдвигов может быть несколько.", "Условие: while j > 0 and items[j - 1] < items[j]."),
  "Для убывания элемент сдвигается влево, пока левый сосед меньше него; строгое сравнение сохраняет устойчивость.")

a4 = fn_task("a4-key", "Сортировка по ключу", "Напишите функцию `rank(students)`: `students` — список пар `[имя, оценка]`. Верните список имён: сначала по **убыванию оценки**, при равных оценках — по **алфавиту**.\n\nПример: `rank([[\"Борис\", 4], [\"Аня\", 5], [\"Вера\", 4]])` → `[\"Аня\", \"Борис\", \"Вера\"]`.",
  "rank", "def rank(students):\n    ordered = sorted(students, key=lambda s: (-s[1], s[0]))\n    return [name for name, _ in ordered]\n",
  [[[["Борис", 4], ["Аня", 5], ["Вера", 4]]], [[]], ([[["Яна", 3], ["Аня", 3]]], True), ([[["Глеб", 2], ["Дина", 5], ["Ева", 5], ["Антон", 2]]], True), ([[["Ольга", 1]]], True)],
  [("def rank(students):\n    ordered = sorted(students, key=lambda s: (s[1], s[0]))\n    return [name for name, _ in ordered]\n", "Сортировка по возрастанию оценки."),
   ("def rank(students):\n    ordered = sorted(students, key=lambda s: s[1], reverse=True)\n    return [name for name, _ in ordered]\n", "При равных оценках порядок исходный, а нужен алфавитный."),
   ("def rank(students):\n    ordered = sorted(students, key=lambda s: (-s[1], s[0]), reverse=True)\n    return [name for name, _ in ordered]\n", "reverse=True разворачивает и алфавитный порядок.")],
  hints("Ключ сортировки может быть кортежем: сравнение идёт по первому элементу, потом по второму.", "Для убывания числа используйте отрицательное значение.", "key=lambda s: (-s[1], s[0]).", "Результат sorted — список пар, а нужны только имена.", "Верните [name for name, _ in ordered]."),
  "Кортеж в key сортирует по нескольким критериям; минус превращает убывание в возрастание.")

a5 = predict_task("a5-stable", "Устойчивая сортировка", 'tasks = [("отчёт", 2), ("почта", 1), ("звонок", 2), ("зарядка", 1)]\nresult = sorted(tasks, key=lambda t: t[1])\nprint([name for name, _ in result])\nprint(sorted([3, 1, 2], reverse=True))\n',
  [("['звонок', 'отчёт', 'зарядка', 'почта']\n[3, 2, 1]\n", "Сортировка Python устойчива: равные приоритеты сохраняют исходный порядок."),
   ("['почта', 'зарядка', 'отчёт', 'звонок']\n[1, 2, 3]\n", "Второй вывод — по убыванию: reverse=True.")],
  hints("Сортировка идёт только по приоритету (второй элемент пары).", "Приоритет 1 — «почта» и «зарядка», приоритет 2 — «отчёт» и «звонок».", "Устойчивая сортировка не меняет порядок равных: «почта» перед «зарядкой».", "Итог первой строки: почта, зарядка, отчёт, звонок.", "Вторая строка — по убыванию: [3, 2, 1]."),
  "Python сортирует устойчиво, поэтому равные по ключу элементы остаются в исходном порядке.")

mistakes = [
 {"mistake": "Пишут собственную сортировку вместо sorted", "fix": "Используйте sorted/sort: они быстрее и проверены временем."},
 {"mistake": "Ожидают, что sort() возвращает список", "fix": "sort() меняет список на месте и возвращает None; нужен новый список — sorted()."},
 {"mistake": "Сортируют по убыванию через reverse там, где нужен смешанный порядок", "fix": "Используйте кортеж в key: (-число, имя)."},
 {"mistake": "Забывают, что сортировка пузырьком меняет исходный список", "fix": "Сделайте копию: items = list(items)."}]

finish("alg-03-sorting", "Сортировки", "Реализовать простые сортировки, понимать сложность O(n²) и пользоваться sorted с key.",
  {"algo.sort.simple": "Простые сортировки", "algo.sort.builtin": "sorted, key и устойчивость"},
  ["alg-02-search"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="algorithms")

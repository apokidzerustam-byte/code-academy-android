from lib import *

MERGE = "def merge(left, right):\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    result.extend(left[i:])\n    result.extend(right[j:])\n    return result\n"

begin()
scenes = [
 S("intro", "Разделяй и властвуй", """
  Простые сортировки сравнивают почти все пары элементов и поэтому медленны. Быстрые алгоритмы используют идею «разделяй и
  властвуй»: разбить задачу на части, решить каждую рекурсивно и объединить результаты. Сегодня разберём два алгоритма. Первый —
  сортировка слиянием, второй — быстрая сортировка. Оба работают за О от эн лог эн, что для миллиона элементов означает
  около двадцати миллионов операций вместо тысячи миллиардов у пузырька.""",
  nt("**Разделяй и властвуй**: разбей → реши части рекурсивно → объедини", at="Быстрые алгоритмы")),
 S("merge", "Слияние двух отсортированных списков", """
  Основа сортировки слиянием — умение объединять два уже отсортированных списка в один отсортированный. Заведём по
  указателю на каждый список. Сравниваем элементы, на которые они указывают, берём меньший и двигаем соответствующий
  указатель. Когда один из списков закончился, остаток другого просто дописываем в конец, потому что он уже отсортирован.""",
  clr(), t("def merge(left, right):\n    result = []\n    i = j = 0\n", at="Заведём"),
  t("    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n", at="Сравниваем"),
  t("    result.extend(left[i:])\n    result.extend(right[j:])\n    return result\n\nprint(merge([1, 4, 9], [2, 3, 10, 11]))\n", at="Когда один"), run("Когда один")),
 S("mergesort", "Сортировка слиянием", """
  Теперь сама сортировка. Если в списке не больше одного элемента, он уже отсортирован — это базовый случай. Иначе
  делим список пополам, рекурсивно сортируем обе половины и сливаем результаты нашей функцией merge. Глубина рекурсии равна
  логарифму от числа элементов, а на каждом уровне слияние обрабатывает все элементы, откуда и берётся О от эн лог эн.""",
  clr(), t(MERGE + "\n", at="Теперь сама"),
  t("def merge_sort(items):\n    if len(items) <= 1:\n        return list(items)\n", at="Если в списке"),
  t("    mid = len(items) // 2\n    return merge(merge_sort(items[:mid]), merge_sort(items[mid:]))\n\n", at="делим список"),
  t("print(merge_sort([5, 2, 9, 1, 7, 3, 8]))\n", at="Глубина"), run("Глубина")),
 S("quick", "Быстрая сортировка", """
  Быстрая сортировка устроена иначе. Выбираем опорный элемент, например первый. Все элементы меньше опорного отправляем в
  левую группу, равные — в среднюю, большие — в правую. Затем рекурсивно сортируем левую и правую группы, а средняя уже на
  своём месте. Склеиваем три части. В среднем она очень быстрая, а в худшем случае, например при уже отсортированных данных
  и плохом выборе опорного, замедляется до О от эн в квадрате.""",
  clr(), t("def quick_sort(items):\n    if len(items) <= 1:\n        return list(items)\n    pivot = items[0]\n", at="Выбираем опорный"),
  t("    less = [x for x in items if x < pivot]\n    equal = [x for x in items if x == pivot]\n    more = [x for x in items if x > pivot]\n", at="Все элементы меньше"),
  t("    return quick_sort(less) + equal + quick_sort(more)\n\nprint(quick_sort([5, 2, 9, 1, 5, 7, 3]))\n", at="Склеиваем"), run("Склеиваем")),
 S("count", "Считаем операции", """
  Сравним быстрые и простые алгоритмы по числу сравнений. Напишем сортировку слиянием со счётчиком сравнений и пузырёк
  с таким же счётчиком, и запустим оба на списке из двухсот элементов, расположенных в обратном порядке. Пузырёк
  выполнит около двадцати тысяч сравнений, слияние — менее двух тысяч. Чем больше данных, тем выше разрыв.""",
  clr(), t("def bubble_cmp(items):\n    items, n = list(items), 0\n    swapped = True\n    while swapped:\n        swapped = False\n        for i in range(len(items) - 1):\n            n += 1\n            if items[i] > items[i + 1]:\n                items[i], items[i + 1] = items[i + 1], items[i]\n                swapped = True\n    return n\n\n", at="Напишем сортировку"),
  t("def merge_cmp(items):\n    if len(items) <= 1:\n        return list(items), 0\n    mid = len(items) // 2\n    left, a = merge_cmp(items[:mid])\n    right, b = merge_cmp(items[mid:])\n    res, i, j, n = [], 0, 0, 0\n    while i < len(left) and j < len(right):\n        n += 1\n        if left[i] <= right[j]:\n            res.append(left[i]); i += 1\n        else:\n            res.append(right[j]); j += 1\n    res += left[i:] + right[j:]\n    return res, a + b + n\n\n", at="Напишем сортировку"),
  t("data = list(range(200, 0, -1))\nprint(bubble_cmp(data), merge_cmp(data)[1])\n", at="запустим оба"), run("Чем больше")),
 S("summary", "Итог", """
  Подведём итог. Сортировка слиянием гарантированно работает за О от эн лог эн и устойчива, но требует дополнительной
  памяти. Быстрая сортировка в среднем быстра, но в плохих случаях деградирует. На практике используйте встроенный
  sorted, а идею разделяй и властвуй запомните: она встретится нам ещё в деревьях и бинарном поиске.""",
  nt("Слияние: O(n log n), устойчивая · Быстрая: в среднем O(n log n), худший O(n²)", at="Подведём итог")),
]

notes = """
# Быстрые сортировки

## Слияние

```python
def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def merge_sort(items):
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    return merge(merge_sort(items[:mid]), merge_sort(items[mid:]))
```

## Быстрая сортировка

```python
def quick_sort(items):
    if len(items) <= 1:
        return list(items)
    pivot = items[0]
    less = [x for x in items if x < pivot]
    equal = [x for x in items if x == pivot]
    more = [x for x in items if x > pivot]
    return quick_sort(less) + equal + quick_sort(more)
```

| | Слияние | Быстрая |
|---|---|---|
| Среднее | O(n log n) | O(n log n) |
| Худшее | O(n log n) | O(n²) |
| Память | O(n) | O(log n)…O(n) |
"""

a1 = fn_task("a1-merge", "Слияние списков", "Напишите функцию `merge(left, right)`: объедините два **отсортированных** списка в один отсортированный без `sorted` и `sort`.\n\nПример: `merge([1, 4, 9], [2, 3, 10, 11])` → `[1, 2, 3, 4, 9, 10, 11]`.",
  "merge", MERGE,
  [[[1, 4, 9], [2, 3, 10, 11]], [[], []], ([[], [1, 2]], True), ([[5], []], True), ([[1, 1, 2], [1, 3]], True), ([[1, 2, 3], [4, 5, 6]], True)],
  [("def merge(left, right):\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    return result\n", "Остаток непустого списка потерян."),
   ("def merge(left, right):\n    return left + right\n", "Списки просто склеены без сравнения."),
   ("def merge(left, right):\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] < right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    result.extend(left[i:])\n    return result\n", "Остаток правого списка потерян.")],
  hints("Заведите два указателя — по одному на каждый список.", "Сравнивайте текущие элементы и берите меньший.", "Двигайте указатель того списка, из которого взяли элемент.", "Когда один список закончится, второй нужно дописать целиком.", "result.extend(left[i:]); result.extend(right[j:])."),
  "Слияние за один проход: каждый элемент добавляется ровно один раз — сложность O(n+m).")

a2 = fn_task("a2-mergesort", "Сортировка слиянием", "Напишите `merge_sort(items)` — рекурсивную сортировку слиянием без `sorted`/`sort`. Возвращает новый список по возрастанию.",
  "merge_sort", MERGE + "\n\ndef merge_sort(items):\n    if len(items) <= 1:\n        return list(items)\n    mid = len(items) // 2\n    return merge(merge_sort(items[:mid]), merge_sort(items[mid:]))\n",
  [[[5, 2, 9, 1, 7, 3, 8]], [[]], ([[1]], True), ([[2, 1]], True), ([[3, 3, 3]], True), ([[9, 8, 7, 6, 5, 4, 3, 2, 1, 0]], True), ([[-5, 3, 0, -5, 2]], True)],
  [("def merge_sort(items):\n    if len(items) <= 1:\n        return list(items)\n    mid = len(items) // 2\n    return merge_sort(items[:mid]) + merge_sort(items[mid:])\n", "Половины склеены, а не слиты по порядку."),
   ("def merge_sort(items):\n    return list(items)\n", "Сортировка не выполняется."),
   (MERGE + "\n\ndef merge_sort(items):\n    if len(items) <= 1:\n        return list(items)\n    mid = len(items) // 2\n    return merge(items[:mid], items[mid:])\n", "Половины не отсортированы рекурсивно перед слиянием.")],
  hints("Список из одного элемента уже отсортирован.", "Разделите список пополам: items[:mid] и items[mid:].", "Каждую половину отсортируйте рекурсивно.", "Объедините результаты функцией слияния двух отсортированных списков.", "return merge(merge_sort(left), merge_sort(right))."),
  "Базовый случай — список длиной до 1; слияние сортированных половин даёт сортированный результат.")

a3 = fn_task("a3-quick", "Быстрая сортировка", "Напишите `quick_sort(items)`: быстрая сортировка с опорным элементом `items[0]`; без `sorted`/`sort`. **Дубликаты нельзя терять.**",
  "quick_sort", "def quick_sort(items):\n    if len(items) <= 1:\n        return list(items)\n    pivot = items[0]\n    less = [x for x in items if x < pivot]\n    equal = [x for x in items if x == pivot]\n    more = [x for x in items if x > pivot]\n    return quick_sort(less) + equal + quick_sort(more)\n",
  [[[5, 2, 9, 1, 5, 7, 3]], [[]], ([[4, 4, 4]], True), ([[2, 1, 2, 1]], True), ([[1, 2, 3, 4]], True), ([[4, 3, 2, 1]], True)],
  [("def quick_sort(items):\n    if len(items) <= 1:\n        return list(items)\n    pivot = items[0]\n    less = [x for x in items if x < pivot]\n    more = [x for x in items if x > pivot]\n    return quick_sort(less) + [pivot] + quick_sort(more)\n", "Дубликаты опорного элемента теряются."),
   ("def quick_sort(items):\n    if len(items) <= 1:\n        return list(items)\n    pivot = items[0]\n    less = [x for x in items if x <= pivot]\n    more = [x for x in items if x > pivot]\n    return quick_sort(less) + quick_sort(more)\n", "Опорный элемент входит в левую группу: рекурсия не уменьшает задачу (бесконечная рекурсия)."),
   ("def quick_sort(items):\n    if len(items) <= 1:\n        return list(items)\n    pivot = items[0]\n    less = [x for x in items if x < pivot]\n    equal = [x for x in items if x == pivot]\n    more = [x for x in items if x > pivot]\n    return quick_sort(more) + equal + quick_sort(less)\n", "Группы склеены в обратном порядке.")],
  hints("Выберите опорный элемент и разделите остальные на три группы.", "Меньше опорного, равные опорному и больше опорного.", "Две крайние группы отсортируйте рекурсивно.", "Средняя группа (равные) уже на месте.", "return quick_sort(less) + equal + quick_sort(more)."),
  "Три группы гарантируют, что дубликаты не потеряются, а рекурсивные части строго меньше исходного списка.")

a4 = fn_task("a4-inversions", "Беспорядок в списке", "Инверсия — пара позиций `i < j`, где `items[i] > items[j]`. Напишите `count_inversions(items)`, возвращающую число инверсий (можно любым способом).\n\nПример: `count_inversions([3, 1, 2])` → `2` (пары 3>1 и 3>2).",
  "count_inversions", "def count_inversions(items):\n    count = 0\n    for i in range(len(items)):\n        for j in range(i + 1, len(items)):\n            if items[i] > items[j]:\n                count += 1\n    return count\n",
  [[[3, 1, 2]], [[1, 2, 3]], ([[]], True), ([[3, 2, 1]], True), ([[2, 2, 1]], True), ([[1, 3, 2, 4, 0]], True)],
  [("def count_inversions(items):\n    return sum(1 for i in range(len(items) - 1) if items[i] > items[i + 1])\n", "Считаются только соседние пары."),
   ("def count_inversions(items):\n    count = 0\n    for i in range(len(items)):\n        for j in range(i + 1, len(items)):\n            if items[i] >= items[j]:\n                count += 1\n    return count\n", "Равные элементы тоже считаются инверсией.")],
  hints("Нужно посчитать пары, которые стоят «не в том порядке».", "Пара определяется двумя индексами i < j.", "Переберите все такие пары двумя вложенными циклами.", "Инверсия — строгое «больше»: items[i] > items[j].", "Увеличивайте счётчик для каждой такой пары."),
  "Перебор всех пар работает за O(n²); сортировка слиянием позволяет считать инверсии за O(n log n).")

a5 = predict_task("a5-merge", "Что вернёт слияние", "def merge(left, right):\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    result.extend(left[i:])\n    result.extend(right[j:])\n    return result\n\nprint(merge([1, 5, 5], [2, 5, 8]))\nprint(merge([], [3]))\n",
  [("[1, 2, 5, 5, 8]\n[3]\n", "Равный пятёрке элемент правого списка тоже попадает в результат: пятёрок три."),
   ("[1, 5, 5, 2, 5, 8]\n[3]\n", "Слияние сравнивает элементы: двойка встанет перед пятёрками.")],
  hints("Сравниваются текущие элементы двух списков.", "1 < 2: берём 1. Затем 5 против 2: берём 2.", "5 и 5: при равенстве берём из левого (<=), потом снова 5 против 5.", "Когда левый список закончится, остаток правого — [8] — дописывается.", "Итог: [1, 2, 5, 5, 5, 8]."),
  "Слияние берёт меньший элемент (при равенстве — из левого списка); остаток дописывается в конец.")

mistakes = [
 {"mistake": "Теряют дубликаты в быстрой сортировке", "fix": "Отдельная группа equal для элементов, равных опорному."},
 {"mistake": "Забывают дописать остаток при слиянии", "fix": "После цикла extend для обоих списков."},
 {"mistake": "Опорный элемент попадает в обе рекурсивные группы", "fix": "Каждая часть должна быть строго меньше исходного списка."},
 {"mistake": "Используют быструю сортировку на отсортированных данных с первым опорным", "fix": "Берите опорный из середины или случайный."}]

finish("alg-05-fast-sorts", "Быстрые сортировки", "Реализовать сортировку слиянием и быструю сортировку, понимать идею «разделяй и властвуй».",
  {"algo.sort.merge": "Сортировка слиянием", "algo.sort.quick": "Быстрая сортировка"},
  ["alg-04-recursion", "alg-03-sorting"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="algorithms")

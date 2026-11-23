from lib import *

NODE = "class Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None\n\n\ndef insert(node, value):\n    if node is None:\n        return Node(value)\n    if value < node.value:\n        node.left = insert(node.left, value)\n    elif value > node.value:\n        node.right = insert(node.right, value)\n    return node\n\n\ndef build(values):\n    root = None\n    for v in values:\n        root = insert(root, v)\n    return root\n"

begin()
scenes = [
 S("intro", "Иерархия данных", """
  Не все данные выстраиваются в линию. Папки содержат папки, у компании есть отделы, а в отделах отделы поменьше, у
  документа есть главы, а у глав — разделы. Такая иерархия называется деревом. Сегодня мы поработаем с самым популярным
  видом: бинарным деревом, где у каждого узла не более двух потомков, левого и правого. Рекурсия, которую мы недавно
  изучили, здесь окажется естественным инструментом.""",
  nt("**Дерево**: корень → узлы → листья. Бинарное: не более двух детей", at="Такая иерархия")),
 S("node", "Узел дерева", """
  Дерево состоит из узлов. Каждый узел хранит значение и две ссылки: на левого и правого потомка. Если потомка нет, ссылка
  равна None. Узел, у которого нет потомков, называется листом. Самый верхний узел — корень. Создадим маленькое дерево
  вручную: корень со значением пять и двумя потомками.""",
  clr(), t("class Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None\n\n", at="Каждый узел"),
  t("root = Node(5)\nroot.left = Node(3)\nroot.right = Node(8)\nprint(root.value, root.left.value, root.right.value)\nprint(root.left.left)\n", at="Создадим"), run("Создадим")),
 S("bst", "Двоичное дерево поиска", """
  Особый вид дерева — двоичное дерево поиска. Его правило простое: всё, что в левом поддереве, меньше значения узла, а
  всё в правом — больше. Чтобы вставить значение, начинаем с корня: если оно меньше, идём влево, если больше — вправо,
  пока не найдём пустое место. Рекурсивная вставка записывается очень компактно. Повторные значения мы игнорируем.""",
  clr(), t("class Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None\n\n", at="Особый вид"),
  t("def insert(node, value):\n    if node is None:\n        return Node(value)\n", at="Рекурсивная вставка"),
  t("    if value < node.value:\n        node.left = insert(node.left, value)\n    elif value > node.value:\n        node.right = insert(node.right, value)\n    return node\n\n", at="Рекурсивная вставка"),
  t("root = None\nfor v in [5, 3, 8, 1, 4, 9]:\n    root = insert(root, v)\nprint(root.left.value, root.right.value, root.left.right.value)\n", at="Повторные"), run("Повторные")),
 S("inorder", "Обход дерева", """
  Чтобы пройти по всем узлам, нужен обход. Симметричный обход делает три шага: обходит левое поддерево, затем берёт значение
  узла, затем обходит правое. Для дерева поиска получается замечательный результат: значения идут в отсортированном порядке.
  Именно поэтому деревья поиска ещё называют самосортирующимися.""",
  t("def inorder(node):\n    if node is None:\n        return []\n", at="Симметричный"),
  t("    return inorder(node.left) + [node.value] + inorder(node.right)\n\n", at="затем обходит правое"),
  t("print(inorder(root))\n", at="Для дерева поиска"), run("Именно поэтому")),
 S("height", "Высота и поиск", """
  Высота дерева — это длина самого длинного пути от корня до листа, мы будем считать её в узлах. Пустое дерево имеет высоту
  ноль, а иначе высота равна единице плюс большая из высот левого и правого поддеревьев. Поиск в дереве устроен как бинарный
  поиск: на каждом шаге отбрасываем одно из поддеревьев. В сбалансированном дереве это даёт О от лог эн.""",
  t("def height(node):\n    if node is None:\n        return 0\n", at="Пустое дерево"),
  t("    return 1 + max(height(node.left), height(node.right))\n\n", at="а иначе"),
  t("def contains(node, target):\n    while node is not None:\n        if target == node.value:\n            return True\n        node = node.left if target < node.value else node.right\n    return False\n\n", at="Поиск в дереве"),
  t("print(height(root), contains(root, 4), contains(root, 7))\n", at="В сбалансированном"), run("В сбалансированном")),
 S("levels", "Обход по уровням", """
  Иногда нужен обход по уровням: сначала корень, потом его дети, потом внуки. Для этого используют очередь. Кладём корень в
  очередь, затем повторяем: берём узел из начала, обрабатываем и кладём его потомков в конец. Дети всегда окажутся позади
  родителей, поэтому уровни идут по порядку.""",
  t("from collections import deque\n\ndef level_order(root):\n    result, queue = [], deque([root] if root else [])\n", at="Для этого используют"),
  t("    while queue:\n        node = queue.popleft()\n        result.append(node.value)\n", at="берём узел"),
  t("        if node.left:\n            queue.append(node.left)\n        if node.right:\n            queue.append(node.right)\n    return result\n\n", at="кладём его потомков"),
  t("print(level_order(root))\n", at="Дети всегда"), run("Дети всегда")),
 S("summary", "Итог", """
  Подведём итог. Дерево — иерархическая структура из узлов. В двоичном дереве поиска слева меньшие значения, справа большие.
  Симметричный обход выдаёт значения по возрастанию, высота считается рекурсивно, а обход по уровням требует очереди. Если дерево
  вырождается в цепочку, поиск замедляется до линейного, поэтому на практике применяют сбалансированные деревья. Следующая
  тема — графы, обобщение деревьев.""",
  nt("Обходы: **in-order** (лево-узел-право) · **по уровням** (очередь). Высота: `1 + max(левая, правая)`", at="Подведём итог")),
]

notes = """
# Деревья

```python
class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

def insert(node, value):
    if node is None:
        return Node(value)
    if value < node.value:
        node.left = insert(node.left, value)
    elif value > node.value:
        node.right = insert(node.right, value)
    return node

def inorder(node):
    if node is None:
        return []
    return inorder(node.left) + [node.value] + inorder(node.right)

def height(node):
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))
```

## Обход по уровням

```python
from collections import deque

def level_order(root):
    result, queue = [], deque([root] if root else [])
    while queue:
        node = queue.popleft()
        result.append(node.value)
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    return result
```

## Запомните

1. BST: слева меньше, справа больше.
2. In-order обход BST — по возрастанию.
3. Вырожденное дерево (цепочка) работает как список — O(n).
"""

INORDER = "def inorder(node):\n    if node is None:\n        return []\n    return inorder(node.left) + [node.value] + inorder(node.right)\n"
a1 = fn_task("a1-sorted-unique", "Дерево как сортировщик", "Заготовлены `Node`, `insert` и `build(values)` (построение дерева поиска). Напишите `sorted_unique(values)`: постройте дерево и верните значения симметричным обходом (по возрастанию, без повторов).",
  "sorted_unique", NODE + "\n\n" + INORDER + "\n\ndef sorted_unique(values):\n    return inorder(build(values))\n",
  [[[5, 3, 8, 1, 4, 9]], [[]], ([[2, 2, 2]], True), ([[5, 4, 3, 2, 1]], True), ([[3, 1, 2, 3, 1]], True), ([[-1, 7, 0]], True)],
  [(NODE + "\n\ndef preorder(node):\n    if node is None:\n        return []\n    return [node.value] + preorder(node.left) + preorder(node.right)\n\n\ndef sorted_unique(values):\n    return preorder(build(values))\n", "Прямой обход (узел-лево-право) не даёт отсортированного порядка."),
   (NODE + "\n\ndef inorder(node):\n    if node is None:\n        return []\n    return inorder(node.right) + [node.value] + inorder(node.left)\n\n\ndef sorted_unique(values):\n    return inorder(build(values))\n", "Правое поддерево обходится раньше левого: порядок по убыванию."),
   ("def sorted_unique(values):\n    return sorted(values)\n", "Повторы не удалены.")],
  hints("Дерево поиска хранит меньшие значения слева, большие справа.", "Обход «левое поддерево → узел → правое поддерево» называется симметричным.", "Для пустого узла верните пустой список.", "Результат: inorder(left) + [value] + inorder(right).", "Не забудьте построить дерево: build(values)."),
  "In-order обход дерева поиска выдаёт значения по возрастанию, а вставка игнорирует повторы.",
  starter=NODE + "\n\ndef sorted_unique(values):\n    # постройте дерево и обойдите его симметрично\n    pass\n", type="complete")

a2 = fn_task("a2-height", "Высота дерева", "Используя `Node`, `insert`, `build`, напишите `tree_height(values)`: высота дерева, построенного вставкой значений по порядку (в узлах; пустое дерево — 0, один узел — 1).",
  "tree_height", NODE + "\n\ndef height(node):\n    if node is None:\n        return 0\n    return 1 + max(height(node.left), height(node.right))\n\n\ndef tree_height(values):\n    return height(build(values))\n",
  [[[5, 3, 8, 1, 4, 9]], [[]], ([[1]], True), ([[1, 2, 3, 4, 5]], True), ([[3, 2, 1]], True), ([[4, 2, 6, 1, 3, 5, 7]], True)],
  [(NODE + "\n\ndef height(node):\n    if node is None:\n        return 0\n    return 1 + height(node.left)\n\n\ndef tree_height(values):\n    return height(build(values))\n", "Учитывается только левая ветвь."),
   (NODE + "\n\ndef height(node):\n    if node is None:\n        return 0\n    return height(node.left) + height(node.right)\n\n\ndef tree_height(values):\n    return height(build(values))\n", "Высоты сложены, а не выбран максимум (и базовый случай теряет единицу)."),
   (NODE + "\n\ndef height(node):\n    if node is None:\n        return -1\n    return 1 + max(height(node.left), height(node.right))\n\n\ndef tree_height(values):\n    return height(build(values))\n", "Высота считается в рёбрах, а нужно в узлах.")],
  hints("Высота пустого дерева — 0.", "Высота узла на единицу больше высоты более высокого поддерева.", "Используйте max(height(left), height(right)).", "Не забудьте прибавить единицу за сам узел.", "return 1 + max(height(node.left), height(node.right))."),
  "Рекурсия по поддеревьям: высота — единица плюс максимум из высот потомков.")

a3 = fn_task("a3-path", "Путь поиска", "Используя `Node`, `insert`, `build`, напишите `search_path(values, target)`: постройте дерево и верните список значений узлов, через которые проходит поиск `target` от корня (включая последний проверенный узел). Если `target` нет — путь всё равно возвращается до места, где поиск остановился.\n\nПример: для `[5, 3, 8, 1, 4, 9]` и `4` → `[5, 3, 4]`.",
  "search_path", NODE + "\n\ndef search_path(values, target):\n    node = build(values)\n    path = []\n    while node is not None:\n        path.append(node.value)\n        if target == node.value:\n            break\n        node = node.left if target < node.value else node.right\n    return path\n",
  [[[5, 3, 8, 1, 4, 9], 4], [[5, 3, 8], 7], ([[], 1], True), ([[5, 3, 8, 1, 4, 9], 5], True), ([[1, 2, 3, 4], 4], True), ([[5, 3, 8, 1, 4, 9], 0], True)],
  [(NODE + "\n\ndef search_path(values, target):\n    node = build(values)\n    path = []\n    while node is not None:\n        if target == node.value:\n            break\n        path.append(node.value)\n        node = node.left if target < node.value else node.right\n    return path\n", "Найденный узел не включён в путь."),
   (NODE + "\n\ndef search_path(values, target):\n    node = build(values)\n    path = []\n    while node is not None:\n        path.append(node.value)\n        if target == node.value:\n            break\n        node = node.right if target < node.value else node.left\n    return path\n", "Направление выбрано наоборот."),
   ("def search_path(values, target):\n    return [v for v in values if v <= target]\n", "Путь не строится по дереву.")],
  hints("Начинайте с корня и спускайтесь вниз.", "На каждом узле запишите его значение в путь.", "Если искомое равно значению узла — остановитесь.", "Меньше — идите влево, больше — вправо.", "Цикл while node is not None завершится, когда дойдёте до пустого места."),
  "Поиск в дереве проходит один путь от корня; длина пути не больше высоты дерева.")

a4 = fn_task("a4-levels", "Уровни дерева", "Используя `Node`, `insert`, `build`, напишите `by_levels(values)`: верните список уровней — каждый уровень это список значений слева направо.\n\nПример: `by_levels([5, 3, 8, 1, 4, 9])` → `[[5], [3, 8], [1, 4, 9]]`.",
  "by_levels", NODE + "\n\ndef by_levels(values):\n    root = build(values)\n    levels = []\n    current = [root] if root else []\n    while current:\n        levels.append([node.value for node in current])\n        nxt = []\n        for node in current:\n            if node.left:\n                nxt.append(node.left)\n            if node.right:\n                nxt.append(node.right)\n        current = nxt\n    return levels\n",
  [[[5, 3, 8, 1, 4, 9]], [[]], ([[1]], True), ([[1, 2, 3]], True), ([[4, 2, 6, 1, 3, 5, 7]], True), ([[3, 2, 1]], True)],
  [(NODE + "\n\ndef by_levels(values):\n    root = build(values)\n    levels = []\n    current = [root] if root else []\n    while current:\n        levels.append([node.value for node in current])\n        nxt = []\n        for node in current:\n            if node.right:\n                nxt.append(node.right)\n            if node.left:\n                nxt.append(node.left)\n        current = nxt\n    return levels\n", "На каждом уровне правый потомок идёт перед левым."),
   (NODE + "\n\ndef by_levels(values):\n    root = build(values)\n    return [[v for v in sorted(values)]] if root else []\n", "Все значения возвращены одним уровнем."),
   (NODE + "\n\ndef by_levels(values):\n    root = build(values)\n    levels = []\n    current = [root] if root else []\n    while current:\n        levels.append([node.value for node in current])\n        nxt = []\n        for node in current:\n            if node.left:\n                nxt.append(node.left)\n        current = nxt\n    return levels\n", "Правые потомки не обходятся.")],
  hints("Уровень — это все узлы на одной глубине.", "Начните со списка из корня.", "Для каждого уровня соберите значения, затем потомков для следующего уровня.", "Порядок потомков: сначала левый, потом правый.", "Цикл идёт, пока текущий уровень не пуст."),
  "Обход по уровням: уровень — это список узлов, следующий уровень — потомки по порядку слева направо.")

a5 = predict_task("a5-bst", "Что в дереве", NODE + "\n\nroot = build([6, 2, 9, 1, 4, 7])\nprint(root.left.right.value)\nprint(root.right.left.value, root.right.right)\nnode, steps = root, 0\nwhile node.left:\n    node = node.left\n    steps += 1\nprint(node.value, steps)\n",
  [("4\n7 9\n1 2\n", "root.right.right — пустая ссылка: значение None, а не 9."),
   ("2\n7 None\n1 2\n", "Левый потомок 2 — это узел 2, а его правый потомок — 4.")],
  hints("Вставляем 6, 2, 9, 1, 4, 7: корень 6.", "2 < 6 — влево; 9 > 6 — вправо; 1 < 6, 1 < 2 — влево от 2; 4 < 6, 4 > 2 — вправо от 2; 7 > 6, 7 < 9 — влево от 9.", "root.left.right — это 4.", "У узла 9 нет правого потомка: None.", "Ползём влево до конца: 6 → 2 → 1, два шага."),
  "Дерево: 6 (лево 2 (лево 1, право 4), право 9 (лево 7)). Самое левое значение — минимум.")

mistakes = [
 {"mistake": "Забывают базовый случай «узел пуст»", "fix": "Первой строкой: if node is None: return ...", "errorType": "AttributeError"},
 {"mistake": "Путают порядок обхода", "fix": "In-order: лево → узел → право (для BST — по возрастанию)."},
 {"mistake": "Не присваивают результат рекурсивной вставки", "fix": "node.left = insert(node.left, value)."},
 {"mistake": "Строят дерево из отсортированных данных и получают цепочку", "fix": "Перемешайте данные или применяйте сбалансированные деревья."}]

finish("alg-08-trees", "Деревья", "Строить двоичные деревья поиска, обходить их и считать высоту.",
  {"algo.tree": "Бинарные деревья", "algo.tree.bst": "Дерево поиска (BST)", "algo.tree.traversal": "Обходы дерева"},
  ["alg-07-hash", "alg-04-recursion"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="algorithms")

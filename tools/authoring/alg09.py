from lib import *

BUILD = "def build_graph(edges):\n    graph = {}\n    for a, b in edges:\n        graph.setdefault(a, []).append(b)\n        graph.setdefault(b, []).append(a)\n    for node in graph:\n        graph[node].sort()\n    return graph\n"
BFS = "from collections import deque\n\n\ndef bfs_order(edges, start):\n    graph = build_graph(edges)\n    if start not in graph:\n        return [start]\n    seen = {start}\n    queue = deque([start])\n    order = []\n    while queue:\n        node = queue.popleft()\n        order.append(node)\n        for nxt in graph[node]:\n            if nxt not in seen:\n                seen.add(nxt)\n                queue.append(nxt)\n    return order\n"

begin()
scenes = [
 S("intro", "Сети связей", """
  Карта дорог, друзья в социальной сети, компьютеры в локальной сети, страницы сайта со ссылками друг на друга — всё это графы.
  Граф состоит из вершин и рёбер, которые их соединяют. Дерево — частный случай графа, где нет циклов. Сегодня мы научимся хранить
  граф в программе и обходить его двумя способами: в ширину и в глубину. Эти обходы отвечают на вопросы: можно ли добраться
  из одной вершины в другую и каким путём.""",
  nt("**Граф** = вершины + рёбра. Хранение: словарь «вершина → список соседей»", at="Граф состоит")),
 S("store", "Как хранить граф", """
  Самый удобный способ — словарь, где ключ это вершина, а значение — список соседей. Это называется списком смежности.
  Пусть у нас есть пары дружбы. Для каждой пары добавляем каждого в список соседей другого, потому что дружба взаимна. Такой граф
  называется неориентированным. Если связь идёт только в одну сторону, как подписка в соцсети, граф ориентированный, и
  добавлять нужно только одну сторону.""",
  clr(), t('edges = [("Аня", "Борис"), ("Аня", "Вера"), ("Борис", "Глеб"), ("Дина", "Ева")]\ngraph = {}\n', at="Пусть у нас"),
  t("for a, b in edges:\n    graph.setdefault(a, []).append(b)\n    graph.setdefault(b, []).append(a)\n", at="Для каждой пары"),
  t("for name in graph:\n    print(name, graph[name])\n", at="неориентированным"), run("неориентированным")),
 S("bfs", "Обход в ширину", """
  Обход в ширину посещает вершины по расстоянию от стартовой: сначала соседей, потом соседей соседей. Используется очередь. Кладём
  старт в очередь и в множество посещённых. Затем снимаем вершину из очереди, запоминаем и добавляем всех непосещённых
  соседей. Множество посещённых нужно, чтобы не ходить по кругу, когда в графе есть циклы.""",
  clr(), t("from collections import deque\n\ndef bfs(graph, start):\n    seen = {start}\n    queue = deque([start])\n    order = []\n", at="Кладём"),
  t("    while queue:\n        node = queue.popleft()\n        order.append(node)\n", at="снимаем вершину"),
  t("        for nxt in graph[node]:\n            if nxt not in seen:\n                seen.add(nxt)\n                queue.append(nxt)\n    return order\n\n", at="добавляем всех"),
  t('graph = {"A": ["B", "C"], "B": ["A", "D"], "C": ["A", "D"], "D": ["B", "C"]}\nprint(bfs(graph, "A"))\n', at="Множество посещённых"), run("Множество посещённых")),
 S("path", "Кратчайший путь", """
  Главное свойство обхода в ширину: он находит кратчайший путь по числу рёбер. Вместе с вершиной в очереди будем хранить
  расстояние до неё. Первая найденная цель — самая близкая. Если очередь опустела, а цель не найдена, пути нет, и мы
  вернём минус один.""",
  clr(), t("from collections import deque\n\ndef distance(graph, start, goal):\n    seen = {start}\n    queue = deque([(start, 0)])\n", at="Вместе с вершиной"),
  t("    while queue:\n        node, d = queue.popleft()\n        if node == goal:\n            return d\n", at="Первая найденная"),
  t("        for nxt in graph[node]:\n            if nxt not in seen:\n                seen.add(nxt)\n                queue.append((nxt, d + 1))\n    return -1\n\n", at="Если очередь"),
  t('graph = {"A": ["B", "C"], "B": ["A", "D"], "C": ["A", "D"], "D": ["B", "C"], "E": []}\nprint(distance(graph, "A", "D"), distance(graph, "A", "E"))\n', at="вернём минус"), run("вернём минус")),
 S("dfs", "Обход в глубину", """
  Обход в глубину действует иначе: идёт по одной ветке как можно дальше и только потом возвращается. Естественно записывается
  рекурсией: посетили вершину, затем для каждого непосещённого соседа вызываем ту же функцию. Порядок посещения
  отличается от обхода в ширину, но множество достижимых вершин одно и то же. Глубина нужна, например, для поиска связных
  компонентов и проверки циклов.""",
  clr(), t("def dfs(graph, node, seen=None):\n    if seen is None:\n        seen = []\n    seen.append(node)\n", at="Естественно"),
  t("    for nxt in graph[node]:\n        if nxt not in seen:\n            dfs(graph, nxt, seen)\n    return seen\n\n", at="для каждого"),
  t('graph = {"A": ["B", "C"], "B": ["A", "D"], "C": ["A", "D"], "D": ["B", "C"]}\nprint(dfs(graph, "A"))\n', at="Порядок посещения"), run("Порядок посещения")),
 S("components", "Связные компоненты", """
  Если граф разваливается на несколько несвязанных частей, каждая такая часть называется связной компонентой. Посчитать их
  просто: перебираем вершины, и если вершина ещё не посещена, запускаем от неё обход и увеличиваем счётчик. Всё, что
  обход зацепил, помечено как посещённое, и второй раз мы эту компоненту не посчитаем.""",
  clr(), t('graph = {"A": ["B"], "B": ["A"], "C": [], "D": ["E"], "E": ["D"]}\nseen = set()\ncount = 0\n', at="перебираем вершины"),
  t("def visit(node):\n    seen.add(node)\n    for nxt in graph[node]:\n        if nxt not in seen:\n            visit(nxt)\n\n", at="запускаем"),
  t("for node in graph:\n    if node not in seen:\n        visit(node)\n        count += 1\nprint(count)\n", at="Всё, что"), run("Всё, что")),
 S("summary", "Итог", """
  Подведём итог. Граф хранят как словарь соседей. Обход в ширину использует очередь и находит кратчайшие пути по числу рёбер.
  Обход в глубину использует рекурсию или стек и хорошо подходит для компонент связности. Множество посещённых вершин
  защищает от зацикливания. Остался последний урок по алгоритмам: как делать программы быстрее с помощью запоминания
  результатов и других приёмов.""",
  nt("BFS — очередь, кратчайший путь · DFS — рекурсия/стек, компоненты · `seen` защищает от циклов", at="Подведём итог")),
]

notes = """
# Графы

```python
edges = [("Аня", "Борис"), ("Аня", "Вера"), ("Борис", "Глеб")]
graph = {}
for a, b in edges:
    graph.setdefault(a, []).append(b)
    graph.setdefault(b, []).append(a)
```

## Обход в ширину и расстояние

```python
from collections import deque

def distance(graph, start, goal):
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        node, d = queue.popleft()
        if node == goal:
            return d
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, d + 1))
    return -1
```

## Обход в глубину

```python
def dfs(graph, node, seen=None):
    if seen is None:
        seen = []
    seen.append(node)
    for nxt in graph[node]:
        if nxt not in seen:
            dfs(graph, nxt, seen)
    return seen
```

| | BFS | DFS |
|---|---|---|
| Структура | очередь | стек / рекурсия |
| Кратчайший путь | да | нет |
| Компоненты | да | да |
"""

a1 = fn_task("a1-build", "Список смежности", "Напишите `build_graph(edges)`: `edges` — список пар `[a, b]` (неориентированные рёбра). Верните словарь «вершина → **отсортированный** список соседей». Повторяющиеся рёбра не должны дублировать соседей.\n\nПример: `build_graph([[\"A\", \"B\"], [\"A\", \"C\"]])` → `{\"A\": [\"B\", \"C\"], \"B\": [\"A\"], \"C\": [\"A\"]}`.",
  "build_graph", "def build_graph(edges):\n    graph = {}\n    for a, b in edges:\n        graph.setdefault(a, set()).add(b)\n        graph.setdefault(b, set()).add(a)\n    return {node: sorted(neighbors) for node, neighbors in graph.items()}\n",
  [[[["A", "B"], ["A", "C"]]], [[]], ([[["A", "B"], ["B", "A"], ["A", "B"]]], True), ([[["Х", "Ю"], ["Я", "Х"]]], True), ([[["A", "B"], ["C", "D"], ["B", "C"]]], True)],
  [("def build_graph(edges):\n    graph = {}\n    for a, b in edges:\n        graph.setdefault(a, set()).add(b)\n    return {node: sorted(neighbors) for node, neighbors in graph.items()}\n", "Ребро добавлено только в одну сторону."),
   ("def build_graph(edges):\n    graph = {}\n    for a, b in edges:\n        graph.setdefault(a, []).append(b)\n        graph.setdefault(b, []).append(a)\n    return graph\n", "Соседи не отсортированы и дублируются при повторных рёбрах."),
   ("def build_graph(edges):\n    graph = {}\n    for a, b in edges:\n        graph[a] = [b]\n        graph[b] = [a]\n    return graph\n", "Каждое новое ребро затирает предыдущие.")],
  hints("Для каждого ребра нужны две записи: a → b и b → a.", "Для вершины заведите пустой набор соседей: graph.setdefault(a, set()).", "Множество автоматически убирает дубликаты.", "В конце превратите множества в отсортированные списки.", "{node: sorted(neighbors) for node, neighbors in graph.items()}."),
  "Словарь со множествами защищает от дубликатов; sorted делает результат предсказуемым.")

a2 = fn_task("a2-bfs", "Порядок обхода в ширину", "Заготовлена `build_graph(edges)` (соседи отсортированы). Напишите `bfs_order(edges, start)`: список вершин в порядке обхода в ширину от `start`, соседи — по алфавиту. Если вершины `start` нет в графе, верните `[start]`.\n\nВершины недостижимые из `start` не включаются.",
  "bfs_order", BUILD + "\n\n" + BFS,
  [[[["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"]], "A"], [[["A", "B"], ["C", "D"]], "A"], ([[], "X"], True), ([[["1", "2"], ["2", "3"], ["3", "4"], ["1", "4"]], "3"], True), ([[["A", "B"], ["A", "C"], ["B", "D"], ["C", "E"]], "B"], True)],
  [(BUILD + "\n\ndef bfs_order(edges, start):\n    graph = build_graph(edges)\n    if start not in graph:\n        return [start]\n    order, stack, seen = [], [start], set()\n    while stack:\n        node = stack.pop()\n        if node in seen:\n            continue\n        seen.add(node)\n        order.append(node)\n        stack.extend(graph[node])\n    return order\n", "Используется стек: получается обход в глубину."),
   (BUILD + "\n\ndef bfs_order(edges, start):\n    graph = build_graph(edges)\n    return sorted(graph) if start in graph else [start]\n", "Возвращены все вершины по алфавиту, а не обход."),
   (BUILD + "\n\nfrom collections import deque\n\n\ndef bfs_order(edges, start):\n    graph = build_graph(edges)\n    if start not in graph:\n        return [start]\n    queue = deque([start])\n    order = []\n    while queue:\n        node = queue.popleft()\n        order.append(node)\n        for nxt in graph[node]:\n            if nxt not in order:\n                queue.append(nxt)\n    return order\n", "Вершины добавляются в очередь повторно: порядок содержит дубликаты или зацикливается.")],
  hints("Для обхода в ширину нужна очередь и множество посещённых.", "Положите start в очередь и в seen.", "Снимайте вершину слева, добавляйте её в порядок.", "Каждого непосещённого соседа помечайте в seen сразу при добавлении в очередь.", "Соседи уже отсортированы функцией build_graph."),
  "Очередь гарантирует обход по слоям; пометка при постановке в очередь исключает повторы.",
  starter=BUILD + "\n\ndef bfs_order(edges, start):\n    graph = build_graph(edges)\n    # обход в ширину от start\n    pass\n", type="complete")

a3 = fn_task("a3-dist", "Расстояние между вершинами", "Заготовлена `build_graph(edges)`. Напишите `dist(edges, a, b)`: минимальное число рёбер между `a` и `b`, либо `-1`, если пути нет или вершины нет в графе. `dist(edges, x, x)` для вершины графа равно `0`.",
  "dist", BUILD + "\n\nfrom collections import deque\n\n\ndef dist(edges, a, b):\n    graph = build_graph(edges)\n    if a not in graph or b not in graph:\n        return -1\n    seen = {a}\n    queue = deque([(a, 0)])\n    while queue:\n        node, d = queue.popleft()\n        if node == b:\n            return d\n        for nxt in graph[node]:\n            if nxt not in seen:\n                seen.add(nxt)\n                queue.append((nxt, d + 1))\n    return -1\n",
  [[[["A", "B"], ["B", "C"], ["A", "D"], ["D", "C"], ["C", "E"]], "A", "E"], [[["A", "B"], ["C", "D"]], "A", "D"], ([[["A", "B"]], "A", "A"], True), ([[["A", "B"]], "A", "Z"], True), ([[["1", "2"], ["2", "3"], ["3", "4"], ["4", "5"], ["1", "5"]], "2", "5"], True), ([[], "A", "B"], True)],
  [(BUILD + "\n\nfrom collections import deque\n\n\ndef dist(edges, a, b):\n    graph = build_graph(edges)\n    if a not in graph or b not in graph:\n        return -1\n    seen = {a}\n    stack = [(a, 0)]\n    while stack:\n        node, d = stack.pop()\n        if node == b:\n            return d\n        for nxt in graph[node]:\n            if nxt not in seen:\n                seen.add(nxt)\n                stack.append((nxt, d + 1))\n    return -1\n", "Стек даёт обход в глубину: найденный путь не обязательно кратчайший."),
   (BUILD + "\n\nfrom collections import deque\n\n\ndef dist(edges, a, b):\n    graph = build_graph(edges)\n    seen = {a}\n    queue = deque([(a, 0)])\n    while queue:\n        node, d = queue.popleft()\n        if node == b:\n            return d\n        for nxt in graph.get(node, []):\n            if nxt not in seen:\n                seen.add(nxt)\n                queue.append((nxt, d + 1))\n    return 0\n", "Если пути нет, возвращается 0 вместо -1."),
   (BUILD + "\n\nfrom collections import deque\n\n\ndef dist(edges, a, b):\n    graph = build_graph(edges)\n    if a not in graph or b not in graph:\n        return -1\n    seen = {a}\n    queue = deque([(a, 1)])\n    while queue:\n        node, d = queue.popleft()\n        if node == b:\n            return d\n        for nxt in graph[node]:\n            if nxt not in seen:\n                seen.add(nxt)\n                queue.append((nxt, d + 1))\n    return -1\n", "Отсчёт начинается с 1, а не с 0.")],
  hints("Кратчайший путь по числу рёбер ищет обход в ширину.", "Храните в очереди пары (вершина, расстояние).", "Старт имеет расстояние 0.", "Когда сняли вершину b — верните её расстояние.", "Если очередь опустела — путь не найден: -1."),
  "BFS посещает вершины в порядке возрастания расстояния, поэтому первая найденная цель — ближайшая.")

a4 = fn_task("a4-components", "Сколько групп", "Напишите `count_groups(n, edges)`: в графе вершины `0 … n-1` и рёбра `edges` (пары чисел). Верните число связных компонент (вершины без рёбер — отдельные компоненты).",
  "count_groups", "def count_groups(n, edges):\n    graph = {i: [] for i in range(n)}\n    for a, b in edges:\n        graph[a].append(b)\n        graph[b].append(a)\n    seen = set()\n    count = 0\n    for start in range(n):\n        if start in seen:\n            continue\n        count += 1\n        stack = [start]\n        seen.add(start)\n        while stack:\n            node = stack.pop()\n            for nxt in graph[node]:\n                if nxt not in seen:\n                    seen.add(nxt)\n                    stack.append(nxt)\n    return count\n",
  [[5, [[0, 1], [3, 4]]], [3, []], ([0, []], True), ([4, [[0, 1], [1, 2], [2, 3]]], True), ([6, [[0, 1], [2, 3], [4, 5], [1, 2]]], True), ([1, []], True), ([3, [[0, 1], [1, 2], [2, 0]]], True)],
  [("def count_groups(n, edges):\n    return n - len(edges)\n", "Формула верна только для лесов без циклов и дубликатов; на графах с циклами даёт неверный результат."),
   ("def count_groups(n, edges):\n    return len(edges)\n", "Возвращено число рёбер."),
   ("def count_groups(n, edges):\n    graph = {i: [] for i in range(n)}\n    for a, b in edges:\n        graph[a].append(b)\n        graph[b].append(a)\n    seen = set()\n    count = 0\n    for start in range(n):\n        if start in seen:\n            continue\n        count += 1\n        stack = [start]\n        while stack:\n            node = stack.pop()\n            if node in seen:\n                continue\n            seen.add(node)\n            stack.extend(graph[node])\n    return count - 1\n", "Результат уменьшен на единицу.")],
  hints("Перебирайте вершины от 0 до n-1.", "Если вершина ещё не посещена — это новая компонента.", "От неё запустите обход (DFS или BFS), пометив все достижимые вершины.", "Увеличивайте счётчик перед каждым запуском обхода.", "Изолированная вершина тоже даёт компоненту."),
  "Каждый запуск обхода «закрашивает» целую компоненту, поэтому число запусков равно числу компонент.")

a5 = predict_task("a5-order", "BFS или DFS", 'graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}\n\ndef dfs(node, seen):\n    seen.append(node)\n    for nxt in graph[node]:\n        if nxt not in seen:\n            dfs(nxt, seen)\n    return seen\n\nprint(dfs("A", []))\n',
  [("['A', 'B', 'C', 'D']\n", "Это порядок обхода в ширину; DFS уходит вглубь: A → B → D, затем C."),
   ("['A', 'B', 'D']\n", "После возврата из ветви B обход продолжается: C тоже посещается.")],
  hints("DFS из A идёт к первому соседу — B.", "Из B идём в D.", "У D нет соседей — возвращаемся к A.", "Следующий сосед A — C; D уже посещён.", "Порядок: A, B, D, C."),
  "Обход в глубину сначала доходит до конца ветви, а потом возвращается назад.")

mistakes = [
 {"mistake": "Не ведут множество посещённых вершин", "fix": "Иначе обход зацикливается на графе с циклами."},
 {"mistake": "Добавляют ребро только в одну сторону в неориентированном графе", "fix": "Добавляйте и a → b, и b → a."},
 {"mistake": "Используют DFS для кратчайшего пути", "fix": "Кратчайший путь по числу рёбер находит BFS."},
 {"mistake": "Отмечают вершину посещённой при снятии из очереди", "fix": "Отмечайте при постановке в очередь, чтобы не добавить её дважды."}]

finish("alg-09-graphs", "Графы", "Хранить граф списками смежности, обходить его в ширину и в глубину, искать кратчайшие пути и компоненты связности.",
  {"algo.graph": "Графы и списки смежности", "algo.graph.bfs": "Обход в ширину", "algo.graph.dfs": "Обход в глубину"},
  ["alg-08-trees", "alg-06-stack-queue"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="algorithms")

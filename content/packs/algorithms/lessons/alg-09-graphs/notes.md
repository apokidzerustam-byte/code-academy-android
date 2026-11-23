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

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

# Стек и очередь

## Стек

```python
stack = []
stack.append(1)
stack.append(2)
print(stack.pop())   # 2
```

## Скобки

```python
def balanced(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack
```

## Очередь

```python
from collections import deque

queue = deque()
queue.append("Аня")
queue.append("Борис")
print(queue.popleft())   # Аня
```

| | Стек | Очередь |
|---|---|---|
| Порядок | LIFO | FIFO |
| Добавить | `append` | `append` |
| Взять | `pop()` | `popleft()` |

# Code review

```python
def average(numbers):
    return sum(numbers) / len(numbers)   # пустой список → ZeroDivisionError

import ast
print(ast.literal_eval("[1, 2, 3]"))     # безопасно, в отличие от eval
```

## Чек-лист

1. Верно ли работает (границы: пусто, 0, минус).
2. Понятно ли (имена, размер).
3. Безопасно ли (ввод пользователя).
4. Есть ли тесты.
5. Нет ли лишнего.

Замечание: конкретно, вежливо, с причиной.

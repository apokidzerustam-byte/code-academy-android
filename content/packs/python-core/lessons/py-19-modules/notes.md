# Модули и стандартная библиотека

```python
import math
print(math.sqrt(49), math.pi)

from math import floor, ceil
print(floor(2.7), ceil(2.1))

import math as m
print(m.hypot(3, 4))
```

## Случайные числа

```python
import random

colors = ["красный", "синий", "зелёный"]
print(random.choice(colors) in colors)        # True
print(1 <= random.randint(1, 6) <= 6)         # True
random.seed(1)                                # воспроизводимость
```

## Даты

```python
from datetime import date, timedelta

a = date(2026, 11, 23)
b = date.fromisoformat("2026-12-31")
print((b - a).days)               # 38
print(a + timedelta(days=10))     # 2026-12-03
print(a.weekday())                # 0 — понедельник
```

## collections

```python
from collections import Counter, defaultdict

print(Counter("абракадабра").most_common(2))   # [('а', 5), ('б', 2)]

groups = defaultdict(list)
for word in ["арбуз", "банан", "абрикос"]:
    groups[word[0]].append(word)
print(dict(groups))
```

## Запомните

1. `import модуль` → вызов `модуль.функция()`.
2. `from модуль import имя` → вызов без приставки.
3. Свой файл `tools.py` импортируется как `import tools`.

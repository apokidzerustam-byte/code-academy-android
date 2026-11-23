# JSON

```python
import json

person = {"name": "Аня", "age": 25, "marks": [5, 4], "active": True, "phone": None}
print(json.dumps(person, ensure_ascii=False))
print(json.dumps(person, ensure_ascii=False, indent=2))
```

| Python | JSON |
| --- | --- |
| `dict` | объект `{}` |
| `list`, `tuple` | массив `[]` |
| `str` | строка |
| `int`, `float` | число |
| `True` / `False` | `true` / `false` |
| `None` | `null` |

## Из JSON в Python

```python
import json

text = '[{"name": "хлеб", "price": 40, "qty": 2}, {"name": "сыр", "price": 350, "qty": 1}]'
items = json.loads(text)
print(sum(i["price"] * i["qty"] for i in items))   # 430
```

## Файлы

```python
import json

settings = {"theme": "тёмная", "font": 18, "sound": True}
with open("settings.json", "w", encoding="utf-8") as f:
    json.dump(settings, f, ensure_ascii=False, indent=2)
with open("settings.json", encoding="utf-8") as f:
    print(json.load(f) == settings)    # True
```

## Ошибки

```python
import json

try:
    json.loads('{"a": 1,}')
except ValueError:
    print("некорректный JSON")
```

## Запомните

1. `s` в имени — работа со строкой, без `s` — с файлом.
2. `ensure_ascii=False` сохраняет кириллицу читаемой.
3. Всегда обрабатывайте `JSONDecodeError` (это `ValueError`) для внешних данных.

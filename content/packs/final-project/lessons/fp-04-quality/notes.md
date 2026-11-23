# Качество проекта

```python
def parse_amount(text):
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value > 0 else None

cases = [("12.5", 12.5), ("0", None), ("-3", None), ("abc", None), ("", None), (" 7 ", 7.0)]
for text, expected in cases:
    assert parse_amount(text) == expected, text
print("все тесты прошли")
```

Ошибка → воспроизвести → сузить → исправить → тест, чтобы не вернулась.

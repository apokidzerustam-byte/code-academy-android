# unittest

```python
import unittest

def add(a, b):
    return a + b

class TestAdd(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(add(2, 3), 5)

    def test_negative(self):
        self.assertEqual(add(-1, -1), -2)
```

На компьютере: `python -m unittest`.

## Методы проверки

- `assertEqual(a, b)`, `assertTrue(x)`, `assertFalse(x)`
- `assertIn(x, коллекция)`, `assertIsNone(x)`
- `assertAlmostEqual(a, b)` — для дробей
- `with self.assertRaises(ValueError): ...` — ожидаем исключение

## Провал и ошибка

Провал (failure) — проверка не сошлась. Ошибка (error) — исключение в коде или в тесте.

## setUp

Метод `setUp` выполняется перед каждым тестом и создаёт свежее состояние.

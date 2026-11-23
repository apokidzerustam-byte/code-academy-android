# Отладка

## Типы ошибок

- `IndexError` — индекс вне списка
- `KeyError` — нет ключа в словаре
- `ValueError` — неверное значение (например, `int("x1")`)
- `AttributeError` — у значения нет такого метода (часто `None`)

## logging

```python
import logging, sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="%(levelname)s: %(message)s")
logging.info("запуск")
logging.warning("предупреждение")
```

Уровни по возрастанию: DEBUG, INFO, WARNING, ERROR.

## Классические ловушки

- `range(5)` даёт 0…4
- значение по умолчанию `[]` общее для всех вызовов: используйте `None`
- изменение списка во время обхода

## Метод

Воспроизвести → гипотеза → проверить → исправить → написать тест.

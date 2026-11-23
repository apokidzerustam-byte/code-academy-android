# Документация

```python
def price_with_vat(price: float, rate: float = 0.23) -> float:
    """Возвращает цену с налогом, округлённую до копеек."""
    return round(price * (1 + rate), 2)

print(price_with_vat.__doc__)
print(price_with_vat.__annotations__)
```

## README

```text
# Название
Описание.
## Запуск
команда
```

Документация должна совпадать с кодом.

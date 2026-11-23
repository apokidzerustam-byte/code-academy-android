# Читаемый код

```python
VAT_RATE = 0.23

def price_with_vat(price, vat_rate=VAT_RATE):
    return price * (1 + vat_rate)

def flat(x, y):
    if x <= 0:
        return 0
    if y <= 0:
        return x
    return x * y

print(price_with_vat(100))
print(flat(3, 4))
```

## Правила

1. Название отвечает на вопрос «что это?» или «что делает?».
2. Число с смыслом — в константу.
3. Одна функция — одна задача.
4. Особые случаи — ранним возвратом.

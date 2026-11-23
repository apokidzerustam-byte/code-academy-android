# Производительность и логирование

## Сначала измерьте

```python
import time

start = time.perf_counter()
total = sum(range(1000))
elapsed = time.perf_counter() - start
print(total, elapsed < 1)
```

- замеряйте несколько раз, берите лучший результат;
- для сравнения алгоритмов считайте шаги, а не секунды;
- ускоряйте то место, которое измерили, а не то, которое кажется медленным.

## Ускорение

- структура данных: `set` и `dict` ищут быстро, `in` по списку медленно;
- кэш: `functools.lru_cache` не считает одно и то же дважды, но занимает память и может устареть;
- Android: основной поток — только экран, долгое — в фоне.

## Журнал

```python
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("shop.orders")
log.info("заказ %s создан", 42)
```

Уровни: `DEBUG` < `INFO` < `WARNING` < `ERROR` < `CRITICAL`.

Не журналируйте пароли, токены, номера карт и личные данные: маскируйте их перед записью.

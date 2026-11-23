# Асинхронность (asyncio)

```python
import asyncio

async def greet(name):
    await asyncio.sleep(0.01)
    return f"Привет, {name}"

print(asyncio.run(greet("Аня")))
```

## Несколько задач сразу

```python
import asyncio

async def worker(name, delay):
    await asyncio.sleep(delay)
    print(name)

async def main():
    await asyncio.gather(worker("A", 0.06), worker("B", 0.02), worker("C", 0.04))
    print("готово")

asyncio.run(main())    # B C A готово
```

## Результаты и таймаут

```python
import asyncio

async def double(ms):
    await asyncio.sleep(ms / 1000)
    return ms * 2

async def main():
    return await asyncio.gather(double(60), double(20), double(40))

print(asyncio.run(main()))    # [120, 40, 80]
```

## Запомните

1. `await` — только внутри `async def`.
2. `gather` возвращает результаты в порядке передачи.
3. Асинхронность помогает при ожидании, а не при вычислениях.
4. В заданиях с `asyncio` выбирайте режим «Авто» или A в настройках исполнителя.

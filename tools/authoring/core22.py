from lib import *

begin()
scenes = [
 S("intro", "Ожидание — не работа", """
  Программа, которая скачивает данные из сети или читает большой файл, большую часть времени просто ждёт. Пока она ждёт ответа
  сервера, процессор простаивает. Если нужно скачать десять страниц одну за другой, суммарное время будет десять раз по
  времени одной. Асинхронное программирование решает эту проблему: пока одна задача ждёт, программа успевает заняться другой.
  Важно понять: это не параллельная работа нескольких процессоров, а умное чередование задач в ожидании.""",
  nt("**Асинхронность** — пока одна задача ждёт, выполняется другая", at="Асинхронное")),
 S("coroutine", "Корутины: async и await", """
  Асинхронная функция объявляется словами async def. Её вызов сам по себе ничего не выполняет, а создаёт корутину — заготовку
  работы. Запустить её можно функцией asyncio точка run. Внутри асинхронной функции слово await означает: «здесь я жду
  результат, пока я жду, выполняйте что-нибудь другое». Функция asyncio точка sleep имитирует ожидание, как будто мы ждём
  ответа от сервера.""",
  clr(), t('import asyncio\n\nasync def greet(name):\n    await asyncio.sleep(0.01)\n    return f"Привет, {name}"\n\n', at="Асинхронная функция"),
  t('print(greet("Аня"))\n', at="Её вызов"),
  t('print(asyncio.run(greet("Аня")))\n', at="Запустить её"), run("Функция asyncio")),
 S("sequential", "Последовательно и вместе", """
  Допустим, у нас три задачи с разной длительностью. Если ждать их одну за другой через await, общее время равно сумме. Функция
  gather запускает все задачи сразу и ждёт, пока завершатся все, а общее время равно самой долгой из них. Каждая задача
  печатает своё имя, когда заканчивается. Заметьте порядок вывода: первой закончится самая короткая задача, а не первая в
  списке.""",
  clr(), t('import asyncio\n\nasync def worker(name, delay):\n    await asyncio.sleep(delay)\n    print(name)\n\n', at="Допустим"),
  t('async def main():\n    await asyncio.gather(worker("A", 0.06), worker("B", 0.02), worker("C", 0.04))\n    print("готово")\n\n', at="Функция gather"),
  t("asyncio.run(main())\n", at="Каждая задача"), run("Заметьте порядок")),
 S("results", "Результаты gather", """
  Функция gather возвращает список результатов в том порядке, в котором задачи были переданы, а не в том, в котором они
  завершились. Это удобно: результат первой задачи всегда лежит на первом месте. Напишем корутину, которая возвращает
  удвоенную задержку, и соберём результаты трёх задач.""",
  clr(), t('import asyncio\n\nasync def double(ms):\n    await asyncio.sleep(ms / 1000)\n    return ms * 2\n\n', at="Напишем корутину"),
  t('async def main():\n    return await asyncio.gather(double(60), double(20), double(40))\n\n', at="соберём результаты"),
  t("print(asyncio.run(main()))\n", at="соберём результаты"), run("соберём результаты")),
 S("timeout", "Таймаут", """
  Ожидание не должно быть вечным. Функция wait_for ограничивает время: если задача не успела за отведённые секунды, возникает
  исключение TimeoutError, которое можно перехватить. Так программа не зависает, если сервер молчит. Задача, которая
  ждёт десять миллисекунд, укладывается в сто, а ждущая двести миллисекунд — нет.""",
  clr(), t('import asyncio\n\nasync def slow(ms):\n    await asyncio.sleep(ms / 1000)\n    return "ok"\n\n', at="Функция wait_for"),
  t('async def main(ms, limit):\n    try:\n        return await asyncio.wait_for(slow(ms), limit / 1000)\n    except asyncio.TimeoutError:\n        return "timeout"\n\n', at="Так программа"),
  t("print(asyncio.run(main(10, 100)), asyncio.run(main(200, 20)))\n", at="Задача, которая"), run("Задача, которая")),
 S("when", "Когда это нужно", """
  Асинхронность выигрывает там, где много ожидания: сетевые запросы, чтение файлов, таймеры. Для тяжёлых вычислений она не
  поможет: пока процессор занят расчётом, переключиться на другую задачу нельзя. Обратите внимание ещё на одно. Слово await
  можно использовать только внутри async def, а вызвать асинхронный код из обычной программы можно через asyncio точка run.
  В Android-приложениях асинхронность представлена корутинами Kotlin, и идеи там те же самые.""",
  nt("Ожидание (сеть, файлы, таймеры) → `async`. Тяжёлые вычисления → не помогает.", at="Асинхронность выигрывает")),
 S("summary", "Итог", """
  Подведём итог. Функция, объявленная через async def, возвращает корутину. Запустить её можно через asyncio точка run, а внутри
  использовать await для ожидания. Функция gather запускает много задач сразу и возвращает результаты в порядке передачи. Для
  защиты от зависаний есть wait_for с таймаутом. Асинхронность экономит время на ожидании, но не ускоряет вычисления. Дальше —
  основы протокола HTTP, на котором строится большая часть интернета.""",
  nt("`async def` · `await` · `asyncio.run` · `asyncio.gather` · `asyncio.wait_for`", at="Подведём итог")),
]

notes = """
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
"""

a1 = fn_task("a1-gather", "Результаты всех задач", "Напишите функцию `double_all(delays)`: для каждой задержки в миллисекундах запустите асинхронно (`asyncio.gather`) задачу, которая ждёт `delay / 1000` секунд и возвращает `delay * 2`. Верните список результатов **в порядке исходного списка**. Функция синхронная: внутри запускайте `asyncio.run`.\n\nПример: `double_all([60, 20, 40])` → `[120, 40, 80]`.",
  "double_all", "import asyncio\n\n\nasync def double(ms):\n    await asyncio.sleep(ms / 1000)\n    return ms * 2\n\n\nasync def main(delays):\n    return list(await asyncio.gather(*(double(d) for d in delays)))\n\n\ndef double_all(delays):\n    return asyncio.run(main(delays))\n",
  [[[60, 20, 40]], [[]], ([[10]], True), ([[50, 10, 30, 20]], True)],
  [("import asyncio\n\n\nasync def double(ms):\n    await asyncio.sleep(ms / 1000)\n    return ms * 2\n\n\nasync def main(delays):\n    results = await asyncio.gather(*(double(d) for d in delays))\n    return sorted(results)\n\n\ndef double_all(delays):\n    return asyncio.run(main(delays))\n", "Результаты отсортированы вместо исходного порядка."),
   ("import asyncio\n\n\nasync def double(ms):\n    await asyncio.sleep(ms / 1000)\n    return ms\n\n\nasync def main(delays):\n    return list(await asyncio.gather(*(double(d) for d in delays)))\n\n\ndef double_all(delays):\n    return asyncio.run(main(delays))\n", "Задержка не удвоена.")],
  hints("Нужна корутина, которая ждёт и возвращает результат.", "Корутину объявляют через async def, ожидание — await asyncio.sleep(...).", "Все корутины запускают одной командой asyncio.gather(*корутины).", "gather сам сохраняет порядок результатов.", "В обычной функции вызовите asyncio.run(main(delays))."),
  "gather возвращает результаты в порядке передачи задач независимо от того, какая закончилась первой.")

a2 = fn_task("a2-order", "Порядок завершения", "Напишите функцию `finish_order(delays)`: запустите задачи с задержками (в миллисекундах) одновременно и верните список **индексов** задач в порядке их завершения (задержки в тестах различаются не менее чем на 40 мс).\n\nПример: `finish_order([100, 20, 60])` → `[1, 2, 0]`.",
  "finish_order", "import asyncio\n\n\nasync def worker(i, ms, done):\n    await asyncio.sleep(ms / 1000)\n    done.append(i)\n\n\nasync def main(delays):\n    done = []\n    await asyncio.gather(*(worker(i, d, done) for i, d in enumerate(delays)))\n    return done\n\n\ndef finish_order(delays):\n    return asyncio.run(main(delays))\n",
  [[[100, 20, 60]], [[]], ([[40]], True), ([[120, 40, 80, 160, 0]], True)],
  [("def finish_order(delays):\n    return list(range(len(delays)))\n", "Возвращён порядок запуска, а не завершения."),
   ("def finish_order(delays):\n    return sorted(range(len(delays)), key=lambda i: -delays[i])\n", "Порядок от самой долгой задачи к самой короткой — наоборот.")],
  hints("Каждая задача должна отметить себя, когда закончит ожидание.", "Заведите общий список done и дописывайте в него индекс после sleep.", "Запустите все задачи через gather — они ждут одновременно.", "Задача с меньшей задержкой дописывается раньше.", "Верните накопленный список done после ожидания gather."),
  "Порядок завершения определяется задержками, а не порядком запуска: короткие задачи заканчиваются раньше.")

a3 = fn_task("a3-timeout", "С таймаутом", "Напишите функцию `try_wait(ms, limit)`: запускает ожидание `ms` миллисекунд с ограничением `limit` миллисекунд (`asyncio.wait_for`). Верните `\"ok\"`, если уложились, и `\"timeout\"`, если нет. Задержки в тестах различаются не менее чем на 40 мс.\n\nПримеры: `try_wait(10, 100)` → `\"ok\"`, `try_wait(200, 20)` → `\"timeout\"`.",
  "try_wait", "import asyncio\n\n\nasync def slow(ms):\n    await asyncio.sleep(ms / 1000)\n    return \"ok\"\n\n\nasync def main(ms, limit):\n    try:\n        return await asyncio.wait_for(slow(ms), limit / 1000)\n    except asyncio.TimeoutError:\n        return \"timeout\"\n\n\ndef try_wait(ms, limit):\n    return asyncio.run(main(ms, limit))\n",
  [[10, 100], [200, 20], ([0, 60], True), ([300, 100], True), ([50, 150], True)],
  [("import asyncio\n\n\nasync def slow(ms):\n    await asyncio.sleep(ms / 1000)\n    return \"ok\"\n\n\ndef try_wait(ms, limit):\n    return asyncio.run(slow(ms))\n", "Таймаут не применяется: на долгое ожидание вернётся «ok»."),
   ("import asyncio\n\n\nasync def slow(ms):\n    await asyncio.sleep(ms / 1000)\n    return \"ok\"\n\n\nasync def main(ms, limit):\n    try:\n        return await asyncio.wait_for(slow(ms), limit / 1000)\n    except asyncio.TimeoutError:\n        return \"ok\"\n\n\ndef try_wait(ms, limit):\n    return asyncio.run(main(ms, limit))\n", "При таймауте возвращается «ok».")],
  hints("Нужно ограничить ожидание по времени.", "Для этого есть asyncio.wait_for(корутина, секунды).", "Лимит задан в миллисекундах — переведите в секунды.", "При превышении возникает asyncio.TimeoutError — перехватите его.", "except asyncio.TimeoutError: return 'timeout'."),
  "wait_for отменяет задачу, если она не уложилась в лимит, и вызывает исключение, которое мы превращаем в ответ.")

a4 = predict_task("a4-gather-order", "Кто закончит первым", 'import asyncio\n\nasync def worker(name, delay):\n    await asyncio.sleep(delay)\n    print(name)\n    return name.lower()\n\nasync def main():\n    results = await asyncio.gather(worker("A", 0.06), worker("B", 0.02), worker("C", 0.04))\n    print(results)\n\nasyncio.run(main())\n',
  [("A\nB\nC\n['a', 'b', 'c']\n", "Печать идёт в порядке завершения: B (0.02), C (0.04), A (0.06)."),
   ("B\nC\nA\n['b', 'c', 'a']\n", "gather возвращает результаты в порядке передачи задач, а не завершения.")],
  hints("Каждая задача печатает имя после ожидания.", "Меньшая задержка — раньше печать.", "Порядок печати: B, C, A.", "Список results собирается gather по порядку аргументов.", "Это ['a', 'b', 'c']."),
  "Печать происходит по мере завершения задач, а итоговый список gather сохраняет порядок вызова.")

mistakes = [
 {"mistake": "Вызывают async-функцию как обычную: greet('Аня')", "fix": "Это создаст только корутину. Запустите через asyncio.run(...) или await."},
 {"mistake": "Используют await вне async def", "fix": "await допустим только внутри асинхронной функции.", "errorType": "SyntaxError"},
 {"mistake": "Используют time.sleep внутри async вместо asyncio.sleep", "fix": "time.sleep блокирует всё приложение; ждите через await asyncio.sleep."},
 {"mistake": "Ждут ускорения тяжёлых вычислений", "fix": "Асинхронность ускоряет ожидание, а не расчёты."}]

finish("py-22-async", "Асинхронность", "Писать корутины, запускать несколько задач через gather и ограничивать ожидание таймаутом.",
  {"python.async": "async и await", "python.async.gather": "asyncio.gather", "python.async.timeout": "Таймауты: wait_for"},
  ["py-21-inheritance"], scenes, notes, [a1, a2, a3, a4], mistakes, pack="python-core", runner="A")

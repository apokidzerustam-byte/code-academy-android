"""Урок JS 4: асинхронность — таймеры, промисы, async/await."""
from jsib import *

J1 = """console.log("1: старт");
setTimeout(() => console.log("3: таймер"), 0);
console.log("2: конец кода");
"""
J2 = """const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

wait(50).then(() => console.log("прошло 50 мс"));
console.log("ждём…");
"""
J3 = """const wait = (ms, value) => new Promise((r) => setTimeout(() => r(value), ms));

async function main() {
  const a = await wait(30, "A");
  const b = await wait(10, "B");
  console.log(a + b);
}

main();
console.log("main запущена");
"""
J4 = """async function load(id) {
  if (id < 0) throw new Error("плохой id");
  return id * 2;
}

async function run() {
  try {
    console.log(await load(2));
    console.log(await load(-1));
  } catch (e) {
    console.log("Ошибка:", e.message);
  }
}

run();
"""
J5 = """const wait = (ms, value) => new Promise((r) => setTimeout(() => r(value), ms));

Promise.all([wait(30, "x"), wait(10, "y")]).then((r) => console.log(r));
"""
o1, o2, o3, o4, o5 = js_run(J1), js_run(J2), js_run(J3), js_run(J4), js_run(J5)

use_file("main.js")
scenes = [
    scene("intro", "Почему нужна асинхронность", """
      Представьте, что программа запросила данные из сети и ждёт ответа секунду. Если бы всё остановилось, страница замерла бы:
      кнопки не нажимались бы. В JavaScript долгие действия запускаются, а программа идёт дальше и вернётся к результату,
      когда он будет готов. Это называется асинхронностью. Сегодня разберём таймеры, обещания и слова async и await.""",
          [NOTE("Асинхронность: **запустили и пошли дальше**, результат придёт позже.", at="В JavaScript")]),
    scene("timer", "Таймер и порядок выполнения", """
      Функция setTimeout откладывает действие. Даже с задержкой ноль миллисекунд оно выполнится не сразу, а когда закончится
      текущий код. Поэтому сначала напечатаются первая и вторая строки, и только потом таймер. Запускаем: порядок вывода не
      совпадает с порядком строк в коде.""",
          [CLEAR(), T(J1, at="Функция setTimeout"), HL([2], at="Функция setTimeout"), RUN(at="Запускаем"), OUT(o1, at="Запускаем")]),
    scene("promise", "Promise — обещание результата", """
      Promise, обещание, представляет результат, которого ещё нет. Мы создаём вспомогательную функцию wait: она возвращает обещание,
      которое выполнится через заданное время. Метод then принимает функцию, которую вызовут, когда обещание будет выполнено.
      Запускаем: сначала «ждём», а через пятьдесят миллисекунд сообщение из then.""",
          [CLEAR(), T(J2, at="Promise"), HL([1], at="Мы создаём"), HL([3], at="Метод then"), RUN(at="Запускаем"), OUT(o2, at="Запускаем")]),
    scene("await", "async и await", """
      Цепочки then быстро становятся громоздкими. Слова async и await делают асинхронный код похожим на обычный. Функция с
      async возвращает обещание. А await приостанавливает только её, пока обещание не выполнится, и отдаёт значение. Запускаем:
      main запущена печатается сразу, не дожидаясь, а результат склеенных букв приходит позже.""",
          [CLEAR(), T(J3, at="Цепочки"), HL([3], at="Функция с"), HL([4, 5], at="А await приостанавливает"), RUN(at="Запускаем"), OUT(o3, at="Запускаем")]),
    scene("errors", "Ошибки в async-коде", """
      Если внутри async-функции бросить исключение, обещание завершится отказом, а await превратит этот отказ в обычное исключение.
      Поэтому ловить ошибки можно привычным try и catch. Здесь первая загрузка проходит, вторая выбрасывает ошибку, и мы
      видим сообщение. Запускаем.""",
          [CLEAR(), T(J4, at="Если внутри"), HL([2], at="бросить"), HL([8, 9, 10, 11, 12], at="try"), RUN(at="Запускаем"), OUT(o4, at="Запускаем")]),
    scene("all", "Несколько обещаний сразу", """
      Если запросы не зависят друг от друга, их можно запускать одновременно. Promise точка all принимает массив обещаний и
      выполняется, когда готовы все. Результаты приходят в том же порядке, как в массиве, даже если второе обещание готово
      раньше. Запускаем.""",
          [CLEAR(), T(J5, at="Если запросы"), HL([3], at="Promise точка all"), RUN(at="Запускаем"), OUT(o5, at="Запускаем")]),
    scene("summary", "Итог", """
      Подведём итог. Долгие действия не блокируют программу: сначала выполняется весь текущий код, а отложенное идёт после.
      Promise представляет будущий результат. Async и await позволяют писать ожидание как обычный код, а ошибки ловятся через try и
      catch. Promise точка all ждёт несколько обещаний одновременно.""",
          [NOTE("`setTimeout` · `new Promise` · `.then` · `async/await` · `try/catch` · `Promise.all`", at="Подведём")]),
]
use_file(None)

notes = """
# JavaScript: асинхронность

```js
setTimeout(() => console.log("позже"), 0);   // откладывает до конца текущего кода

const wait = (ms, value) =>
  new Promise((resolve) => setTimeout(() => resolve(value), ms));

wait(50, "ok").then((v) => console.log(v));

async function main() {
  try {
    const a = await wait(30, "A");           // ждём, не блокируя страницу
    console.log(a);
  } catch (e) {
    console.log("Ошибка:", e.message);
  }
}

Promise.all([wait(30, "x"), wait(10, "y")]).then(console.log);   // ["x", "y"]
```

- Сначала выполняется весь синхронный код, потом микрозадачи (`then`, `await`), затем таймеры.
- `async`-функция всегда возвращает `Promise`.
- Забытый `await` даёт `Promise` вместо значения (в выводе — `[object Promise]`, в вычислениях — `NaN`).
- `await` только внутри `async`-функции.
"""

PRE = "const getNumber = (n) => new Promise((resolve) => setTimeout(() => resolve(n), 10));\n\n"

a1 = fn_task("a1-delay", "write", "Своя задержка",
    "Напишите функцию `delay(ms, value)`: **возвращает** `Promise`, который через `ms` миллисекунд выполняется значением `value`.",
    "Создавать Promise с таймером.", "delay",
    [([10, "ok"], "ok"), ([0, 5], 5), ([20, [1, 2]], [1, 2], "Значение любого типа")],
    "function delay(ms, value) {\n  return new Promise((resolve) => setTimeout(() => resolve(value), ms));\n}\n",
    "function delay(ms, value) {\n  // ваш код\n}\n",
    [("function delay(ms, value) {\n  return new Promise((resolve) => setTimeout(resolve, ms));\n}\n", "Обещание выполняется без значения: undefined."),
     ("function delay(ms, value) {\n  return new Promise((resolve) => {});\n}\n", "Обещание никогда не выполняется."),
     ("function delay(ms, value) {\n  return new Promise((resolve) => setTimeout(() => resolve(ms), ms));\n}\n", "Вместо value передаётся ms.")],
    hints("Нужно вернуть новый Promise.", "new Promise((resolve) => { … }) — внутри вызовите resolve, когда результат готов.", "Отложить вызов поможет setTimeout.", "Передайте resolve значение value.", "setTimeout(() => resolve(value), ms)"),
    "Promise выполняется, когда вызван resolve(value); setTimeout откладывает этот вызов на ms миллисекунд.", expected_text="Promise со значением value.")

a2 = fn_task("a2-sum-async", "write", "Сумма из двух запросов",
    "Дана функция `getNumber(n)`: она возвращает `Promise` с числом `n` (через 10 мс). Напишите **async**-функцию `sumAsync(a, b)`: получает оба числа через `getNumber` и возвращает их сумму.",
    "Использовать await.", "sumAsync",
    [([2, 3], 5), ([10, -4], 6), ([0, 0], 0), ([1.5, 2.5], 4)],
    PRE + "async function sumAsync(a, b) {\n  const x = await getNumber(a);\n  const y = await getNumber(b);\n  return x + y;\n}\n",
    PRE + "async function sumAsync(a, b) {\n  // ваш код\n}\n",
    [(PRE + "async function sumAsync(a, b) {\n  return getNumber(a) + getNumber(b);\n}\n", "Без await складываются обещания: результат — строка «[object Promise]…»."),
     (PRE + "async function sumAsync(a, b) {\n  const x = await getNumber(a);\n  return x;\n}\n", "Второе число потеряно.")],
    hints("Слово await ставят перед обещанием: оно отдаёт значение.", "Дождитесь первого числа: const x = await getNumber(a).", "Так же получите второе число.", "Верните сумму получившихся чисел.", "return x + y;"),
    "await приостанавливает функцию до результата обещания и возвращает число; async-функция вернёт Promise с суммой.", input_text="Два числа.")

a3 = fn_task("a3-fix-await", "fix", "Забытый await",
    "Функция `doubleAsync(n)` должна вернуть число, **удвоенное** результатом `getNumber(n)`, но возвращает `NaN`. Найдите причину.",
    "Находить пропущенный await.", "doubleAsync",
    [([4], 8), ([0], 0), ([-3], -6), ([2.5], 5)],
    PRE + "async function doubleAsync(n) {\n  const x = await getNumber(n);\n  return x * 2;\n}\n",
    PRE + "async function doubleAsync(n) {\n  const x = getNumber(n);\n  return x * 2;\n}\n",
    [(PRE + "async function doubleAsync(n) {\n  const x = getNumber(n);\n  return await (x * 2);\n}\n", "await стоит не там: умножается само обещание.")],
    hints("Выведите x в консоль: что в нём лежит?", "getNumber возвращает не число, а обещание.", "Умножать обещание на 2 нельзя — получается NaN.", "Перед вызовом, который возвращает обещание, нужен await.", "const x = await getNumber(n);"),
    "Без await переменная x хранит Promise, а Promise * 2 — это NaN. await достаёт из обещания само число.")

POST = "async function load(id) {\n  if (id < 0) throw new Error(\"плохой id\");\n  return id * 2;\n}\n\n"
a4 = fn_task("a4-safe", "write", "Безопасная загрузка",
    "Дана async-функция `load(id)`: для отрицательного `id` она бросает ошибку, иначе возвращает `id * 2`. Напишите **async**-функцию `safeLoad(id)`: возвращает результат `load(id)`, а если случилась ошибка — строку `\"ошибка\"`.",
    "Ловить ошибки в async-коде.", "safeLoad",
    [([2], 4), ([-1], "ошибка"), ([0], 0, "Ноль — не ошибка"), ([-100], "ошибка")],
    POST + "async function safeLoad(id) {\n  try {\n    return await load(id);\n  } catch (e) {\n    return \"ошибка\";\n  }\n}\n",
    POST + "async function safeLoad(id) {\n  // ваш код\n}\n",
    [(POST + "async function safeLoad(id) {\n  return await load(id);\n}\n", "Нет try/catch: ошибка вылетает наружу."),
     (POST + "async function safeLoad(id) {\n  try {\n    return load(id);\n  } catch (e) {\n    return \"ошибка\";\n  }\n}\n", "Без await ошибка не попадает в catch: обещание отклоняется уже снаружи.")],
    hints("Ошибки ловят блоком try и catch.", "Вызов load(id) положите внутрь try.", "Перед load нужен await — иначе ошибка до catch не дойдёт.", "В catch верните строку \"ошибка\".", "try { return await load(id); } catch (e) { return \"ошибка\"; }"),
    "await превращает отказ обещания в исключение, поэтому try/catch его перехватывает; без await блок catch не сработает.")

CODE5 = 'console.log("A");\nsetTimeout(() => console.log("B"), 0);\nPromise.resolve().then(() => console.log("C"));\n(async () => {\n  console.log("D");\n  await null;\n  console.log("E");\n})();\nconsole.log("F");\n'
a5 = predict_js("a5-predict", "Порядок вывода", CODE5,
    [("A\nB\nC\nD\nE\nF", "Это порядок строк в коде, а выполнение идёт иначе."),
     ("A\nD\nF\nB\nC\nE", "Таймер выполняется после обещаний."),
     ("A\nF\nD\nC\nE\nB", "Тело async-функции работает синхронно до первого await: D раньше F.")],
    hints("Сначала выполняется весь синхронный код.", "Тело async-функции идёт синхронно до первого await.", "Затем выполняются обещания (then, продолжение после await).", "Таймеры — в самом конце.", "Порядок: A, D, F, затем C и E, затем B."),
    "Синхронно: A, D (до await), F. Потом микрозадачи: C, затем E. Последним таймер: B.")

skills = {"js.async": "Таймеры и порядок выполнения", "js.promise": "Promise", "js.await": "async/await и обработка ошибок"}
write_lesson("js-04-async", "JavaScript: асинхронность",
             "Понимать порядок выполнения кода, создавать Promise и писать async/await с обработкой ошибок.",
             list(skills), ["js-03-objects"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Забыт await перед вызовом async-функции", "fix": "Без await вместо значения получите Promise."},
              {"mistake": "try/catch без await", "fix": "Ошибка async-функции попадёт в catch только вместе с await."},
              {"mistake": "Ожидание, что setTimeout остановит программу", "fix": "Код после таймера выполняется сразу; результат придёт позже."},
              {"mistake": "await вне async-функции", "fix": "await работает только внутри функции с async."}],
             min_pass=3, pack="javascript", runner="js")
merge_js_lesson("js-04-async", skills)

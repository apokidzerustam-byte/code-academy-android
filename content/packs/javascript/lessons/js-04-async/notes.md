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

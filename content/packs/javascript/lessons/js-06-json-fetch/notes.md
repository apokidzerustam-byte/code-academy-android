# JSON, fetch и обработка ошибок

```js
const user = { name: "Аня", tags: ["js"] };
const text = JSON.stringify(user);      // объект → строка
const back = JSON.parse(text);          // строка → объект

async function getJson(url) {
  const res = await fetch(url);                         // обещание с ответом
  if (!res.ok) throw new Error("HTTP " + res.status);   // 404 — не отказ обещания!
  return res.json();                                    // тело тоже через await
}

try {
  const data = await getJson("/users/1");
} catch (e) {
  console.log("ошибка:", e.message);                    // сеть недоступна или HTTP-ошибка
}
```

| Что | Как |
|---|---|
| объект → текст | `JSON.stringify(x)` |
| текст → объект | `JSON.parse(s)` (при ошибке `SyntaxError`) |
| успех ответа | `res.ok`, `res.status` |
| несколько запросов | `await Promise.all(ids.map(load))` |
| ограничить время | `Promise.race([запрос, таймер])` |

- В JSON `undefined` и функции пропадают, даты становятся строками.
- Статус 404 не отклоняет обещание: **всегда проверяйте `ok`**.
- В этом приложении сети нет: в заданиях вместо `fetch` — учебная функция `fakeFetch`, возвращающая настоящий `Response`.

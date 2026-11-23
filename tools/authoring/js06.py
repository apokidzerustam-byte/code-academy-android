"""Урок JS 6: JSON, fetch и обработка ошибок (без сети: настоящий Response и учебный fetch)."""
from jsib import *

J1 = """const user = { name: "Аня", age: 30, tags: ["js", "web"] };
const text = JSON.stringify(user);
console.log(text);
console.log(JSON.parse(text).tags[1]);

try {
  JSON.parse("{name: 'Аня'}");
} catch (e) {
  console.log(e.name);
}
"""
J2 = """const users = { 1: { id: 1, name: "Аня" } };

async function fakeFetch(url) {
  const m = /^\\/users\\/(\\d+)$/.exec(url);
  if (m && users[m[1]]) {
    return new Response(JSON.stringify(users[m[1]]), { status: 200 });
  }
  return new Response(JSON.stringify({ error: "not found" }), { status: 404 });
}

async function main() {
  const res = await fakeFetch("/users/1");
  console.log(res.ok, res.status);
  const user = await res.json();
  console.log(user.name);
  const missing = await fakeFetch("/users/9");
  console.log(missing.ok, missing.status);
}

main();
"""
J3 = """async function fakeFetch(url) {
  if (url === "/offline") throw new TypeError("Failed to fetch");
  if (url === "/users/1") return new Response('{"name":"Аня"}', { status: 200 });
  return new Response("{}", { status: 404 });
}

async function getJson(url) {
  const res = await fakeFetch(url);
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.json();
}

async function main() {
  for (const url of ["/users/1", "/users/9", "/offline"]) {
    try {
      const data = await getJson(url);
      console.log(url, "ok", data.name);
    } catch (e) {
      console.log(url, "ошибка:", e.message);
    }
  }
}

main();
"""
J4 = """const wait = (ms, value) => new Promise((r) => setTimeout(() => r(value), ms));

function withTimeout(promise, ms) {
  const limit = new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms));
  return Promise.race([promise, limit]);
}

withTimeout(wait(10, "быстрый ответ"), 100).then(console.log);
withTimeout(wait(200, "медленный ответ"), 50).catch((e) => console.log(e.message));
"""
J5 = """const users = { 1: { name: "Аня" }, 2: { name: "Борис" } };

async function fakeFetch(url) {
  const user = users[url.split("/").pop()];
  return new Response(JSON.stringify(user), { status: user ? 200 : 404 });
}

async function getName(id) {
  const res = await fakeFetch("/users/" + id);
  return res.ok ? (await res.json()).name : "?";
}

async function main() {
  const names = await Promise.all([1, 2, 9].map(getName));
  console.log(names);
}

main();
"""
o1, o2, o3, o4, o5 = js_run(J1), js_run(J2), js_run(J3), js_run(J4), js_run(J5)
assert o1.split("\n")[1:] == ["web", "SyntaxError"], o1
assert o2.split("\n") == ["true 200", "Аня", "false 404"], o2
assert o3.split("\n")[1] == "/users/9 ошибка: HTTP 404" and o3.split("\n")[2] == "/offline ошибка: Failed to fetch", o3

use_file("main.js")
scenes = [
    scene("intro", "Приложение и сервер", """
      Почти любое приложение разговаривает с сервером: отправляет запрос и получает ответ. Ответ приходит в виде текста, чаще всего
      в формате JSON. Запрос в браузерном JavaScript делает функция fetch. Она возвращает обещание с объектом ответа, а в объекте
      есть статус и метод, который достаёт данные. В этом приложении у программ нет доступа к интернету, и это сделано нарочно ради
      безопасности. Поэтому мы будем использовать настоящий объект Response, но вместо сети подставим учебную функцию, которая
      отвечает так же, как сервер. В реальном проекте её заменит настоящий fetch, а остальной код не изменится. Приложение для заметок, магазин, погода или чат устроены одинаково: запрос, ответ, данные на экране. Такой приём, когда зависимость передают снаружи, ещё и упрощает тестирование: подставил
      заготовленные ответы и проверил все случаи, без сети и без ожидания.""",
          [NOTE("**fetch** возвращает обещание с ответом · **JSON** — текстовый формат данных · **ошибки** — часть нормальной работы", at="Запрос в браузерном")]),
    scene("json", "JSON: текст и данные", """
      JSON это способ записать данные текстом. Метод stringify превращает объект в строку, а parse делает обратное. Строка
      получается без пробелов, а ключи в ней всегда в двойных кавычках. Берём пользователя с именем, возрастом и списком тегов,
      превращаем в текст и обратно достаём второй тег. А что будет, если текст записан неверно? Например, ключ без кавычек или
      одинарные кавычки. Метод parse выбросит ошибку SyntaxError, и программа упадёт, если её не перехватить. Поэтому
      разбирать чужой текст нужно внутри try и catch. Ещё важная мелочь: значения undefined и функции в JSON пропадают, а даты
      превращаются в строки. Значит, JSON подходит для передачи данных, но не любой объект проходит через него без потерь. Сравните: объект
      в памяти программы может хранить функции и ссылки, а текст это только значения. Поэтому хорошие данные для обмена всегда простые:
      числа, строки, списки и вложенные объекты.""",
          [CLEAR(), T(J1, at="JSON это способ"), HL([2], at="Метод stringify"), HL([4], at="Берём пользователя"), HL([6, 7, 8, 9, 10], at="А что будет"),
           RUN(at="Метод parse выбросит"), OUT(o1, at="Метод parse выбросит")]),
    scene("fetch", "Ответ сервера: Response", """
      Теперь сам ответ. Объект Response хранит статус, то есть число вроде двухсот или четырёхсот четырёх, и флаг ok: он равен
      истине для успешных статусов. Тело ответа достают методом json, и он тоже возвращает обещание, поэтому перед ним нужен
      await. Наша учебная функция fakeFetch ищет пользователя и отвечает либо данными со статусом двести, либо ошибкой со статусом
      четыреста четыре. Запрашиваем существующего пользователя и получаем истину, двести и имя. Запрашиваем несуществующего и
      получаем ложь и четыреста четыре. Запускаем, и вывод совпадает с нашими словами.""",
          [CLEAR(), T(J2, at="Теперь сам ответ"), HL([14, 15], at="Тело ответа"), HL([3, 4, 5, 6, 7, 8, 9], at="Наша учебная"), HL([12, 13], at="Запрашиваем существующего"),
           HL([16, 17], at="Запрашиваем несуществующего"), RUN(at="Запускаем, и вывод"), OUT(o2, at="Запускаем, и вывод")]),
    scene("errors", "Две разные ошибки", """
      Здесь прячется самая частая ошибка новичков. Ответ с кодом четыреста четыре для fetch совсем не ошибка: обещание благополучно
      выполняется, просто статус плохой. Поэтому всегда проверяйте ok. Отдельная беда: сети нет совсем, сервер недоступен. Тогда
      обещание отклоняется исключением. Это легко упустить, потому что в тестах на хорошем интернете всё работает. Получается два вида сбоя: сервер ответил, но отказом, и сервер вообще не ответил. Функция
      getJson проверяет ok и бросает свою ошибку с понятным текстом, а вызывающий код ловит всё одним try и catch. Три запроса
      дают три разных исхода: данные, ответ с ошибкой и недоступность. Пользователю в каждом случае нужно показать свой текст:
      «не найдено» совсем не то же самое, что «проверьте соединение».""",
          [CLEAR(), T(J3, at="Здесь прячется"), HL([9], at="Поэтому всегда"), HL([2], at="Отдельная беда"), HL([7, 8, 9, 10, 11], at="Функция"),
           HL([15, 16, 17, 18, 19, 20], at="а вызывающий код"), RUN(at="Три запроса"), OUT(o3, at="Три запроса")]),
    scene("timeout", "Не ждать вечно", """
      Бывает и так, что сервер не отвечает и не отказывает: просто молчит. Пользователь не должен смотреть на крутящийся
      индикатор вечно. Для этого ставят ограничение по времени. Метод Promise race ждёт первое из нескольких обещаний. Мы
      соревнуем запрос и таймер: таймер через заданное время отклоняется ошибкой timeout. Быстрый ответ выигрывает гонку и
      возвращается как обычно, а медленный проигрывает, и мы получаем ошибку. Эту же идею вы встретите в Android: у сетевых
      запросов всегда есть время ожидания. Обычно хватает нескольких секунд, а после этого приложение предлагает повторить.""",
          [CLEAR(), T(J4, at="Бывает и так"), HL([3, 4, 5, 6], at="Метод Promise race"), HL([8], at="Быстрый ответ"), HL([9], at="а медленный"),
           RUN(at="Эту же идею"), OUT(o4, at="Эту же идею")]),
    scene("parallel", "Много запросов сразу", """
      Если нужно загрузить несколько пользователей, ждать их по одному медленно: каждый следующий запрос стартует только после
      предыдущего. Лучше запустить все сразу и дождаться вместе методом Promise all. Он принимает список обещаний и возвращает
      список результатов в том же порядке. Мы превращаем список идентификаторов в список обещаний методом map. Для третьего
      идентификатора пользователя нет, и функция getName возвращает знак вопроса. Порядок результатов совпадает с порядком
      идентификаторов, даже если запросы закончились в другое время. Не используйте для этого forEach с async внутри:
      он не дожидается обещаний. Параллельность экономит время: три запроса по секунде выполнятся за одну секунду
      вместо трёх, если сервер не возражает. Но не стоит запускать сотни запросов разом: серверы ограничивают частоту.""",
          [CLEAR(), T(J5, at="Если нужно"), HL([14], at="Мы превращаем"), HL([8, 9, 10, 11], at="Для третьего"), RUN(at="Порядок результатов"), OUT(o5, at="Порядок результатов")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: не проверить ok и разбирать тело ответа с ошибкой как обычные данные. Вторая: забыть await перед
      json и получить обещание вместо данных. Третья: не обернуть разбор JSON в try, и одно кривое сообщение роняет всю программу.
      Четвёртая: показывать пользователю только крутящийся индикатор, когда произошла ошибка, и не сообщать, что делать дальше. Хорошее сообщение об ошибке отвечает на два вопроса: что случилось и что
      пользователь может сделать, например проверить соединение или повторить позже.""",
          [NOTE("Ошибка 1: нет проверки `res.ok`.", at="Первая"), NOTE("Ошибка 2: нет `await` перед `res.json()`.", at="Вторая"),
           NOTE("Ошибка 3: `JSON.parse` без `try/catch`.", at="Третья"), NOTE("Ошибка 4: пользователь не видит причину и не знает, что делать.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. JSON превращается в текст методом stringify и обратно методом parse, а неверный текст вызывает SyntaxError.
      Ответ fetch хранит статус и флаг ok, а тело достаётся через await и json. Ошибки бывают двух видов: ответ с отказом, его
      нужно проверять самому, и отсутствие ответа, его ловит catch. Время ожидания ограничивают через Promise race, а
      несколько запросов запускают одновременно через Promise all. В заданиях вы предскажете, во что превратится JSON, научитесь
      читать данные из ответа, соберёте функцию, которая различает все виды сбоев, поправите забытый await и загрузите
      нескольких пользователей сразу.""",
          [NOTE("`JSON.stringify/parse` · `res.ok` · `await res.json()` · `try/catch` · `Promise.race` · `Promise.all`", at="Подведём итог")]),
]
use_file(None)

notes = """
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
"""

PRE = """const users = {
  1: { id: 1, name: "Аня", age: 30 },
  2: { id: 2, name: "Борис", age: 25 },
  3: { id: 3, name: "Вера", age: 41 },
};

async function fakeFetch(url) {
  if (url === "/offline") throw new TypeError("Failed to fetch");
  if (url === "/broken") return new Response("<html>oops", { status: 200 });
  if (url === "/users") return new Response(JSON.stringify(Object.values(users)), { status: 200 });
  const m = /^\\/users\\/(\\d+)$/.exec(url);
  if (m && users[m[1]]) return new Response(JSON.stringify(users[m[1]]), { status: 200 });
  return new Response(JSON.stringify({ error: "not found" }), { status: 404 });
}

"""

# --- Задание 1: предсказать ---
CODE1 = ('const data = { a: 1, b: undefined, c: [1, undefined, 3], d: new Date(0), e: "x" };\nconsole.log(JSON.stringify(data));\n'
         'console.log(JSON.parse(\'{"n":1}\').n + JSON.parse("2"));\nconsole.log(typeof JSON.parse(\'"5"\'));\n')
a1 = predict_js("a1-json", "Во что превратится JSON", CODE1,
    [('{"a":1,"b":null,"c":[1,null,3],"d":"1970-01-01T00:00:00.000Z","e":"x"}\n3\nstring', "Свойство со значением undefined в объекте пропадает целиком, а не становится null."),
     ('{"a":1,"c":[1,null,3],"d":"1970-01-01T00:00:00.000Z","e":"x"}\n12\nstring', "Оба результата parse — числа, они складываются: 1 + 2 = 3, а не склеиваются."),
     ('{"a":1,"c":[1,null,3],"d":"1970-01-01T00:00:00.000Z","e":"x"}\n3\nnumber', "Строка в кавычках внутри JSON — строка, а не число.")],
    hints("JSON — это текст: stringify превращает значения в текст по особым правилам.", "Свойство объекта со значением undefined в JSON не попадает вовсе.", "В массиве undefined превращается в null, чтобы не сдвигать позиции.",
          "Дата превращается в строку формата ISO.", "JSON.parse('2') даёт число 2, а JSON.parse('\"5\"') даёт строку «5»."),
    "stringify пропускает undefined в объектах, заменяет его на null в массивах и превращает дату в строку. parse возвращает число или строку в зависимости от записи в тексте.")

# --- Задание 2: имя пользователя ---
a2 = fn_task("a2-user-name", "write", "Имя пользователя",
    "Дана учебная функция `fakeFetch(url)` (как `fetch`: возвращает обещание с `Response`). Напишите **async**-функцию `userName(id)`: запросите `/users/` + `id`. Если ответ **не ok**, верните строку `\"не найден\"`, "
    "иначе верните поле `name` пользователя из тела ответа.",
    "Проверять ok и читать тело ответа.", "userName",
    [([1], "Аня"), ([3], "Вера"), ([99], "не найден", "Для несуществующего пользователя ответ — 404"), ([2], "Борис"), ([0], "не найден")],
    PRE + "async function userName(id) {\n  const res = await fakeFetch(\"/users/\" + id);\n  if (!res.ok) return \"не найден\";\n  const user = await res.json();\n  return user.name;\n}\n",
    PRE + "async function userName(id) {\n  // ваш код\n}\n",
    [(PRE + "async function userName(id) {\n  const res = await fakeFetch(\"/users/\" + id);\n  const user = await res.json();\n  return user.name;\n}\n", "Нет проверки ok: для 404 тело — это ошибка, и имени в нём нет."),
     (PRE + "async function userName(id) {\n  const res = await fakeFetch(\"/users/\" + id);\n  if (!res.ok) return \"не найден\";\n  return res.json();\n}\n", "Возвращается весь объект пользователя, а нужно только имя."),
     (PRE + "async function userName(id) {\n  const res = await fakeFetch(\"/users/\" + id);\n  if (!res.ok) return \"не найден\";\n  return res.name;\n}\n", "Имя лежит в теле ответа, которое читают через await res.json().")],
    hints("Сначала запросите данные: await fakeFetch(...).", "Проверьте res.ok до чтения тела.", "Если не ok — верните \"не найден\".", "Тело достают методом json, и перед ним тоже нужен await.", "return user.name после const user = await res.json()."),
    "Статус 404 не отклоняет обещание, поэтому ok проверяют сами; тело ответа — тоже обещание, и его достают через await res.json().", input_text="Идентификатор пользователя.")

# --- Задание 3: loadJson ---
LJ_SOL = ("async function loadJson(url) {\n  let res;\n  try {\n    res = await fakeFetch(url);\n  } catch (e) {\n    return { ok: false, error: \"network\" };\n  }\n"
          "  if (!res.ok) return { ok: false, error: \"HTTP \" + res.status };\n  try {\n    return { ok: true, data: await res.json() };\n  } catch (e) {\n    return { ok: false, error: \"bad json\" };\n  }\n}\n")
a3 = fn_task("a3-load-json", "write", "Загрузка с обработкой сбоев",
    "Напишите **async**-функцию `loadJson(url)`, которая **никогда не бросает ошибку**, а возвращает объект:\n\n"
    "- `{ ok: true, data }` — если ответ успешен и тело — корректный JSON;\n- `{ ok: false, error: \"HTTP 404\" }` — если ответ пришёл, но не ok (подставьте реальный статус);\n"
    "- `{ ok: false, error: \"network\" }` — если запрос не удался (обещание отклонено);\n- `{ ok: false, error: \"bad json\" }` — если тело не разбирается как JSON.",
    "Различать три вида сбоев.", "loadJson",
    [(["/users/2"], {"ok": True, "data": {"id": 2, "name": "Борис", "age": 25}}), (["/users/99"], {"ok": False, "error": "HTTP 404"}),
     (["/offline"], {"ok": False, "error": "network"}, "Сеть недоступна: fakeFetch выбрасывает исключение"), (["/broken"], {"ok": False, "error": "bad json"}, "Тело ответа — не JSON"),
     (["/nothing"], {"ok": False, "error": "HTTP 404"})],
    PRE + LJ_SOL,
    PRE + "async function loadJson(url) {\n  // ваш код\n}\n",
    [(PRE + "async function loadJson(url) {\n  const res = await fakeFetch(url);\n  if (!res.ok) return { ok: false, error: \"HTTP \" + res.status };\n  return { ok: true, data: await res.json() };\n}\n", "Нет перехвата сбоя сети и неверного JSON: ошибки вылетают наружу."),
     (PRE + "async function loadJson(url) {\n  try {\n    const res = await fakeFetch(url);\n    return { ok: true, data: await res.json() };\n  } catch (e) {\n    return { ok: false, error: \"network\" };\n  }\n}\n", "Нет проверки ok и разных текстов ошибок: 404 принимается за успех."),
     (PRE + "async function loadJson(url) {\n  try {\n    const res = await fakeFetch(url);\n    if (!res.ok) return { ok: false, error: \"HTTP \" + res.status };\n    return { ok: true, data: await res.json() };\n  } catch (e) {\n    return { ok: false, error: \"network\" };\n  }\n}\n", "Неверный JSON принимается за сбой сети: нужен отдельный результат bad json.")],
    hints("Три вида сбоев — три разных места, где может случиться ошибка.", "Запрос может быть отклонён: оберните await fakeFetch в try/catch и верните network.", "Ответ может быть не ok: проверьте res.ok и верните \"HTTP \" + res.status.",
          "Тело может не разобраться как JSON: await res.json() тоже кладут в try/catch и возвращают bad json.", "Нужны два отдельных try/catch: один вокруг запроса, второй вокруг чтения тела."),
    "Сбой запроса, плохой статус и неверное тело — три разных события, и каждое обрабатывается отдельно, чтобы вызывающий код получил понятный результат.", input_text="Адрес запроса.")

# --- Задание 4: забытый await ---
a4 = fn_task("a4-older", "fix", "Забытый await перед json",
    "Функция `olderThan(age)` должна вернуть имена пользователей **старше** `age` (строго), в порядке списка, но падает с ошибкой. Найдите причину и исправьте.",
    "Находить пропущенный await.", "olderThan",
    [([29], ["Аня", "Вера"]), ([40], ["Вера"]), ([50], [], "Старше 50 лет никого нет"), ([24], ["Аня", "Борис", "Вера"]), ([30], ["Вера"], "Строго старше: 30 не считается")],
    PRE + "async function olderThan(age) {\n  const res = await fakeFetch(\"/users\");\n  const list = await res.json();\n  return list.filter((u) => u.age > age).map((u) => u.name);\n}\n",
    PRE + "async function olderThan(age) {\n  const res = await fakeFetch(\"/users\");\n  const list = res.json();\n  return list.filter((u) => u.age > age).map((u) => u.name);\n}\n",
    [(PRE + "async function olderThan(age) {\n  const res = await fakeFetch(\"/users\");\n  const list = await res;\n  return list.filter((u) => u.age > age).map((u) => u.name);\n}\n", "await стоит перед самим ответом, а не перед json(): у Response нет метода filter."),
     (PRE + "async function olderThan(age) {\n  const res = await fakeFetch(\"/users\");\n  const list = await res.json();\n  return list.map((u) => u.name);\n}\n", "Потерян фильтр по возрасту."),
     (PRE + "async function olderThan(age) {\n  const res = await fakeFetch(\"/users\");\n  const list = await res.json();\n  return list.filter((u) => u.age >= age).map((u) => u.name);\n}\n", "Нужно строго старше: пользователь возраста age не подходит.")],
    hints("Прочитайте текст ошибки: у чего нет метода filter?", "res.json() возвращает не массив, а обещание массива.", "Обещание нужно дождаться: перед вызовом json нужен await.", "Именно перед res.json(), а не перед res.", "const list = await res.json();"),
    "Метод json возвращает обещание. Без await в list лежит Promise, а у него нет метода filter. await достаёт из обещания сам массив.", input_text="Возраст.")

# --- Задание 5: Promise.all ---
PRE5 = PRE + "async function getUser(id) {\n  const res = await fakeFetch(\"/users/\" + id);\n  return res.ok ? res.json() : null;\n}\n\n"
LM_SOL = PRE5 + "async function loadMany(ids) {\n  const list = await Promise.all(ids.map(getUser));\n  return list.map((u) => (u ? u.name : \"?\"));\n}\n"
a5 = fn_task("a5-load-many", "write", "Много пользователей сразу",
    "Дана функция `getUser(id)`: возвращает обещание с пользователем или `null`, если такого нет. Напишите **async**-функцию `loadMany(ids)`: загрузите всех пользователей из списка идентификаторов **одновременно** "
    "(через `Promise.all`) и верните массив имён **в порядке `ids`**. Для несуществующего пользователя в массив кладите `\"?\"`.",
    "Запускать запросы параллельно и сохранять порядок.", "loadMany",
    [([[1, 2]], ["Аня", "Борис"]), ([[3, 99, 1]], ["Вера", "?", "Аня"]), ([[]], [], "Пустой список"), ([[2, 2]], ["Борис", "Борис"]), ([[99]], ["?"])],
    LM_SOL, PRE5 + "async function loadMany(ids) {\n  // ваш код\n}\n",
    [(PRE5 + "async function loadMany(ids) {\n  const names = [];\n  ids.forEach(async (id) => {\n    const u = await getUser(id);\n    names.push(u ? u.name : \"?\");\n  });\n  return names;\n}\n", "forEach не дожидается async-функций: массив возвращается пустым."),
     (PRE5 + "async function loadMany(ids) {\n  return ids.map(async (id) => {\n    const u = await getUser(id);\n    return u ? u.name : \"?\";\n  });\n}\n", "Возвращается список обещаний: нет Promise.all."),
     (PRE5 + "async function loadMany(ids) {\n  const list = await Promise.all(ids.map(getUser));\n  return list.filter(Boolean).map((u) => u.name);\n}\n", "Несуществующие пользователи теряются, а нужен знак вопроса.")],
    hints("Сначала превратите список идентификаторов в список обещаний: ids.map(getUser).", "Дождитесь всех сразу: await Promise.all(...).", "Promise.all сохраняет порядок: результат на i-м месте соответствует i-му идентификатору.",
          "Для null в результате нужен знак вопроса, иначе имя.", "list.map((u) => (u ? u.name : \"?\"))"),
    "Promise.all запускает запросы одновременно и возвращает результаты в порядке исходного списка. forEach с async внутри не дожидается обещаний.", input_text="Список идентификаторов.")

skills = {"js.json": "JSON: stringify и parse", "js.fetch": "Ответ сервера: Response, ok, json", "js.errors": "Сбои запросов, таймаут, Promise.all"}
write_lesson("js-06-json-fetch", "JavaScript: JSON, fetch и ошибки",
             "Работать с JSON и ответами сервера, различать виды сбоев и запускать несколько запросов сразу.",
             list(skills), ["js-05-dom"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Не проверяют res.ok", "fix": "Статус 404 не отклоняет обещание: проверяйте ok сами."},
              {"mistake": "Нет await перед res.json()", "fix": "json возвращает обещание: без await вместо данных будет Promise."},
              {"mistake": "JSON.parse без try/catch", "fix": "Неверный текст вызывает SyntaxError: ловите его."},
              {"mistake": "forEach с async внутри", "fix": "Для нескольких запросов используйте Promise.all(ids.map(...))."}],
             min_pass=4, pack="javascript", runner="js")
merge_js_lesson("js-06-json-fetch", skills)

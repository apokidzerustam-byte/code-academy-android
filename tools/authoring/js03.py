"""Урок JS 3: объекты, деструктуризация и JSON."""
from jsib import *

J1 = """const user = { name: "Аня", age: 25, skills: ["js", "sql"] };
user.city = "Краков";
console.log(user.name, user["age"]);
console.log(Object.keys(user));
console.log(user.skills.length);
delete user.age;
console.log("age" in user);
"""
J2 = """const base = { theme: "light", size: 12 };
const custom = { ...base, size: 16, lang: "ru" };
const { theme, size } = custom;
console.log(JSON.stringify(custom));
console.log(theme, size);
"""
J3 = """const stock = { яблоки: 3, груши: 0, сливы: 7 };
for (const [name, n] of Object.entries(stock)) {
  console.log(name, n > 0 ? "есть" : "нет");
}
"""
J4 = """const text = JSON.stringify({ id: 1, tags: ["a", "b"] });
console.log(text);
const back = JSON.parse(text);
console.log(back.tags[1]);
try {
  JSON.parse("{oops");
} catch (e) {
  console.log("Ошибка:", e.name);
}
"""
o1, o2, o3, o4 = js_run(J1), js_run(J2), js_run(J3), js_run(J4)

use_file("main.js")
scenes = [
    scene("intro", "Объект: данные с названиями", """
      Массив хранит значения по номерам. А если нужно описать вещь с названными свойствами: пользователя с именем, возрастом
      и навыками? Для этого есть объект. Это набор пар «ключ и значение» в фигурных скобках. Почти все данные в программах
      и в интернете устроены как объекты и массивы объектов.""",
          [NOTE("Объект — набор пар **ключ: значение**. Читаем `user.name` или `user[\"name\"]`.", at="Это набор")]),
    scene("basic", "Читаем и меняем объект", """
      Создадим пользователя. К свойству обращаются через точку или через квадратные скобки с именем в кавычках. Новое свойство
      появляется простым присваиванием. Функция Object точка keys возвращает массив имён свойств. Слово delete удаляет
      свойство, а оператор in проверяет, есть ли оно. Запускаем.""",
          [CLEAR(), T(J1, at="Создадим"), HL([3], at="через точку"), HL([2], at="Новое свойство"), HL([4], at="Object"), HL([6], at="Слово delete"), HL([7], at="оператор in"),
           RUN(at="Запускаем"), OUT(o1, at="Запускаем")]),
    scene("spread", "Копирование и деструктуризация", """
      Три точки раскрывают содержимое объекта. Так делают копию с изменениями: сначала раскрываем базовые настройки, затем
      перекрываем размер и добавляем язык. Правое значение побеждает. Это не меняет исходный объект. А деструктуризация
      достаёт сразу несколько свойств в отдельные переменные: тема и размер. Запускаем.""",
          [CLEAR(), T(J2, at="Три точки"), HL([2], at="Так делают"), HL([3], at="деструктуризация"), RUN(at="Запускаем"), OUT(o2, at="Запускаем")]),
    scene("entries", "Обход объекта", """
      Чтобы пройтись по объекту, используют Object точка entries: он возвращает массив пар из имени и значения. Цикл for of сразу
      раскладывает каждую пару на две переменные. Посмотрим остатки на складе: если число больше нуля, фрукт есть. Запускаем.""",
          [CLEAR(), T(J3, at="Чтобы пройтись"), HL([2], at="Цикл"), HL([3], at="если число"), RUN(at="Запускаем"), OUT(o3, at="Запускаем")]),
    scene("json", "JSON: обмен данными", """
      Чтобы сохранить данные или передать их другой программе, объект превращают в текст формата JSON. Функция stringify
      делает текст, а parse возвращает объект обратно. Если текст не является корректным JSON, parse бросает исключение,
      и поймать его нужно блоком try и catch. Без этого программа упала бы. Запускаем.""",
          [CLEAR(), T(J4, at="Чтобы сохранить"), HL([1], at="Функция stringify"), HL([3], at="parse"), HL([5, 6, 7, 8], at="поймать"), RUN(at="Запускаем"), OUT(o4, at="Запускаем")]),
    scene("summary", "Итог", """
      Подведём итог. Объект хранит пары ключ и значение. Свойства читают через точку, перебирают через Object entries, копируют
      через три точки. Деструктуризация достаёт нужные поля. JSON превращает объекты в текст и обратно, а ошибки разбора
      ловят через try и catch.""",
          [NOTE("`obj.key` · `Object.keys/values/entries` · `{ ...a, ...b }` · `JSON.stringify/parse` · `try/catch`", at="Подведём")]),
]
use_file(None)

notes = """
# JavaScript: объекты и JSON

```js
const user = { name: "Аня", age: 25, skills: ["js", "sql"] };
user.name;  user["age"];  user.city = "Краков";
Object.keys(user);  Object.values(user);  Object.entries(user);
delete user.age;  "age" in user;

const custom = { ...base, size: 16 };      // копия с изменениями (правое побеждает)
const { theme, size } = custom;            // достать поля

for (const [key, value] of Object.entries(obj)) { … }

const text = JSON.stringify(obj);          // объект → текст
const back = JSON.parse(text);             // текст → объект
try { JSON.parse(bad); } catch (e) { … }   // ошибка разбора
```

- Ключ — строка; значение — что угодно (число, массив, другой объект).
- `{ ...a, ...b }` — свойства `b` перекрывают одноимённые из `a`.
- `Object.keys(obj)` — массив имён; `Object.values(obj)` — массив значений.
- `JSON.parse` на неверном тексте бросает `SyntaxError`.
"""

a1 = fn_task("a1-count-words", "write", "Частота слов",
    "Напишите функцию `countWords(text)`: **возвращает** объект, где ключ — слово (в нижнем регистре), значение — сколько раз оно встретилось. Слова разделены пробелами (возможно, несколькими). Для пустой строки — пустой объект.",
    "Собирать счётчики в объекте.", "countWords",
    [(["a b a"], {"a": 2, "b": 1}), (["Да да нет"], {"да": 2, "нет": 1}), ([""], {}, "Пустая строка"), (["  x   x "], {"x": 2}, "Лишние пробелы")],
    "function countWords(text) {\n  const counts = {};\n  for (const w of text.toLowerCase().split(/\\s+/)) {\n    if (w === \"\") continue;\n    counts[w] = (counts[w] || 0) + 1;\n  }\n  return counts;\n}\n",
    "function countWords(text) {\n  // ваш код\n}\n",
    [("function countWords(text) {\n  const counts = {};\n  for (const w of text.split(/\\s+/)) {\n    if (w === \"\") continue;\n    counts[w] = (counts[w] || 0) + 1;\n  }\n  return counts;\n}\n", "Регистр не учтён: «Да» и «да» разные."),
     ("function countWords(text) {\n  const counts = {};\n  for (const w of text.toLowerCase().split(\" \")) {\n    counts[w] = (counts[w] || 0) + 1;\n  }\n  return counts;\n}\n", "Лишние пробелы дают слово «пусто»."),
     ("function countWords(text) {\n  const counts = {};\n  for (const w of text.toLowerCase().split(/\\s+/)) {\n    if (w === \"\") continue;\n    counts[w] = 1;\n  }\n  return counts;\n}\n", "Счётчик не увеличивается.")],
    hints("Заведите пустой объект для счётчиков.", "Разрежьте строку на слова: toLowerCase() и split(/\\s+/).", "Пустые «слова» от лишних пробелов пропустите.", "Для каждого слова: счётчик = прежний счётчик (или 0) плюс один.", "counts[w] = (counts[w] || 0) + 1;"),
    "Для каждого слова увеличиваем счётчик: (counts[w] || 0) + 1 даёт единицу при первой встрече.", expected_text="Объект со счётчиками.")

a2 = fn_task("a2-merge", "write", "Настройки по умолчанию",
    "Напишите функцию `withDefaults(options)`: **возвращает** новый объект настроек. По умолчанию `{ theme: \"light\", size: 12 }`, а значения из `options` их **перекрывают**; новые ключи из `options` тоже попадают в результат.",
    "Объединять объекты через spread.", "withDefaults",
    [([{}], {"theme": "light", "size": 12}), ([{"size": 16}], {"theme": "light", "size": 16}), ([{"theme": "dark", "lang": "ru"}], {"theme": "dark", "size": 12, "lang": "ru"}, "Новые ключи сохраняются")],
    "function withDefaults(options) {\n  return { theme: \"light\", size: 12, ...options };\n}\n",
    "function withDefaults(options) {\n  // ваш код\n}\n",
    [("function withDefaults(options) {\n  return { ...options, theme: \"light\", size: 12 };\n}\n", "Значения по умолчанию перекрывают настройки пользователя."),
     ("function withDefaults(options) {\n  return options;\n}\n", "Значения по умолчанию потеряны."),
     ("function withDefaults(options) {\n  return { theme: \"light\", size: 12 };\n}\n", "Настройки пользователя игнорируются.")],
    hints("Нужен новый объект из двух частей.", "Три точки раскрывают объект внутри фигурных скобок.", "Правое значение перекрывает левое.", "Сначала значения по умолчанию, потом options.", "{ theme: \"light\", size: 12, ...options }"),
    "Порядок важен: сначала значения по умолчанию, затем ...options — они перекроют одноимённые ключи.", expected_text="Новый объект настроек.")

a3 = fn_task("a3-total-stock", "fix", "Остатки на складе",
    "Функция `totalStock(stock)` должна вернуть **сумму значений** объекта (`{ яблоки: 3, груши: 0 }` → `3`), но возвращает странную строку. Найдите ошибку.",
    "Отличать ключи от значений.", "totalStock",
    [([{"яблоки": 3, "груши": 0}], 3), ([{"a": 1, "b": 2, "c": 3}], 6), ([{}], 0), ([{"x": 10}], 10)],
    "function totalStock(stock) {\n  let sum = 0;\n  for (const key of Object.keys(stock)) {\n    sum += stock[key];\n  }\n  return sum;\n}\n",
    "function totalStock(stock) {\n  let sum = 0;\n  for (const key of Object.keys(stock)) {\n    sum += key;\n  }\n  return sum;\n}\n",
    [("function totalStock(stock) {\n  return Object.keys(stock).length;\n}\n", "Считается число ключей, а не сумма значений."),
     ("function totalStock(stock) {\n  let sum = 0;\n  for (const key of Object.keys(stock)) {\n    sum += stock.key;\n  }\n  return sum;\n}\n", "stock.key ищет свойство с именем key; нужны квадратные скобки.")],
    hints("Вызовите totalStock({ a: 1 }) и посмотрите на результат.", "Что хранит переменная key: имя свойства или его значение?", "К сумме прибавляется имя, а не число.", "Значение по имени из переменной берут через квадратные скобки.", "sum += stock[key];"),
    "Object.keys даёт имена свойств. Чтобы получить значение по имени из переменной, нужны квадратные скобки: stock[key].")

a4 = fn_task("a4-describe", "write", "Пользователь из JSON",
    "Напишите функцию `describeUser(json)`: получает **текст JSON** вида `{\"name\":\"Аня\",\"age\":25}` и **возвращает** строку `Аня (25)`. Если текст — не корректный JSON, вернуть строку `ошибка`.",
    "Разбирать JSON и ловить ошибки.", "describeUser",
    [(["{\"name\":\"Аня\",\"age\":25}"], "Аня (25)"), (["{oops"], "ошибка"), (["{\"name\":\"Ли\",\"age\":7}"], "Ли (7)", "Подставляются любые значения"), ([""], "ошибка", "Пустой текст — тоже ошибка")],
    "function describeUser(json) {\n  try {\n    const { name, age } = JSON.parse(json);\n    return `${name} (${age})`;\n  } catch (e) {\n    return \"ошибка\";\n  }\n}\n",
    "function describeUser(json) {\n  // ваш код\n}\n",
    [("function describeUser(json) {\n  const { name, age } = JSON.parse(json);\n  return `${name} (${age})`;\n}\n", "Нет try/catch: на неверном JSON функция падает."),
     ("function describeUser(json) {\n  try {\n    const { name, age } = JSON.parse(json);\n    return name + age;\n  } catch (e) {\n    return \"ошибка\";\n  }\n}\n", "Строка собрана неверно: нет скобок и пробела.")],
    hints("Текст в объект превращает JSON.parse.", "На неверном тексте parse бросает ошибку — её нужно перехватить.", "Оберните разбор в try, а в catch верните \"ошибка\".", "Достаньте поля: const { name, age } = …", "Строка: `${name} (${age})`."),
    "try ловит исключение от JSON.parse, а деструктуризация достаёт name и age для шаблонной строки.", input_text="Строка с JSON.")

CODE5 = 'const a = { x: 1, y: 2 };\nconst b = { ...a, y: 20, z: 30 };\nconst { x, ...rest } = b;\nconsole.log(JSON.stringify(a));\nconsole.log(JSON.stringify(b));\nconsole.log(x, JSON.stringify(rest));\nconsole.log(Object.keys(b).length);\n'
a5 = predict_js("a5-predict", "Копии объектов", CODE5,
    [('{"x":1,"y":20}\n{"x":1,"y":20,"z":30}\n1 {"y":20,"z":30}\n3', "Исходный объект a при копировании не меняется: y в нём остаётся 2."),
     ('{"x":1,"y":2}\n{"x":1,"y":20,"z":30}\n1 {"x":1,"y":20,"z":30}\n3', "Остаток rest не включает x: его уже достали."),
     ('{"x":1,"y":2}\n{"x":1,"y":2,"z":30}\n1 {"y":2,"z":30}\n3', "Правое значение побеждает: y в b равно 20.")],
    hints("Копия b не меняет объект a.", "В b свойство y перекрыто значением 20 и добавлено z.", "Деструктуризация достаёт x, остальное собирается в rest.", "rest содержит все свойства кроме x.", "В b три ключа: x, y, z."),
    "a остаётся прежним; b = {x:1, y:20, z:30}; x достаётся отдельно, rest = {y:20, z:30}; ключей три.")

skills = {"js.objects": "Объекты: свойства и методы Object", "js.spread": "Spread и деструктуризация", "js.json": "JSON и обработка ошибок разбора"}
write_lesson("js-03-objects", "JavaScript: объекты и JSON",
             "Описывать данные объектами, копировать их через spread, обходить через Object.entries и работать с JSON.",
             list(skills), ["js-02-arrays"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Имя из переменной читают через точку", "fix": "obj[name], а не obj.name — точка ищет свойство с буквальным именем."},
              {"mistake": "Порядок в { ...a, ...b } перепутан", "fix": "Правое значение побеждает: сначала умолчания, потом пользовательские."},
              {"mistake": "JSON.parse без try/catch", "fix": "Неверный текст бросает SyntaxError — ловите его.", "errorType": "SyntaxError"},
              {"mistake": "Object.keys вместо Object.values", "fix": "keys — имена, values — значения, entries — пары."}],
             min_pass=3, pack="javascript", runner="js")
merge_js_lesson("js-03-objects", skills)

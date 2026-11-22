"""Урок веб 2: JavaScript — переменные, функции, условия, циклы, страница и события.
Весь вывод в сценах — настоящий запуск тем же веб-раннером, что в приложении."""
from mk import *

J1 = """let name = "Аня";
const year = 2026;
console.log("Привет,", name);
console.log(`Сейчас ${year} год`);
"""
J2 = """function square(x) {
  return x * x;
}

console.log(square(4));
console.log(square(1.5));
"""
J3 = """const scores = [72, 95, 58, 81];
let passed = 0;
for (const s of scores) {
  if (s >= 60) {
    passed++;
  }
}
console.log("Сдали:", passed, "из", scores.length);
"""
JERR = """let total = 10;
console.log(totl * 2);
"""
JLOOP = """let i = 0;
while (i < 5) {
  console.log(i);
}
"""
PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Счётчик</title>
</head>
<body>
  <p>Нажатий: <span id="count">0</span></p>
  <button id="btn">Нажми</button>
  <script>
    const btn = document.getElementById("btn");
    const count = document.getElementById("count");
    let n = 0;
    btn.addEventListener("click", () => {
      n++;
      count.textContent = n;
      console.log("клик", n);
    });
  </script>
</body>
</html>
"""


def out(code):
    r = web_out("js", code)
    return r["stdout"], r["stderr"], r["status"]


o1, e1, _ = out(J1); assert not e1
o2, e2, _ = out(J2); assert not e2
o3, e3, _ = out(J3); assert not e3
_, eerr, serr = out(JERR); assert "totl" in eerr, eerr
oloop, eloop, sloop = out(JLOOP); assert "InfiniteLoopError" in eloop or "цикл" in eloop.lower(), (eloop, sloop)
# Нажатия по-настоящему: проверка нажимает кнопку дважды и читает счётчик.
clicked = web_check("html", PAGE, {"kind": "web", "lang": "html", "cases": [
    {"id": "c", "before": "document.getElementById('btn').click(); document.getElementById('btn').click()",
     "expr": "document.getElementById('count').textContent", "expected": "2"}]})
assert clicked["allPassed"], clicked
loop_shown = oloop.strip().split("\n")[:3]
loop_text = "\n".join(loop_shown) + "\n…\n" + eloop

use_file("main.js")
scenes = [
    scene("intro", "Язык браузера", """
      JavaScript — язык, который понимает каждый браузер. Он оживляет страницы: реагирует на нажатия, меняет
      текст, проверяет формы. Сегодня сначала потренируемся в консоли, как с Питоном, а в конце подключим код
      к странице. Код выполняется во встроенном браузере приложения, без доступа к интернету.""",
          [NOTE("JavaScript работает в браузере. Вывод в консоль — `console.log(...)`.", at="JavaScript")]),
    scene("vars", "Переменные и вывод", """
      Переменную объявляют словом let, если значение будет меняться, или const, если не будет. Строки пишут
      в кавычках, а в конце строки ставят точку с запятой. Вывод — console точка log, через запятую можно
      передать несколько значений. Ещё удобная запись — шаблонная строка в обратных кавычках: внутри доллар
      и фигурные скобки подставляют значение. Запускаем.""",
          [CLEAR(), T(J1, at="Переменную"), HL([1], at="Переменную"), HL([2], at="или const"), HL([3], at="Вывод"),
           HL([4], at="шаблонная строка"), RUN(at="Запускаем"), OUT(o1, at="Запускаем")]),
    scene("func", "Функции", """
      Функцию объявляют словом function, затем имя, параметры в скобках и тело в фигурных скобках. return
      возвращает результат. В заданиях проверка вызывает вашу функцию с разными аргументами и сравнивает
      ответ, поэтому важно именно вернуть значение, а не напечатать. Запустим: шестнадцать и две целых двадцать пять.""",
          [CLEAR(), T(J2, at="Функцию"), HL([1, 2, 3], at="Функцию"), HL([2], at="return"), RUN(at="Запустим"),
           OUT(o2, at="Запустим")]),
    scene("loop", "Массив, цикл и условие", """
      Массив — список значений в квадратных скобках. Цикл for of проходит по каждому элементу. Условие if
      пишут в круглых скобках, а тело — в фигурных. Знак плюс плюс увеличивает число на один. Посчитаем, сколько
      оценок не ниже шестидесяти. Запускаем.""",
          [CLEAR(), T(J3, at="Массив"), HL([1], at="Массив"), HL([3], at="Цикл"), HL([4, 5, 6], at="Условие if"),
           RUN(at="Запускаем"), OUT(o3, at="Запускаем")]),
    scene("errors", "Ошибки", """
      Ошибёмся в имени переменной. Запускаем. Ошибка ReferenceError: имя не определено, и приложение показывает
      номер строки. Читайте сообщение целиком: оно почти всегда указывает, где искать.""",
          [CLEAR(), T(JERR, at="Ошибёмся"), RUN(at="Запускаем"), OUT(eerr, err=True, at="Ошибка"), HL([2], at="номер строки")]),
    scene("infinite", "Бесконечный цикл", """
      А теперь классическая ошибка: забыли увеличить счётчик в цикле while, и условие никогда не станет ложным.
      Такой код повесил бы обычную страницу. Приложение следит за циклами и через две секунды останавливает
      программу с понятным сообщением. Кнопка «Стоп» тоже всегда работает.""",
          [CLEAR(), T(JLOOP, at="забыли"), HL([2, 3, 4], at="забыли"), RUN(at="Приложение следит"),
           OUT(loop_text, err=True, at="через две секунды")]),
    scene("dom", "Код на странице", """
      Теперь подключим код к странице. Скрипт пишут в теге script в конце body. document точка getElementById
      находит элемент по id. addEventListener подписывается на событие: при каждом нажатии кнопки увеличиваем
      счётчик и записываем его в textContent — текст элемента. В заданиях проверка сама нажимает кнопки и
      читает, что получилось на странице.""",
          [CLEAR(file="index.html"), T(PAGE, at="Теперь подключим", file="index.html"), HL([10, 19], at="Скрипт", file="index.html"),
           HL([11, 12], at="getElementById", file="index.html"), HL([14, 15, 16, 17, 18], at="addEventListener", file="index.html"),
           NOTE("Нашли элемент → подписались на событие → изменили текст: `el.textContent = …`.", at="В заданиях")]),
    scene("summary", "Итоги", """
      Итак: let и const для переменных, console точка log для вывода, function и return для функций, for of
      и if для обхода и условий. На странице — getElementById, addEventListener и textContent. Переходите к заданиям.""",
          [NOTE("`let`/`const` · `console.log` · `function … return` · `for (const x of arr)` · `addEventListener`", at="Итак")]),
]

notes = """
# JavaScript: первые шаги

## Переменные и вывод
```js
let n = 1;          // можно менять
const year = 2026;  // нельзя переназначить
console.log("n =", n, `год ${year}`);
```

## Функции
```js
function square(x) {
  return x * x;      // вернуть, а не напечатать
}
const half = (x) => x / 2;   // стрелочная функция
```

## Условия и циклы
```js
if (s >= 60) { … } else { … }
for (const s of scores) { … }        // по элементам массива
for (let i = 0; i < 5; i++) { … }    // со счётчиком
```
Сравнение — `===` (строго: `"2" === 2` ложно). `"2" + 2` даёт строку `"22"`.

## Страница
```js
const btn = document.getElementById("btn");
btn.addEventListener("click", () => {
  document.getElementById("count").textContent = "…";
});
```

## Частые ошибки
- Опечатка в имени → `ReferenceError: … is not defined`.
- Функция печатает, а нужно `return`.
- Бесконечный цикл: забыли изменить счётчик. Приложение остановит его через 2 секунды.
- `=` вместо `===` в условии.
"""

# --- Задание 1: функция-приветствие ---------------------------------------------
S1 = "function greet(name) {\n  return `Привет, ${name}!`;\n}\n"
t1 = {"kind": "web", "lang": "js", "cases": [
    {"id": "v1", "function": "greet", "args": ["Аня"], "expected": "Привет, Аня!"},
    {"id": "v2", "function": "greet", "args": ["мир"], "expected": "Привет, мир!"},
    {"id": "h1", "hidden": True, "function": "greet", "args": ["Ли"], "expected": "Привет, Ли!",
     "hint": "Имя подставляется любое"},
    {"id": "h2", "hidden": True, "function": "greet", "args": [""], "expected": "Привет, !",
     "hint": "Пустое имя тоже подставляется как есть"},
]}
a1 = asg("a1-greet", "write", "Функция приветствия",
         "Напишите функцию `greet(name)`, которая **возвращает** строку `Привет, <имя>!`.\n\n"
         "Например, `greet(\"Аня\")` возвращает `Привет, Аня!`.",
         "Писать функцию с параметром и return.", "Аргумент name — строка.", "Строка-приветствие.",
         ["Функция должна вернуть значение (return), печатать не нужно."],
         hints("Объявите function greet(name) { … }.",
               "Результат отдаётся словом return.",
               "Строку удобно собрать шаблоном в обратных кавычках.",
               "Внутри шаблона имя подставляется так: ${name}.",
               "function greet(name) {\n  return `Привет, ${name}!`;\n}"),
         t1, S1, "return отдаёт строку тому, кто вызвал функцию; шаблон подставляет имя.",
         ["Возвращает строку для любого имени."],
         [("function greet(name) {\n  console.log(`Привет, ${name}!`);\n}\n", "Функция печатает, но ничего не возвращает."),
          ("function greet(name) {\n  return \"Привет, Аня!\";\n}\n", "Ответ «зашит» под пример."),
          ("function greet(name) {\n  return `Привет, ${name}`;\n}\n", "Потерян восклицательный знак."),
          ("function hello(name) {\n  return `Привет, ${name}!`;\n}\n", "Функция должна называться greet.")],
         starter="function greet(name) {\n  // ваш код\n}\n")

# --- Задание 2: максимум в массиве ---------------------------------------------------
S2 = "function maxOf(numbers) {\n  let best = numbers[0];\n  for (const x of numbers) {\n    if (x > best) {\n      best = x;\n    }\n  }\n  return best;\n}\n"
t2 = {"kind": "web", "lang": "js", "cases": [
    {"id": "v1", "function": "maxOf", "args": [[3, 9, 4]], "expected": 9},
    {"id": "v2", "function": "maxOf", "args": [[10, 2]], "expected": 10},
    {"id": "h1", "hidden": True, "function": "maxOf", "args": [[-5, -2, -9]], "expected": -2,
     "hint": "Все числа могут быть отрицательными — не начинайте поиск с нуля"},
    {"id": "h2", "hidden": True, "function": "maxOf", "args": [[7]], "expected": 7, "hint": "Массив из одного числа"},
    {"id": "h3", "hidden": True, "function": "maxOf", "args": [[1, 5, 5, 2]], "expected": 5},
]}
a2 = asg("a2-max", "write", "Самое большое число",
         "Напишите функцию `maxOf(numbers)`: она получает непустой массив чисел и **возвращает** наибольшее из них.\n\n"
         "Пример: `maxOf([3, 9, 4])` → `9`.",
         "Обходить массив циклом и запоминать лучшее значение.", "Непустой массив чисел.", "Наибольшее число.",
         ["Числа могут быть отрицательными.", "Math.max тоже можно, но попробуйте циклом."],
         hints("Заведите переменную для лучшего найденного числа.",
               "Начните с первого элемента массива, а не с нуля.",
               "Пройдите по всем элементам циклом for of.",
               "Если элемент больше лучшего — запомните его.",
               "let best = numbers[0];\nfor (const x of numbers) { if (x > best) best = x; }\nreturn best;"),
         t2, S2, "best начинается с первого элемента; цикл заменяет его каждым большим числом.",
         ["Работает с отрицательными числами.", "Работает с массивом из одного числа."],
         [("function maxOf(numbers) {\n  let best = 0;\n  for (const x of numbers) {\n    if (x > best) best = x;\n  }\n  return best;\n}\n",
           "Начальное значение 0 ломает случай, когда все числа отрицательные."),
          ("function maxOf(numbers) {\n  return numbers[numbers.length - 1];\n}\n", "Последний элемент — не обязательно наибольший."),
          ("function maxOf(numbers) {\n  let best = numbers[0];\n  for (const x of numbers) {\n    if (x < best) best = x;\n  }\n  return best;\n}\n",
           "Знак сравнения наоборот: ищется минимум.")],
         starter="function maxOf(numbers) {\n  // ваш код\n}\n")

# --- Задание 3: исправить ошибку на единицу ------------------------------------------------
STARTER3 = "// Должна вернуть сумму 1 + 2 + … + n\nfunction sumTo(n) {\n  let s = 0;\n  for (let i = 1; i < n; i++) {\n    s += i;\n  }\n  return s;\n}\n"
S3 = STARTER3.replace("i < n", "i <= n")
t3 = {"kind": "web", "lang": "js", "cases": [
    {"id": "v1", "function": "sumTo", "args": [3], "expected": 6},
    {"id": "v2", "function": "sumTo", "args": [1], "expected": 1},
    {"id": "h1", "hidden": True, "function": "sumTo", "args": [100], "expected": 5050},
    {"id": "h2", "hidden": True, "function": "sumTo", "args": [0], "expected": 0, "hint": "Для n = 0 сумма пустая — 0"},
]}
a3 = asg("a3-fix", "fix", "Не хватает последнего",
         "Функция `sumTo(n)` должна возвращать сумму `1 + 2 + … + n`, но для `sumTo(3)` выдаёт `3` вместо `6`. Исправьте.",
         "Находить ошибку «на единицу» в границе цикла.", "Целое n ≥ 0.", "Сумма от 1 до n.",
         ["Исправьте ошибку, а не подгоняйте ответ."],
         hints("Вызовите sumTo(3) и посчитайте вручную, какие i проходит цикл.",
               "Цикл проходит i = 1 и 2. А 3?",
               "Посмотрите на условие продолжения цикла.",
               "Число n тоже должно войти в сумму: нужно «меньше или равно».",
               "for (let i = 1; i <= n; i++)"),
         t3, S3, "Условие i < n останавливает цикл до n, поэтому последнее слагаемое терялось. i <= n включает его.",
         ["Сумма верна для любого n."],
         [(STARTER3.replace("let i = 1", "let i = 0"), "Начало с 0 ничего не меняет: по-прежнему нет n."),
          (STARTER3.replace("return s;", "return s + 1;"), "Подгонка: верно только для отдельных n."),
          (STARTER3.replace("i < n", "i <= n").replace("let s = 0", "let s = 1"), "Сумма начинается не с нуля — лишняя единица.")],
         starter=STARTER3)

# --- Задание 4: кнопка и счётчик на странице -------------------------------------------------
P4_HEAD = '<!DOCTYPE html>\n<html lang="ru">\n<head>\n  <meta charset="utf-8">\n  <title>Лайки</title>\n</head>\n<body>\n  <button id="like">Нравится</button>\n  <p>Лайков: <span id="likes">0</span></p>\n'
P4_TAIL = "</body>\n</html>\n"
S4 = P4_HEAD + '  <script>\n    let likes = 0;\n    document.getElementById("like").addEventListener("click", () => {\n      likes++;\n      document.getElementById("likes").textContent = likes;\n    });\n  </script>\n' + P4_TAIL
CLICK = "document.getElementById('like').click();"
t4 = {"kind": "web", "lang": "html", "cases": [
    {"id": "start", "expr": "document.getElementById('likes').textContent.trim()", "expected": "0"},
    {"id": "one", "before": CLICK, "expr": "document.getElementById('likes').textContent.trim()", "expected": "1"},
    {"id": "three", "before": CLICK * 3, "expr": "document.getElementById('likes').textContent.trim()", "expected": "3"},
    {"id": "h1", "hidden": True, "before": CLICK * 7, "expr": "document.getElementById('likes').textContent.trim()", "expected": "7",
     "hint": "Каждое нажатие — плюс один"},
]}
a4 = asg("a4-likes", "write", "Кнопка «Нравится»",
         "На странице есть кнопка `id=\"like\"` и счётчик `<span id=\"likes\">0</span>`. Допишите скрипт: "
         "каждое нажатие кнопки увеличивает число в счётчике на 1.\n\nНажмите «Запустить» и попробуйте кнопку в предпросмотре.",
         "Находить элементы страницы и реагировать на нажатие.", "Страница с кнопкой и счётчиком.",
         "После N нажатий в счётчике число N.", ["Разметку не меняйте — только скрипт."],
         hints("Сначала найдите кнопку: document.getElementById(\"like\").",
               "Подпишитесь на нажатие: addEventListener(\"click\", () => { … }).",
               "Храните число в переменной let снаружи обработчика.",
               "Внутри обработчика увеличьте число и запишите его в textContent счётчика.",
               "let likes = 0;\ndocument.getElementById(\"like\").addEventListener(\"click\", () => {\n  likes++;\n  document.getElementById(\"likes\").textContent = likes;\n});"),
         t4, S4, "Переменная likes живёт между нажатиями; обработчик click увеличивает её и показывает в span.",
         ["Счётчик растёт на 1 за нажатие.", "До нажатий показан 0."],
         [(P4_HEAD + '  <script>\n    document.getElementById("like").addEventListener("click", () => {\n      let likes = 0;\n      likes++;\n      document.getElementById("likes").textContent = likes;\n    });\n  </script>\n' + P4_TAIL,
           "Переменная создаётся заново при каждом нажатии — счётчик всегда 1."),
          (P4_HEAD + '  <script>\n    let likes = 0;\n    document.getElementById("like").addEventListener("click", () => {\n      likes++;\n      console.log(likes);\n    });\n  </script>\n' + P4_TAIL,
           "Число печатается в консоль, но на странице не меняется."),
          (P4_HEAD + '  <script>\n    let likes = 0;\n    document.getElementById("likes").addEventListener("click", () => {\n      likes++;\n      document.getElementById("likes").textContent = likes;\n    });\n  </script>\n' + P4_TAIL,
           "Обработчик повешен на счётчик, а не на кнопку.")],
         starter=P4_HEAD + "  <script>\n    // ваш код\n  </script>\n" + P4_TAIL)

# --- Задание 5: предсказать вывод -------------------------------------------------------------
CODE5 = 'console.log("2" + 2);\nconsole.log(2 + 2);\nconsole.log("5" - 2);\n'
ans5 = web_out("js", CODE5)["stdout"].strip()
assert ans5 == "22\n4\n3", ans5
a5 = asg("a5-predict", "predict", "Строки и числа",
         "Что напечатает программа? Каждая строка вывода — с новой строки.",
         "Понимать сложение строк и чисел в JavaScript.", "—", "Три строки.", [],
         hints("Если хотя бы одно слагаемое — строка, плюс склеивает строки.",
               "\"2\" + 2 — это склейка.",
               "2 + 2 — обычные числа.",
               "Минус для строк не определён, поэтому JavaScript превращает строку в число.",
               "Ответ: 22, 4 и 3 — каждое с новой строки."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "\"2\" + 2 склеивает строки → 22; 2 + 2 = 4; \"5\" - 2: минус переводит строку в число → 3.",
         ["Все три строки верны."],
         [("4\n4\n3", "Плюс со строкой склеивает, а не складывает."),
          ("22\n4\n52", "Минус строки не склеивает — он переводит их в числа."),
          ("22\n4\nNaN", "\"5\" превращается в число 5, поэтому результат 3.")],
         code=CODE5)

for a in (a1, a2, a3):
    web_verify("js", a)
web_verify("html", a4)

skills = {"js.basics": "JavaScript: переменные и вывод", "js.functions": "Функции JavaScript",
          "js.dom": "Работа со страницей (DOM)", "js.events": "События: нажатие кнопки"}
write_lesson("web-02-js", "JavaScript: функции, циклы и кнопки",
             "Писать функции и циклы на JavaScript, понимать ошибки и бесконечные циклы, реагировать на нажатия на странице.",
             list(skills), ["web-01-html-css"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Функция печатает вместо return", "fix": "Проверка сравнивает возвращённое значение: пишите return.", "errorType": "AssertionError"},
              {"mistake": "Опечатка в имени переменной", "fix": "ReferenceError подсказывает имя и строку.", "errorType": "ReferenceError"},
              {"mistake": "Бесконечный цикл while", "fix": "Внутри цикла меняйте переменную из условия.", "errorType": "InfiniteLoopError"},
              {"mistake": "Переменная счётчика внутри обработчика", "fix": "Объявляйте её снаружи, иначе она обнуляется при каждом нажатии."},
              {"mistake": "\"2\" + 2", "fix": "Плюс со строкой склеивает. Для чисел используйте Number(...)."}],
             min_pass=3, pack="web-basics", runner="js")

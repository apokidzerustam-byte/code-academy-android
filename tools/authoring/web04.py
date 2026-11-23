"""Урок веб 4: смысловая вёрстка и формы."""
from webib import *


def preview(code):
    return "Предпросмотр страницы:\n" + page_text(code)


SEM = page("""  <header>
    <h1>Мой блог</h1>
    <nav><a href="#posts">Записи</a> <a href="#about">Обо мне</a></nav>
  </header>
  <main>
    <section id="posts">
      <h2>Записи</h2>
      <article><h3>Первый пост</h3><p>Привет, мир!</p></article>
    </section>
  </main>
  <footer>© 2026, Аня</footer>""")
FORM = page("""  <form>
    <label for="name">Имя</label>
    <input id="name" name="name" type="text" required>

    <label for="email">Почта</label>
    <input id="email" name="email" type="email" required>

    <label for="plan">Тариф</label>
    <select id="plan" name="plan">
      <option value="free">Бесплатный</option>
      <option value="pro">Про</option>
    </select>

    <label><input type="checkbox" name="agree"> Согласен с правилами</label>
    <button type="submit">Отправить</button>
  </form>""")
CHECK = page("""  <form id="f">
    <input id="a" required value="">
    <input id="b" type="email" value="ann@site.ru">
    <input id="c" type="email" value="ann@">
  </form>""")
inv = page_text(CHECK, "document.querySelectorAll('input:invalid').length")
assert str(inv) == "2", inv
BAD = page('  <label for="mail">Почта</label>\n  <input id="email" type="text">')
orphan = page_text(BAD, "document.querySelector('label').control === null")
assert orphan is True or str(orphan) == "True", orphan

use_file("index.html")
scenes = [
    scene("intro", "Теги со смыслом", """
      Страницу можно собрать из одних div, но тогда ни поисковик, ни программа для чтения с экрана не поймут, где заголовок
      сайта, где меню, а где основное содержимое. Поэтому в HTML есть теги со смыслом: header — шапка, nav — навигация,
      main — главное содержимое, section — раздел, article — самостоятельная запись, footer — подвал. Выглядят они как обычные
      блоки, зато страница становится понятной и людям, и программам.""",
          [NOTE("`header` · `nav` · `main` · `section` · `article` · `footer` — теги со смыслом вместо одинаковых `div`.", at="Поэтому в HTML")]),
    scene("semantic", "Смысловой каркас", """
      Соберём каркас блога. В шапке заголовок h1 и меню nav с двумя ссылками. Внутри main раздел section с заголовком
      второго уровня и статьёй article. В конце footer с подписью. Запускаем: для глаза всё то же, что и с div, но структура
      страницы теперь читается из самих тегов. Заголовок h1 на странице один, ниже идут h2 и h3 по порядку.""",
          [CLEAR(), T(SEM, at="Соберём"), HL([8, 9, 10, 11], at="В шапке"), HL([12, 13, 14, 15, 16], at="Внутри main"), HL([18], at="В конце"),
           RUN(at="Запускаем"), OUT(preview(SEM), at="Запускаем")]),
    scene("form", "Форма", """
      Теперь форма. Тег form объединяет поля. Каждому полю нужна подпись label. Связываем их так: у подписи атрибут for,
      у поля id с тем же значением. Тогда нажатие на подпись ставит курсор в поле, а программа для чтения с экрана
      правильно озвучивает поле. Тип поля задаёт атрибут type: text, email, number, checkbox. Слово required делает поле
      обязательным. Для выбора из списка есть select с вариантами option, а кнопка отправки — button с типом submit.""",
          [CLEAR(), T(FORM, at="Теперь форма"), HL([8, 9], at="Связываем"), HL([9], at="Тип поля"), HL([9], at="Слово required"),
           HL([14, 15, 16, 17, 18], at="Для выбора"), HL([21], at="кнопка отправки"), RUN(at="Для выбора"), OUT(preview(FORM), at="Для выбора")]),
    scene("valid", "Проверка прямо в браузере", """
      Браузер умеет проверять поля сам. Обязательное пустое поле или почта без домена считаются неверными. У формы есть метод
      checkValidity: он вернёт ложь, если хоть одно поле неверно. Посчитаем неверные поля на примере из трёх: пустое
      обязательное и почта без домена дают два. Но помните: проверка в браузере — лишь удобство для пользователя. Серверу
      доверять данным из формы нельзя, он проверяет их заново.""",
          [CLEAR(), T(CHECK, at="Браузер умеет"), RUN(at="Посчитаем"), OUT(preview(CHECK), at="Посчитаем"),
           NOTE("Измерили: неверных полей — **" + str(inv) + "** (пустое обязательное и «ann@»).", at="дают два")]),
    scene("label", "Подпись не связана с полем", """
      Типичная ошибка: у подписи for один, а у поля id другой. Визуально всё выглядит нормально, но связи нет: нажатие на
      подпись не работает, программа чтения не знает, что к чему. Проверка в заданиях именно это и смотрит: у подписи
      должно быть связанное поле. Чтобы избежать ошибки, копируйте значение id в for.""",
          [CLEAR(), T(BAD, at="Типичная"), HL([8, 9], at="Типичная"), RUN(at="Визуально"), OUT(preview(BAD), at="Визуально"),
           NOTE("Измерили: у подписи связанного поля нет — `label.control === null`.", at="связи нет")]),
    scene("summary", "Итог", """
      Подведём итог. Смысловые теги header, nav, main, section, article и footer делают структуру понятной. В форме у каждого
      поля есть подпись label с атрибутом for, равным id поля. Тип поля задаёт type, обязательность — required, а кнопку
      отправки делает button с типом submit. Проверка в браузере удобна для людей, но не заменяет проверку на сервере.""",
          [NOTE("`label for=\"x\"` ↔ `input id=\"x\"` · `type` · `required` · `select/option` · `button type=\"submit\"`", at="В форме")]),
]
use_file(None)

notes = """
# Смысловая вёрстка и формы

```html
<header><h1>Мой блог</h1><nav>…</nav></header>
<main>
  <section><h2>Записи</h2><article>…</article></section>
</main>
<footer>© 2026</footer>

<form>
  <label for="email">Почта</label>
  <input id="email" name="email" type="email" required>

  <select id="plan" name="plan">
    <option value="free">Бесплатный</option>
  </select>

  <label><input type="checkbox" name="agree"> Согласен</label>
  <button type="submit">Отправить</button>
</form>
```

| Тег / атрибут | Для чего |
|---|---|
| `header`, `nav`, `main`, `footer` | смысл блоков страницы |
| `label for="id"` | подпись, связанная с полем |
| `type` | text, email, number, checkbox, password |
| `required`, `min`, `max`, `pattern` | проверка в браузере |
| `name` | имя поля при отправке данных |

- `h1` на странице один; дальше `h2`, `h3` по порядку.
- Проверка в браузере (`form.checkValidity()`) — удобство, а **не защита**: сервер проверяет заново.
- Подпись без связи (`for` ≠ `id`) — частая ошибка доступности.
"""

# --- Задание 1: смысловой каркас ---
S1 = page("""  <header>
    <h1>Кофейня</h1>
    <nav><a href="#menu">Меню</a> <a href="#contacts">Контакты</a></nav>
  </header>
  <main>
    <p>Свежий кофе каждый день.</p>
  </main>
  <footer>Работаем с 8 до 20</footer>""")
t1 = {"kind": "web", "lang": "html", "cases": [
    {"id": "head", "expr": "((document.querySelector('header h1') || {}).textContent || '').trim()", "expected": "Кофейня"},
    {"id": "nav", "expr": "document.querySelectorAll('header nav a').length", "expected": 2},
    {"id": "main", "expr": "((document.querySelector('main p') || {}).textContent || '').trim()", "expected": "Свежий кофе каждый день."},
    {"id": "foot", "expr": "((document.querySelector('footer') || {}).textContent || '').trim()", "expected": "Работаем с 8 до 20"},
    {"id": "one", "hidden": True, "expr": "document.querySelectorAll('h1, header, main, footer, nav').length", "expected": 5,
     "hint": "Каждый смысловой блок должен быть на странице один раз"},
]}
a1 = asg("a1-semantic", "write", "Каркас сайта",
         "Соберите каркас сайта кофейни из смысловых тегов:\n\n- `header` с заголовком `h1` «Кофейня» и `nav` из **двух** ссылок (тексты любые);\n- `main` с абзацем «Свежий кофе каждый день.»;\n- `footer` с текстом «Работаем с 8 до 20».",
         "Использовать смысловые теги.", "Пустая страница.", "Шапка с меню, основное содержимое, подвал.",
         ["Заголовок h1 один."],
         hints("Вместо одинаковых div — теги со смыслом.", "Шапка — header, в ней h1 и nav.", "Основное содержимое — main, подвал — footer.", "В nav две ссылки a с href.", "<header><h1>Кофейня</h1><nav>…</nav></header>"),
         t1, S1, "header, nav, main и footer не меняют вид, но объясняют структуру страницы людям и программам.",
         ["Все четыре блока на месте."],
         [(page("""  <div>
    <h1>Кофейня</h1>
    <div><a href="#a">Меню</a> <a href="#b">Контакты</a></div>
  </div>
  <div><p>Свежий кофе каждый день.</p></div>
  <div>Работаем с 8 до 20</div>"""), "Везде div вместо смысловых тегов."),
          (page("""  <header>
    <h1>Кофейня</h1>
    <nav><a href="#menu">Меню</a></nav>
  </header>
  <main><p>Свежий кофе каждый день.</p></main>
  <footer>Работаем с 8 до 20</footer>"""), "В меню одна ссылка вместо двух."),
          (page("""  <header>
    <h1>Кофейня</h1>
    <nav><a href="#a">Меню</a> <a href="#b">Контакты</a></nav>
    <p>Свежий кофе каждый день.</p>
  </header>
  <footer>Работаем с 8 до 20</footer>"""), "Нет main: абзац лежит в шапке.")],
         starter=page("  <!-- Ваш каркас -->"))

# --- Задание 2: форма ---
S2 = page("""  <form>
    <label for="name">Имя</label>
    <input id="name" name="name" type="text" required>
    <label for="email">Почта</label>
    <input id="email" name="email" type="email" required>
    <button type="submit">Отправить</button>
  </form>""")
t2 = {"kind": "web", "lang": "html", "cases": [
    {"id": "name", "expr": "(document.querySelector('label[for=\"name\"]') || {}).control && document.querySelector('label[for=\"name\"]').control.type", "expected": "text"},
    {"id": "email", "expr": "(document.querySelector('label[for=\"email\"]') || {}).control && document.querySelector('label[for=\"email\"]').control.type", "expected": "email"},
    {"id": "req", "expr": "[...document.querySelectorAll('input')].every(i => i.required)", "expected": True},
    {"id": "btn", "expr": "((document.querySelector('form button[type=\"submit\"]') || {}).textContent || '').trim()", "expected": "Отправить"},
    {"id": "names", "hidden": True, "expr": "[...document.querySelectorAll('input')].map(i => i.name).join(',')", "expected": "name,email",
     "hint": "У полей должны быть атрибуты name: name и email"},
    {"id": "labels", "hidden": True, "expr": "document.querySelectorAll('label').length", "expected": 2},
]}
a2 = asg("a2-form", "write", "Форма регистрации",
         "Сделайте форму из двух **обязательных** полей и кнопки:\n\n- `Имя` — текстовое поле, `id` и `name` равны `name`;\n- `Почта` — поле типа `email`, `id` и `name` равны `email`;\n- кнопка отправки с текстом `Отправить`.\n\nУ каждого поля — подпись `label`, связанная с ним.",
         "Собрать форму с подписями.", "Пустая страница.", "Форма с двумя связанными полями и кнопкой.",
         ["Подпись связывается атрибутом for."],
         hints("Все поля пишут внутри тега form.", "Подпись: <label for=\"name\">; поле: <input id=\"name\">.", "Тип почты — type=\"email\", обязательность — required.", "Кнопка: <button type=\"submit\">Отправить</button>.", "У поля нужны id (для label) и name (для отправки)."),
         t2, S2, "label for связывается с id поля; type задаёт вид поля, required — обязательность, name — имя при отправке.",
         ["Подписи связаны, поля обязательны, кнопка есть."],
         [(page("""  <form>
    <label>Имя</label>
    <input id="name" name="name" type="text" required>
    <label>Почта</label>
    <input id="email" name="email" type="email" required>
    <button type="submit">Отправить</button>
  </form>"""), "Подписи не связаны с полями (нет for)."),
          (page("""  <form>
    <label for="name">Имя</label>
    <input id="name" name="name" type="text" required>
    <label for="email">Почта</label>
    <input id="email" name="email" type="text" required>
    <button type="submit">Отправить</button>
  </form>"""), "У почты тип text, а нужен email."),
          (page("""  <form>
    <label for="name">Имя</label>
    <input id="name" name="name" type="text">
    <label for="email">Почта</label>
    <input id="email" name="email" type="email">
    <button type="submit">Отправить</button>
  </form>"""), "Поля не обязательны: нет required."),
          (page("""  <form>
    <label for="name">Имя</label>
    <input id="name" type="text" required>
    <label for="email">Почта</label>
    <input id="email" type="email" required>
    <button type="submit">Отправить</button>
  </form>"""), "У полей нет name — данные не отправятся.")],
         starter=page("  <!-- Ваша форма -->"))

# --- Задание 3: select ---
S3 = page("""  <label for="lang">Любимый язык</label>
  <select id="lang" name="lang">
    <option value="py">Python</option>
    <option value="js">JavaScript</option>
    <option value="kt">Kotlin</option>
  </select>""")
t3 = {"kind": "web", "lang": "html", "cases": [
    {"id": "link", "expr": "(document.querySelector('label[for=\"lang\"]') || {}).control && document.querySelector('label[for=\"lang\"]').control.tagName", "expected": "SELECT"},
    {"id": "values", "expr": "[...document.querySelectorAll('select#lang > option')].map(o => o.value).join(',')", "expected": "py,js,kt"},
    {"id": "texts", "expr": "[...document.querySelectorAll('select#lang > option')].map(o => o.textContent.trim()).join(',')", "expected": "Python,JavaScript,Kotlin"},
    {"id": "name", "hidden": True, "expr": "(document.getElementById('lang') || {}).name", "expected": "lang"},
]}
a3 = asg("a3-select", "write", "Выпадающий список",
         "Добавьте подписанный выпадающий список: `select` с `id` и `name` равными `lang` и подписью «Любимый язык». Три варианта: значения `py`, `js`, `kt` с текстами `Python`, `JavaScript`, `Kotlin` — по порядку.",
         "Использовать select и option.", "Пустая страница.", "Список из трёх вариантов с подписью.",
         ["Значение (value) и видимый текст различаются."],
         hints("Выпадающий список — тег select, варианты — option внутри него.", "Видимый текст — между тегами option, а значение для программы — атрибут value.", "Подпись связывается с select через for и id.", "У select не забудьте name.", "<option value=\"py\">Python</option>"),
         t3, S3, "В option value уходит программе, а текст видит человек. label for связывает подпись с select.",
         ["Три варианта по порядку, подпись связана."],
         [(page("""  <label for="lang">Любимый язык</label>
  <select id="lang" name="lang">
    <option>Python</option>
    <option>JavaScript</option>
    <option>Kotlin</option>
  </select>"""), "Нет значений value: вместо py, js, kt уходят тексты."),
          (page("""  <label for="lang">Любимый язык</label>
  <select id="lang" name="lang">
    <option value="kt">Kotlin</option>
    <option value="js">JavaScript</option>
    <option value="py">Python</option>
  </select>"""), "Порядок вариантов перепутан."),
          (page("""  <label>Любимый язык</label>
  <select id="lang" name="lang">
    <option value="py">Python</option>
    <option value="js">JavaScript</option>
    <option value="kt">Kotlin</option>
  </select>"""), "Подпись не связана со списком.")],
         starter=page("  <!-- Ваш список -->"))

# --- Задание 4: исправить ---
STARTER4 = page("""  <label for="mail">Почта</label>
  <input id="email" name="email" type="text">
  <label for="age">Возраст</label>
  <input id="age" name="age" type="text">""")
S4 = page("""  <label for="email">Почта</label>
  <input id="email" name="email" type="email">
  <label for="age">Возраст</label>
  <input id="age" name="age" type="number">""")
t4 = {"kind": "web", "lang": "html", "cases": [
    {"id": "mail-link", "expr": "(document.querySelector('label') || {}).control ? document.querySelector('label').control.id : null", "expected": "email"},
    {"id": "mail-type", "expr": "document.getElementById('email').type", "expected": "email"},
    {"id": "age-type", "expr": "document.getElementById('age').type", "expected": "number"},
    {"id": "age-link", "hidden": True, "expr": "document.querySelector('label[for=\"age\"]').control === document.getElementById('age')", "expected": True},
]}
a4 = asg("a4-fix", "fix", "Почта не связывается",
         "В форме три ошибки: подпись «Почта» не связана с полем, а у почты и возраста неподходящие типы. Найдите и исправьте. Менять `id` полей и `name` не нужно.",
         "Чинить связь label и типы полей.", "Страница с двумя полями.", "Подписи связаны, типы email и number.",
         ["id и name полей не менять."],
         hints("Нажмите на подпись «Почта»: курсор попадёт в поле?", "for подписи должен совпадать с id поля.", "У подписи сейчас for=\"mail\", а поле называется email.", "Тип поля для почты — email, для возраста — number.", "Исправьте for и два type."),
         t4, S4, "Связь label for ↔ input id работает только при точном совпадении. Правильный type включает проверку и удобную клавиатуру на телефоне.",
         ["Подпись связана, типы верны."],
         [(STARTER4.replace('type="text">\n  <label for="age"', 'type="email">\n  <label for="age"').replace('id="age" name="age" type="text"', 'id="age" name="age" type="number"'), "Типы исправлены, а подпись по-прежнему не связана."),
          (STARTER4.replace('for="mail"', 'for="email"'), "Связь исправлена, но типы остались text.")],
         starter=STARTER4)

# --- Задание 5: предсказать ---
CODE5 = page("""  <form id="f">
    <input id="a" required value="">
    <input id="b" type="email" value="ann@site.ru">
    <input id="c" type="email" value="ann@">
    <input id="d" type="number" min="1" max="10" value="12">
    <input id="e" type="text" value="ok">
  </form>""")
ans5 = str(page_text(CODE5, "document.querySelectorAll('input:invalid').length"))
assert ans5 == "3", ans5
a5 = asg("a5-predict", "predict", "Сколько полей неверны?",
         "Сколько полей из пяти браузер сочтёт **неверными** (`:invalid`)? Ответьте числом.",
         "Понимать проверку полей формы.", "—", "Одно число.", [],
         hints("Проверьте каждое поле по очереди.", "Пустое обязательное поле неверно.", "Почта должна содержать домен после «@».", "Число не должно выходить за min и max.", "Неверны три поля, кроме ann@site.ru и ok."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "Неверны: пустое обязательное (a), «ann@» (c) и число 12 больше max=10 (d). Остальные два в порядке.", ["Верное число."],
         [("1", "Неверных полей больше одного."), ("2", "Пропущено число за пределами min/max."), ("5", "Часть полей корректна: ann@site.ru и текст ok.")],
         code=CODE5)

for a in (a1, a2, a3, a4):
    web_verify("html", a)

skills = {"web.semantic": "Смысловые теги страницы", "web.forms": "Формы: label, input, select", "web.validation": "Проверка полей в браузере"}
write_lesson("web-04-forms", "Смысловая вёрстка и формы",
             "Размечать страницу тегами со смыслом и собирать формы с подписями, типами полей и проверкой в браузере.",
             list(skills), ["web-03-layout"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Везде div вместо смысловых тегов", "fix": "Используйте header, nav, main, section, footer: структура понятна людям и программам."},
              {"mistake": "for подписи не равен id поля", "fix": "Копируйте значение id в for: нажатие на подпись должно ставить курсор в поле."},
              {"mistake": "Поле без атрибута name", "fix": "Без name данные поля не попадут в отправляемую форму."},
              {"mistake": "Доверяют только проверке в браузере", "fix": "Сервер всегда проверяет данные формы заново."}],
             min_pass=3, pack="web-basics", runner="html")
merge_pack("web-basics", "web-04-forms", skills,
           "Страницы во встроенном браузере без интернета: разметка, оформление, раскладка, формы и поведение.")

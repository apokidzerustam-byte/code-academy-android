"""Урок веб 6: анимации и доступность."""
from webib import *


def preview(code):
    return "Предпросмотр страницы:\n" + page_text(code)


def val(code, expr):
    return measure(code, expr)


Q = "document.querySelector"
RULES = "[...document.styleSheets].flatMap(s => [...s.cssRules])"

CSS1 = """.btn {
  background: teal;
  color: white;
  border: 0;
  padding: 10px 16px;
  transition: background 0.3s;
}
.btn:hover {
  background: darkcyan;
}"""
BTN = '  <button class="btn">Сохранить</button>'
S_BTN = page(BTN, style(CSS1))
CS_BTN = "getComputedStyle(document.querySelector('.btn'))"
btn_tr = val(S_BTN, CS_BTN + ".transitionDuration + ' ' + " + CS_BTN + ".transitionProperty")
assert btn_tr == "0.3s background", btn_tr

CSS2 = """@keyframes pulse {
  from { transform: scale(1); }
  to   { transform: scale(1.15); }
}
.dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: tomato;
  animation: pulse 1s ease-in-out infinite alternate;
}"""
DOT = '  <div class="dot"></div>'
S_DOT = page(DOT, style(CSS2))
CS_DOT = "getComputedStyle(document.querySelector('.dot'))"
dot_an = val(S_DOT, CS_DOT + ".animationName + ' ' + " + CS_DOT + ".animationDuration + ' ' + " + CS_DOT + ".animationIterationCount")
assert dot_an == "pulse 1s infinite", dot_an

RM = "\n@media (prefers-reduced-motion: reduce) {\n  .dot {\n    animation: none;\n  }\n}"
S_RM = page(DOT, style(CSS2 + RM))
rm_match = val(S_RM, "matchMedia('(prefers-reduced-motion: reduce)').matches")
rm_name = val(S_RM, CS_DOT + ".animationName")
assert rm_match == "False" and rm_name == "pulse", (rm_match, rm_name)

CONTRAST_BODY = '''  <p id="out"></p>
  <script>
    function channel(c) {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    }
    function luminance(hex) {
      const n = parseInt(hex.slice(1), 16);
      return 0.2126 * channel(n >> 16) + 0.7152 * channel((n >> 8) & 255) + 0.0722 * channel(n & 255);
    }
    function contrast(fg, bg) {
      const a = luminance(fg), b = luminance(bg);
      return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    }
    document.getElementById("out").textContent = ["#000000", "#777777", "#767676"].map((c) => contrast(c, "#ffffff").toFixed(2)).join(" ");
  </script>'''
S_CON = page(CONTRAST_BODY)
con_out = page_text(S_CON)
assert con_out.strip() == "21.00 4.48 4.54", con_out

use_file("index.html")
scenes = [
    scene("intro", "Живо и для всех", """
      Сегодня два взаимосвязанных вопроса. Первый: как сделать интерфейс живым, чтобы кнопка плавно меняла цвет, а загрузка
      крутилась. Второй, куда более важный: как сделать сайт доступным для всех. Среди пользователей есть люди с плохим зрением,
      с нарушением моторики, и такие, кто пользуется программой чтения с экрана или вообще не работает мышью. Есть и те,
      кому просто мешает солнце на экране телефона. Доступность не дополнение, а часть качества, и многие её правила совсем
      простые. Хорошая новость в том, что то, что помогает одним, обычно удобно всем: подписи, контраст и понятная структура
      облегчают жизнь каждому. А ещё доступные страницы лучше находят поисковые системы.""",
          [NOTE("**Анимации** — плавность и подсказки · **Доступность** — сайт, которым могут пользоваться все", at="Второй, куда")]),
    scene("transition", "Плавный переход", """
      Начнём с самого простого эффекта. Обычно при наведении на кнопку цвет меняется мгновенно. Свойство transition делает
      изменение плавным. Ему передают, что менять и сколько это должно длиться: здесь фон и три десятых секунды. Очень важная
      деталь: transition записывается в обычное состояние элемента, а не в состояние наведения. Тогда плавно происходит и
      наведение, и возврат. Если написать его только в правило с hover, плавной станет лишь одна сторона. Запускаем и
      проверяем: у кнопки в обычном состоянии стоит длительность три десятых секунды. Если хотите изменять сразу
      несколько свойств, перечислите их через запятую или напишите слово all, но тогда следите, чтобы не анимировалось лишнее.""",
          [CLEAR(), T(S_BTN, at="Начнём"), HL([12], at="Свойство transition"), HL([14, 15, 16], at="Очень важная"), RUN(at="Запускаем и"), OUT(preview(S_BTN), at="Запускаем и"),
           NOTE("Измерили: переход кнопки — **" + btn_tr + "** (длительность и свойство).", at="длительность три десятых")]),
    scene("keyframes", "Ключевые кадры", """
      Если нужно движение, которое идёт само, без наведения, используют анимацию. Сначала описывают кадры правилом keyframes: имя
      анимации и состояния от начала до конца. Здесь элемент увеличивается примерно на пятнадцать процентов. Потом элементу
      назначают свойство animation: имя, длительность в одну секунду, плавность, число повторений и направление. Слово
      infinite означает бесконечно, а alternate заставляет анимацию идти туда и обратно. Запускаем: точка пульсирует, а браузер
      подтверждает имя, длительность и бесконечное повторение. Анимации хороши, когда помогают понять происходящее: показывают, что
      идёт загрузка, или привлекают внимание к нужному месту. Мигающие и мельтешащие эффекты только раздражают.""",
          [CLEAR(), T(S_DOT, at="Если нужно"), HL([7, 8, 9, 10], at="Сначала описывают"), HL([16], at="Потом элементу"), RUN(at="Запускаем"), OUT(preview(S_DOT), at="Запускаем"),
           NOTE("Измерили: анимация — **" + dot_an + "**.", at="браузер")]),
    scene("fast", "Что анимировать", """
      Не всё можно анимировать одинаково дёшево. Если менять ширину, высоту или положение сверху, браузеру приходится заново
      вычислять раскладку всей страницы, и на слабом телефоне появляются рывки. А вот transform и opacity браузер умеет
      обрабатывать отдельно и очень быстро. Поэтому двигайте, поворачивайте и увеличивайте через transform, а появление и
      исчезновение делайте через opacity. И не злоупотребляйте анимациями: короткие, до полусекунды, полезнее долгих. Хорошая анимация почти незаметна: человек не думает «как красиво»,
      а просто понимает, что произошло.""",
          [NOTE("Быстро: `transform`, `opacity` · Медленно: `width`, `height`, `top`, `left` · Длительность — до ~0.5 с", at="А вот transform")]),
    scene("reduced", "Уважайте настройки", """
      Для некоторых людей движение на экране вредно: оно вызывает головокружение и тошноту. Поэтому в системе есть настройка
      уменьшения движения, а в CSS медиазапрос prefers-reduced-motion. Внутри него анимацию отключают. Это то самое правило, которое
      нужно писать почти всегда, когда есть анимация. На нашем экране настройка выключена, поэтому точка по-прежнему пульсирует:
      запрос возвращает ложь, а имя анимации прежнее. Но у человека с включённой настройкой точка будет стоять спокойно. В телефоне эта настройка находится в
      разделе специальных возможностей, и приложение или сайт обязаны её учитывать.""",
          [CLEAR(), T(S_RM, at="Для некоторых"), HL([18, 19, 20, 21, 22], at="Внутри него"), RUN(at="На нашем экране"), OUT(preview(S_RM), at="На нашем экране"),
           NOTE("Измерили: `prefers-reduced-motion: reduce` — **" + rm_match.lower() + "**, имя анимации — **" + rm_name + "**.", at="запрос возвращает")]),
    scene("a11y", "Основы доступности", """
      Теперь доступность. Правил много, начнём с самых частых. Первое: у каждой содержательной картинки есть атрибут alt с
      коротким описанием, а у чисто декоративной он пустой. Второе: у каждого поля ввода есть подпись label, а один
      placeholder её не заменяет. Третье: кнопка только с значком, например лупой, получает aria-label с названием действия,
      иначе программа чтения произнесёт неизвестно что. Четвёртое: используйте смысловые теги и правильные заголовки, ведь именно по ним
      слепой человек перемещается по странице. И пятое: у страницы есть язык в теге html. Проверить многое можно прямо с телефона: включите программу
      чтения с экрана и попробуйте пройти по своей странице, не глядя на неё. Сразу станет ясно, чего не хватает.""",
          [NOTE("`<img alt=\"Фото команды\">` · `<label for=\"q\">` · `<button aria-label=\"Поиск\">🔍</button>` · смысловые теги · `<html lang=\"ru\">`", at="Правил много")]),
    scene("contrast", "Контрастность", """
      Текст должен быть хорошо виден. Для этого есть измеримая норма: отношение яркости текста и фона не меньше четырёх с половиной к одному
      для обычного текста и трёх к одному для крупного. Это отношение можно посчитать кодом. Сначала каждая составляющая цвета
      приводится к линейной шкале, потом считается относительная яркость, и наконец берётся отношение более светлого к более тёмному
      с добавкой ноль целых пять сотых. Запускаем: чёрный на белом даёт двадцать один, средне-серый на белом четыре и сорок восемь
      сотых, то есть чуть меньше нормы, а чуть более тёмный серый уже проходит с запасом. Разница на глаз почти не видна,
      а для читающих с плохим зрением она значима. Не опирайтесь только на цвет: ошибку в поле показывайте
      не только красным, но и текстом, ведь часть людей не различает красный и зелёный.""",
          [CLEAR(), T(S_CON, at="Текст должен"), HL([10, 11, 12, 13], at="Сначала"), HL([14, 15, 16, 17], at="потом считается"), HL([18, 19, 20, 21], at="и наконец"),
           RUN(at="Запускаем"), OUT(preview(S_CON), at="Запускаем"), NOTE("Измерили: **" + con_out.strip() + "** — чёрный, #777777 (не проходит), #767676 (проходит).", at="чёрный на белом")]),
    scene("focus", "Клавиатура и фокус", """
      Не все пользуются мышью. Кто-то переходит между кнопками клавишей Tab, и браузер показывает, где сейчас фокус, контуром. Самая
      частая ошибка дизайнеров: убрать контур правилом outline none, потому что он «некрасивый». Тогда человек с клавиатурой
      теряется. Если контур не нравится, замените его своим, например через псевдокласс focus-visible. Кнопки и ссылки делайте настоящими
      тегами button и a, а не блоками div с обработчиком: настоящие теги сами получают фокус и работают с клавиатурой.""",
          [NOTE("Не убирайте `outline`, а замените: `button:focus-visible { outline: 3px solid orange; }`", at="Самая"),
           NOTE("Кнопка — `button`, ссылка — `a`: фокус и клавиатура работают сами", at="Кнопки и ссылки")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: картинка без alt. Вторая: поле с одним только placeholder. Третья: outline none без замены.
      Четвёртая: анимация без учёта настройки уменьшения движения и слишком длинная.""",
          [NOTE("Ошибка 1: нет `alt`.", at="Первая"), NOTE("Ошибка 2: только `placeholder`.", at="Вторая"), NOTE("Ошибка 3: `outline: none` без замены.", at="Третья"),
           NOTE("Ошибка 4: анимация игнорирует `prefers-reduced-motion`.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. Transition плавно меняет значения, и его пишут в обычное состояние элемента. Анимации описываются keyframes
      и назначаются свойством animation. Двигайте через transform и opacity, а при включённом уменьшении движения отключайте
      анимацию. Доступность это alt у картинок, подписи у полей, aria-label у кнопок со значком, видимый фокус и достаточный
      контраст. В заданиях вы напишете плавный переход, вращение, отключение анимации, исправите страницу и реализуете
      расчёт контраста.""",
          [NOTE("`transition` · `@keyframes` · `animation` · `prefers-reduced-motion` · `alt` · `label` · `aria-label` · `:focus-visible` · контраст ≥ 4.5 : 1", at="Подведём итог")]),
]
use_file(None)

notes = """
# Анимации и доступность

```css
.btn {
  transition: background 0.3s;         /* в обычном состоянии, а не в :hover */
}
.btn:hover { background: darkcyan; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.loader { animation: spin 1s linear infinite; }

@media (prefers-reduced-motion: reduce) {
  .loader { animation: none; }
}

button:focus-visible { outline: 3px solid orange; }
```

```html
<img src="team.jpg" alt="Фото команды">
<label for="q">Поиск</label> <input id="q">
<button aria-label="Поиск">🔍</button>
```

| Что | Правило |
|---|---|
| быстрая анимация | `transform`, `opacity` |
| уменьшение движения | `@media (prefers-reduced-motion: reduce)` |
| контраст текста | не меньше 4.5 : 1 (крупный — 3 : 1) |
| фокус | не убирайте `outline` без замены |

- Контраст: `(L светлого + 0.05) / (L тёмного + 0.05)`, где L — относительная яркость цвета.
- Кнопка — `button`, ссылка — `a`: фокус и клавиатура работают сами.
"""

# --- Задание 1: transition ---
BASE1 = ".btn {\n  background: teal;\n  color: white;\n  border: 0;\n  padding: 10px 16px;\n}\n.btn:hover {\n  background: darkcyan;\n}"
S1 = page(BTN, style(BASE1.replace("  padding: 10px 16px;\n", "  padding: 10px 16px;\n  transition: background 0.3s;\n")))
TQ = "getComputedStyle(document.querySelector('.btn'))"
t1 = {"kind": "web", "lang": "html", "cases": [
    {"id": "duration", "expr": TQ + ".transitionDuration", "expected": "0.3s"},
    {"id": "prop", "expr": "/^(all|background(-color)?)$/.test(" + TQ + ".transitionProperty)", "expected": True},
    {"id": "hover", "hidden": True, "expr": RULES + ".some(r => r.selectorText === '.btn:hover' && r.style.backgroundColor !== '')", "expected": True, "hint": "Правило :hover трогать не нужно"},
]}
a1 = asg("a1-transition", "write", "Плавная кнопка",
         "Кнопка при наведении меняет фон на `darkcyan` (правило `.btn:hover` уже есть), но делает это резко. Сделайте изменение **плавным**: за `0.3s`, для фона. Правило `:hover` не меняйте.",
         "Добавить transition в нужное место.", "Страница с кнопкой.", "У кнопки в обычном состоянии задан переход фона на 0.3 секунды.",
         ["Только CSS."],
         hints("Плавность задаёт свойство transition.", "В нём указывают, что менять и сколько длится: свойство и время.", "Для фона: background, для 0.3 секунды: 0.3s.", "Писать его нужно в правило .btn, а не в .btn:hover.",
               "transition: background 0.3s;"),
         t1, S1, "transition в обычном состоянии плавно меняет значение и при наведении, и при возврате; в :hover он работал бы только в одну сторону.",
         ["Переход 0.3s задан в .btn."],
         [(page(BTN, style(BASE1.replace("  background: darkcyan;\n", "  background: darkcyan;\n  transition: background 0.3s;\n"))), "transition записан в :hover: у кнопки в обычном состоянии перехода нет."),
          (page(BTN, style(BASE1.replace("  padding: 10px 16px;\n", "  padding: 10px 16px;\n  transition: background 3s;\n"))), "Длительность 3 секунды вместо 0.3."),
          (page(BTN, style(BASE1.replace("  padding: 10px 16px;\n", "  padding: 10px 16px;\n  transition: color 0.3s;\n"))), "Плавно меняется цвет текста, а не фон.")],
         starter=page(BTN, style(BASE1)))

# --- Задание 2: keyframes ---
LOADER = '  <div class="loader"></div>'
BASE2 = ".loader {\n  width: 32px;\n  height: 32px;\n  border: 4px solid #ddd;\n  border-top-color: teal;\n  border-radius: 50%;\n}"
SOL2 = "@keyframes spin {\n  from { transform: rotate(0deg); }\n  to   { transform: rotate(360deg); }\n}\n" + BASE2.replace("  border-radius: 50%;\n", "  border-radius: 50%;\n  animation: spin 1s linear infinite;\n")
LQ = "getComputedStyle(document.querySelector('.loader'))"
t2 = {"kind": "web", "lang": "html", "cases": [
    {"id": "name", "expr": LQ + ".animationName", "expected": "spin"},
    {"id": "dur", "expr": LQ + ".animationDuration + ' ' + " + LQ + ".animationIterationCount + ' ' + " + LQ + ".animationTimingFunction", "expected": "1s infinite linear"},
    {"id": "frames", "expr": RULES + ".some(r => r.type === 7 && r.name === 'spin' && r.cssText.includes('rotate(360deg)'))", "expected": True, "hint": "Нужны ключевые кадры spin с поворотом до 360 градусов"},
]}
a2 = asg("a2-spin", "write", "Крутящийся индикатор",
         "Круг `.loader` должен **бесконечно вращаться**. Опишите ключевые кадры `spin` (от `rotate(0deg)` до `rotate(360deg)`) и назначьте анимацию `.loader`: имя `spin`, длительность **1 секунда**, равномерная плавность (`linear`), повторение — бесконечное.",
         "Написать анимацию вращения.", "Страница с кругом.", "Круг вращается бесконечно.",
         ["Только CSS."],
         hints("Анимация состоит из двух частей: описание кадров и назначение элементу.", "Кадры: @keyframes имя { from { … } to { … } }.", "Поворот задаёт transform: rotate(...).", "Назначение: animation: имя длительность плавность повторения.",
               "animation: spin 1s linear infinite; и @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }"),
         t2, page(LOADER, style(SOL2)), "@keyframes описывает кадры, а animation назначает их элементу: имя, длительность, плавность и число повторений.",
         ["Кадры spin заданы.", "Анимация назначена: 1s linear infinite."],
         [(page(LOADER, style(SOL2.replace(" infinite;", ";"))), "Нет повторения: анимация проиграет один раз и остановится."),
          (page(LOADER, style(SOL2.replace("1s linear", "1s ease"))), "Плавность ease: вращение замедляется в начале и в конце."),
          (page(LOADER, style(SOL2.replace("rotate(360deg)", "rotate(180deg)"))), "Поворот только на полоборота."),
          (page(LOADER, style(BASE2.replace("  border-radius: 50%;\n", "  border-radius: 50%;\n  animation: spin 1s linear infinite;\n"))), "Анимация назначена, но ключевых кадров spin нет.")],
         starter=page(LOADER, style(BASE2)))

# --- Задание 3: reduced motion ---
t3 = {"kind": "web", "lang": "html", "cases": [
    {"id": "base", "expr": CS_DOT + ".animationName", "expected": "pulse"},
    {"id": "media", "expr": RULES + ".some(r => r.media && /prefers-reduced-motion:\\s*reduce/.test(r.conditionText || r.media.mediaText) && [...r.cssRules].some(x => x.style && x.style.animationName === 'none'))", "expected": True,
     "hint": "Внутри медиазапроса анимация должна отключаться: animation: none"},
]}
a3 = asg("a3-reduced", "write", "Уважать настройку движения",
         "У точки `.dot` есть анимация пульсации. Добавьте в конец стилей медиазапрос `(prefers-reduced-motion: reduce)`, внутри которого анимация точки **отключается**. Обычная анимация (без настройки) должна остаться.",
         "Отключать анимацию при включённом уменьшении движения.", "Страница с пульсирующей точкой.", "Медиазапрос с animation: none; обычная анимация сохранена.",
         ["Основное правило .dot не меняйте."],
         hints("Настройку системы читает медиазапрос prefers-reduced-motion.", "Нужное значение — reduce: пользователь просит меньше движения.", "Запись: @media (prefers-reduced-motion: reduce) { … }.", "Внутри пишут правило для .dot.", "@media (prefers-reduced-motion: reduce) { .dot { animation: none; } }"),
         t3, page(DOT, style(CSS2 + RM)), "Медиазапрос prefers-reduced-motion срабатывает у людей, включивших уменьшение движения; в нём анимацию отключают, а остальным она остаётся.",
         ["Медиазапрос с animation: none.", "Обычная анимация осталась."],
         [(page(DOT, style(CSS2 + RM.replace("reduce", "no-preference"))), "Условие no-preference срабатывает у тех, кто движения не ограничивал."),
          (page(DOT, style(CSS2.replace("  animation: pulse 1s ease-in-out infinite alternate;\n", ""))), "Анимация удалена совсем: у всех пользователей точка неподвижна."),
          (page(DOT, style(CSS2 + RM.replace("animation: none;", "transition: none;"))), "Отключён transition, а анимация осталась.")],
         starter=page(DOT, style(CSS2)))

# --- Задание 4: доступность ---
IMG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='40'%3E%3Crect width='80' height='40' fill='%2380cbc4'/%3E%3C/svg%3E"
BODY4 = lambda img_alt, label, btn_attr: (
    f'  <header><h1>Мой сайт</h1></header>\n  <main>\n    <img class="photo" src="{IMG}"{img_alt}>\n    {label}<input id="q" type="text" placeholder="Поиск">\n    <button class="icon"{btn_attr}>🔍</button>\n  </main>')
CSS4_BAD = "button:focus {\n  outline: none;\n}"
CSS4_OK = "button:focus-visible {\n  outline: 3px solid orange;\n}"
B4_OK = BODY4(' alt="Фото команды"', '<label for="q">Поиск по сайту</label> ', ' aria-label="Поиск"')
t4 = {"kind": "web", "lang": "html", "cases": [
    {"id": "alt", "expr": "((" + Q + "('img.photo') || {}).alt || '').trim().length > 0", "expected": True},
    {"id": "label", "expr": "(() => { const i = document.getElementById('q'); return (i.labels && i.labels.length > 0) || !!(i.getAttribute('aria-label') || '').trim(); })()", "expected": True},
    {"id": "btn", "expr": "((" + Q + "('button.icon') || {}).getAttribute('aria-label') || '').trim().length > 0", "expected": True},
    {"id": "focus", "expr": "!" + RULES + ".some(r => r.selectorText && /:focus/.test(r.selectorText) && r.style && r.style.outlineStyle === 'none')", "expected": True,
     "hint": "Контур фокуса нельзя просто убирать"},
    {"id": "same", "hidden": True, "expr": "document.querySelectorAll('img, input, button').length", "expected": 3, "hint": "Элементы удалять не нужно"},
]}
a4 = asg("a4-a11y", "fix", "Недоступная страница",
         "На странице четыре проблемы доступности. Исправьте их, не удаляя элементов: у **картинки** нет описания (`alt`, не пустое); у **поля** `#q` нет подписи (добавьте `label` с `for` или `aria-label`); у **кнопки** `.icon` только значок, дайте ей `aria-label`; "
         "правило `button:focus { outline: none; }` **убирает контур фокуса** — уберите его или замените видимым контуром (например, `:focus-visible`).",
         "Находить и исправлять проблемы доступности.", "Страница с картинкой, полем и кнопкой.", "Описание, подпись, название кнопки и видимый фокус.",
         ["Элементы img, input и button должны остаться."],
         hints("Программа чтения нуждается в тексте там, где смысл передан картинкой или значком.", "У содержательной картинки нужен непустой alt.", "Подпись поля: label с for, равным id поля, либо aria-label.", "Кнопке со значком — aria-label с названием действия.",
               "outline: none убирает контур: замените правилом button:focus-visible { outline: 3px solid orange; }"),
         t4, page(B4_OK, style(CSS4_OK)), "Тексты alt и aria-label озвучиваются программой чтения, label связывает подпись с полем, а видимый фокус нужен людям, которые работают с клавиатурой.",
         ["Картинка, поле и кнопка получили названия.", "Фокус виден."],
         [(page(BODY4(' alt=""', '<label for="q">Поиск по сайту</label> ', ' aria-label="Поиск"'), style(CSS4_OK)), "Пустой alt: картинка содержательная, а пустое описание — для декоративных."),
          (page(BODY4(' alt="Фото команды"', '', ' aria-label="Поиск"'), style(CSS4_OK)), "У поля нет подписи: placeholder её не заменяет."),
          (page(BODY4(' alt="Фото команды"', '<label for="q">Поиск по сайту</label> ', ''), style(CSS4_OK)), "У кнопки со значком нет названия."),
          (page(B4_OK, style(CSS4_BAD)), "Контур фокуса по-прежнему убран.")],
         starter=page(BODY4("", "", ""), style(CSS4_BAD)))

# --- Задание 5: контраст ---
CR_START = page('  <script>\n    function contrastRatio(fg, bg) {\n      // ваш код\n    }\n  </script>')
CR_SOL = page('''  <script>
    function channel(c) {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    }
    function luminance(hex) {
      const n = parseInt(hex.slice(1), 16);
      return 0.2126 * channel(n >> 16) + 0.7152 * channel((n >> 8) & 255) + 0.0722 * channel(n & 255);
    }
    function contrastRatio(fg, bg) {
      const a = luminance(fg), b = luminance(bg);
      const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      return Number(ratio.toFixed(2));
    }
  </script>''')
t5 = {"kind": "web", "lang": "html", "cases": [
    {"id": "bw", "expr": "contrastRatio('#000000', '#ffffff')", "expected": 21},
    {"id": "gray", "expr": "contrastRatio('#777777', '#ffffff')", "expected": 4.48},
    {"id": "swap", "expr": "contrastRatio('#ffffff', '#767676')", "expected": 4.54, "hint": "Порядок аргументов не важен: делится светлый на тёмный"},
    {"id": "same", "hidden": True, "expr": "contrastRatio('#ffffff', '#ffffff')", "expected": 1},
    {"id": "red", "hidden": True, "expr": "contrastRatio('#ff0000', '#ffffff')", "expected": 4},
    {"id": "teal", "hidden": True, "expr": "contrastRatio('#008080', '#000000')", "expected": 4.4},
    {"id": "blue", "hidden": True, "expr": "contrastRatio('#0000ff', '#ffffff')", "expected": 8.59},
]}
a5 = asg("a5-contrast", "write", "Расчёт контрастности",
         "Реализуйте `contrastRatio(fg, bg)`: цвета заданы строками `#rrggbb`. Формулы:\n\n"
         "- каналу `c` (0–255) сопоставьте `v = c / 255`, затем `v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4`;\n"
         "- относительная яркость `L = 0.2126·R + 0.7152·G + 0.0722·B` (по преобразованным каналам);\n"
         "- отношение `(L светлого + 0.05) / (L тёмного + 0.05)`.\n\n"
         "Верните число, округлённое до **двух знаков** (тип number). Порядок аргументов не важен.",
         "Посчитать отношение контраста по формуле.", "Два цвета.", "Число — отношение контраста.",
         ["Без библиотек."],
         hints("Сначала нужна яркость каждого цвета, потом отношение.", "Цвет #rrggbb разберите на три канала: parseInt(hex.slice(1), 16) и сдвиги битов (>> 16, >> 8, & 255).", "Канал: v = c / 255; v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4).",
               "Яркость: 0.2126 * R + 0.7152 * G + 0.0722 * B.", "(max + 0.05) / (min + 0.05) и Number(x.toFixed(2))."),
         t5, CR_SOL, "Яркость считается по линейным каналам с коэффициентами для красного, зелёного и синего; отношение берут от более светлого к более тёмному, поэтому порядок аргументов не важен.",
         ["Верные значения на всех наборах."],
         [(CR_SOL.replace("c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)", "c"), "Не учтена гамма: канал берётся линейно."),
          (CR_SOL.replace("(Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)", "(a + 0.05) / (b + 0.05)"), "Нет упорядочивания: при светлом втором цвете получается меньше единицы."),
          (CR_SOL.replace("Math.max(a, b) + 0.05", "Math.max(a, b)").replace("Math.min(a, b) + 0.05", "Math.min(a, b)"), "Забыта добавка 0.05: для чёрного получается деление на ноль."),
          (CR_SOL.replace("0.2126 * channel(n >> 16) + 0.7152 * channel((n >> 8) & 255)", "0.7152 * channel(n >> 16) + 0.2126 * channel((n >> 8) & 255)"), "Коэффициенты красного и зелёного перепутаны.")],
         starter=CR_START)

for a in (a1, a2, a3, a4, a5):
    web_verify("html", a)

skills = {"web.animation": "Переходы и анимации CSS", "web.a11y": "Доступность: alt, подписи, фокус", "web.contrast": "Контрастность и настройки пользователя"}
write_lesson("web-06-animation-a11y", "Анимации и доступность",
             "Делать плавные анимации с учётом настроек пользователя и делать страницу доступной для всех.",
             list(skills), ["web-05-grid-responsive"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "transition записан в :hover", "fix": "Пишите transition в обычное состояние, тогда плавны оба направления."},
              {"mistake": "Картинка без alt и поле без подписи", "fix": "Описывайте содержательные картинки и подписывайте поля через label."},
              {"mistake": "outline: none без замены", "fix": "Замените контур своим через :focus-visible."},
              {"mistake": "Анимация игнорирует prefers-reduced-motion", "fix": "Отключайте её в медиазапросе для уменьшенного движения."}],
             min_pass=4, pack="web-basics", runner="html")
merge_pack("web-basics", "web-06-animation-a11y", skills)

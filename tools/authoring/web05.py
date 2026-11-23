"""Урок веб 5: CSS Grid и адаптивная вёрстка."""
from webib import *


def preview(code):
    return "Предпросмотр страницы:\n" + page_text(code)


ITEMS = "".join(f"    <div>{i}</div>\n" for i in range(1, 7))
GBODY = '  <div class="gallery">\n' + ITEMS + '  </div>'


def gal(css, head=""):
    return page(GBODY, style(css) + head)


def val(code, expr):
    return measure(code, expr)


COLS = "getComputedStyle(document.querySelector('.gallery')).gridTemplateColumns"
LEFTS = "[...document.querySelectorAll('.gallery > div')].map(d => Math.round(d.getBoundingClientRect().left))"
NCOLS = "new Set(" + LEFTS + ").size"

G1 = """.gallery {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.gallery div {
  background: #b2dfdb;
  padding: 8px;
}"""
S_G1 = gal(G1)
g1_cols = val(S_G1, COLS)
g1_tops = val(S_G1, "JSON.stringify([...document.querySelectorAll('.gallery > div')].map(d => Math.round(d.getBoundingClientRect().top)))")
assert g1_cols == "108px 108px 108px", g1_cols
assert len(set(eval(g1_tops))) == 2, g1_tops

G2 = """.gallery {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  gap: 12px;
}
.gallery div { background: #b2dfdb; }"""
S_G2 = gal(G2)
g2_cols = val(S_G2, COLS)
assert g2_cols == "80px 160px 80px", g2_cols

SPAN_BODY = '  <div class="page">\n    <div class="top">Шапка</div>\n' + "".join(f'    <div class="card">{i}</div>\n' for i in range(1, 5)) + '  </div>'
SPAN_CSS = """.page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.top {
  grid-column: 1 / -1;
  background: #ffe082;
}
.card { background: #b2dfdb; }"""
S_SPAN = page(SPAN_BODY, style(SPAN_CSS))
span_w = val(S_SPAN, "Math.round(document.querySelector('.top').getBoundingClientRect().width) + ' ' + Math.round(document.querySelector('.card').getBoundingClientRect().width)")
assert span_w == "344 168", span_w

G3 = """.gallery {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
@media (min-width: 600px) {
  .gallery {
    grid-template-columns: repeat(3, 1fr);
  }
}"""
S_G3 = gal(G3)
g3_cols = val(S_G3, COLS)
g3_match = val(S_G3, "matchMedia('(min-width: 600px)').matches")
assert g3_cols == "344px" and g3_match == "False", (g3_cols, g3_match)

G4 = """.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 8px;
}"""
S_G4 = gal(G4)
g4_n = val(S_G4, NCOLS)
assert g4_n == "3", g4_n

use_file("index.html")
scenes = [
    scene("intro", "Две оси вместо одной", """
      Flexbox, который мы изучили, раскладывает элементы вдоль одной линии: в ряд или в столбик. А если нужна таблица из
      карточек, то есть строки и колонки одновременно? Для этого в CSS есть сетка, Grid. Она двумерная: вы задаёте колонки,
      а строки появляются по мере заполнения. Сетка выручает в галереях, каталогах товаров и каркасе страницы. А ещё сегодня
      разберём адаптивность: как сделать так, чтобы одна и та же страница хорошо выглядела и на телефоне, и на планшете, и
      на большом мониторе. Большинство людей открывают сайты именно с телефона, поэтому адаптивность давно не роскошь, а
      обязательная часть вёрстки. А ещё это отличный повод сравнить подходы: где достаточно сетки, а где нужны особые правила.""",
          [NOTE("**Flexbox** — одна линия · **Grid** — строки и колонки · **адаптивность** — один код для любого экрана", at="Для этого в CSS")]),
    scene("grid", "Колонки и промежутки", """
      Включаем сетку так же, как flexbox: родителю пишем display grid. Колонки задаёт свойство grid-template-columns. Запись
      repeat три, один fr означает три колонки одинаковой ширины. Единица fr, от слова fraction, это доля свободного места.
      Свойство gap задаёт промежуток между ячейками, и по строкам, и по колонкам. Шесть элементов сами выстроятся в две строки
      по три. Запускаем и измеряем. Ширина экрана триста шестьдесят, минус по восемь пикселей полей body с каждой стороны,
      остаётся триста сорок четыре. Вычтем два промежутка по десять и разделим на три: получится ровно сто восемь пикселей
      на колонку. Если вы поменяете gap, ширина колонки изменится сама: сетка всё пересчитает. Вручную подгонять проценты, как
      раньше, больше не нужно, и это одно из главных удобств сетки.""",
          [CLEAR(), T(S_G1, at="Включаем сетку"), HL([8], at="родителю пишем"), HL([9], at="Колонки задаёт"), HL([10], at="Свойство gap"),
           RUN(at="Запускаем и измеряем"), OUT(preview(S_G1), at="Запускаем и измеряем"),
           NOTE("Измерили: колонки — **" + g1_cols + "**, элементы выстроились в **2** ряда по 3.", at="Вычтем два")]),
    scene("fr", "Доли не обязаны быть равными", """
      Доли не обязаны быть равными. Запись один fr, два fr, один fr делит свободное место в пропорции один к двум к одному.
      Важно, что промежутки вычитаются раньше: сначала из ширины убираем gap, а остаток делим на доли. Для контейнера в триста
      сорок четыре пикселя и двух промежутков по двенадцать остаётся триста двадцать, а долей всего четыре, значит одна доля
      равна восьмидесяти. Колонки получаются в восемьдесят, сто шестьдесят и восемьдесят пикселей. Именно эту арифметику вы
      проверите в первом задании. Заметьте, что доли делят только свободное место. Если в колонке есть содержимое, которое
      не сжимается, например длинное слово, она может оказаться шире своей доли, и это стоит помнить при отладке.""",
          [CLEAR(), T(S_G2, at="Доли не обязаны"), HL([9], at="Запись один fr"), HL([10], at="Важно"), RUN(at="Колонки получаются"),
           OUT(preview(S_G2), at="Колонки получаются"), NOTE("Измерили: колонки — **" + g2_cols + "**.", at="Колонки получаются")]),
    scene("span", "Ячейка на несколько колонок", """
      Иногда элемент должен занять сразу несколько колонок, например шапка на всю ширину. Для этого у самого элемента пишем
      grid-column. Запись «один слэш минус один» значит: от первой линии сетки до последней. Минус один всегда обозначает
      последнюю линию, поэтому шапка растянется на все колонки, сколько бы их ни было. Можно и так: span два, то есть занять
      две колонки подряд. Запускаем: ширина шапки равна ширине всего контейнера, а карточки ниже стоят в две колонки. Так же делают боковые панели: меню занимает одну колонку,
      а основное содержимое растягивается на остальные.""",
          [CLEAR(), T(S_SPAN, at="Иногда элемент"), HL([13], at="grid-column"), HL([13], at="Минус один"), RUN(at="Запускаем"),
           OUT(preview(S_SPAN), at="Запускаем"), NOTE("Измерили: ширина шапки и карточки — **" + span_w.replace(" ", " px, ") + " px**.", at="ширина шапки")]),
    scene("viewport", "Экраны бывают разные", """
      Теперь адаптивность. Экраны бывают разные: телефон в триста шестьдесят пикселей, планшет, большой монитор. Чтобы страница
      везде выглядела хорошо, нужны три вещи. Первая: в head должна стоять строка meta viewport с шириной устройства. Без неё
      мобильный браузер рисует страницу так, будто экран шире, около девятисот восьмидесяти пикселей, и затем уменьшает её, из-за
      чего текст становится крошечным. Вторая: размеры задаются в гибких единицах: проценты, fr, rem, а не фиксированными
      пикселями. Третья: картинкам задают max-width сто процентов и height auto, чтобы они не вылезали за экран и не
      искажались. Если все три правила соблюдены, страница сама подстроится почти под любой экран, и
      медиазапросы понадобятся лишь для тонкой настройки.""",
          [NOTE("`<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">` — в `head` каждой страницы", at="Первая"),
           NOTE("Гибкие единицы: `%`, `fr`, `rem` · Картинки: `img { max-width: 100%; height: auto; }`", at="Вторая")]),
    scene("media", "Медиазапросы: сначала телефон", """
      Иногда одних гибких единиц мало: на широком экране хочется другую раскладку. Для этого служат медиазапросы. Правило с
      собакой media и условием действует, только когда условие выполнено. Профессионалы пишут сначала для телефона, а потом
      улучшают для больших экранов. Этот подход называется mobile-first, «сначала мобильные». Базовые правила описывают одну
      колонку, а внутри медиазапроса с min-width шестьсот пикселей включаются три колонки. Слово min значит «от этой ширины и
      шире». У нас экран узкий, поэтому запрос не сработает: проверка matchMedia возвращает ложь, и колонка остаётся одна шириной
      триста сорок четыре. На планшете же условие выполнится, и колонок станет три. Кода при таком подходе меньше, потому что
      мобильная раскладка служит основой, а широкая её лишь дополняет. Порог выбирают не по названиям устройств, а по тому месту, где
      макет начинает выглядеть плохо: растяните окно и посмотрите, когда колонки становятся слишком узкими.""",
          [CLEAR(), T(S_G3, at="Иногда одних"), HL([9], at="Базовые правила"), HL([12, 13, 14, 15, 16], at="внутри медиазапроса"), HL([14], at="Слово min"),
           RUN(at="У нас экран"), OUT(preview(S_G3), at="У нас экран"),
           NOTE("Измерили: колонка — **" + g3_cols + "**, `matchMedia('(min-width: 600px)').matches` — **" + g3_match.lower() + "**.", at="проверка matchMedia")]),
    scene("autofit", "Колонки подбираются сами", """
      Есть способ обойтись почти без медиазапросов. Запись repeat, auto-fit, minmax сто пикселей, один fr говорит: делай столько
      колонок, сколько поместится, если каждая не уже ста пикселей, а лишнее место раздай поровну. На узком экране колонок
      получится меньше, на широком больше, и всё само. Это очень удобно для каталогов и галерей, а кода получается совсем немного. Разница между
      auto-fit и auto-fill заметна только когда карточек мало: auto-fit схлопывает пустые колонки и растягивает карточки. Запускаем: колонок
      получилось три.""",
          [CLEAR(), T(S_G4, at="Есть способ"), HL([9], at="Запись repeat"), RUN(at="Запускаем"), OUT(preview(S_G4), at="Запускаем"),
           NOTE("Измерили: колонок на экране 360 px — **" + g4_n + "**.", at="получилось три")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: забыть display grid у родителя, тогда grid-template-columns ничего не делает. Вторая: не
      поставить meta viewport, и страница на телефоне выглядит как уменьшенная копия настольной. Третья: задать картинке
      max-width, но оставить фиксированную высоту, и картинка сплющивается. Четвёртая: написать медиазапрос с max-width вместо
      min-width и получить на телефоне раскладку для большого экрана.""",
          [NOTE("Ошибка 1: нет `display: grid` у родителя.", at="Первая"), NOTE("Ошибка 2: нет `meta viewport`.", at="Вторая"),
           NOTE("Ошибка 3: у картинки нет `height: auto`.", at="Третья"), NOTE("Ошибка 4: `max-width` вместо `min-width`.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. Grid раскладывает элементы по строкам и колонкам: display grid у родителя, колонки через
      grid-template-columns, промежутки через gap, доли через fr. Элемент может занять несколько колонок через grid-column.
      Для адаптивности нужны meta viewport, гибкие единицы, картинки с max-width сто процентов и медиазапросы в стиле
      mobile-first. А repeat с auto-fit и minmax подбирает число колонок сам. В заданиях вы посчитаете ширину колонки, растянете
      шапку, напишете медиазапрос, поправите картинку и соберёте самоподбирающуюся сетку.""",
          [NOTE("`display: grid` · `grid-template-columns` · `gap` · `fr` · `grid-column` · `@media (min-width)` · `auto-fit` · `meta viewport`", at="Подведём итог")]),
]
use_file(None)

notes = """
# CSS Grid и адаптивная вёрстка

```css
.gallery {
  display: grid;                              /* включаем сетку у родителя */
  grid-template-columns: repeat(3, 1fr);      /* три равные колонки */
  gap: 10px;                                  /* промежуток */
}
.top { grid-column: 1 / -1; }                 /* на все колонки */

/* mobile-first: база — для телефона */
@media (min-width: 600px) {
  .gallery { grid-template-columns: repeat(3, 1fr); }
}

/* колонки подбираются сами */
.catalog { grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); }

img { max-width: 100%; height: auto; }
```

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

| Что | Как |
|---|---|
| колонки | `grid-template-columns: 1fr 2fr 1fr` — доли свободного места |
| промежуток | `gap` вычитается из ширины до деления на доли |
| на всю ширину | `grid-column: 1 / -1` |
| от ширины и шире | `@media (min-width: ...)` |

- Начинайте с раскладки для телефона, а широкие экраны добавляйте медиазапросами.
- Без `meta viewport` телефон показывает уменьшенную настольную страницу.
- Картинке нужны `max-width: 100%` **и** `height: auto`, иначе она исказится.
"""

# --- Задание 1: предсказать ---
CODE1 = gal(G2)
a1 = asg("a1-predict", "predict", "Какая ширина у средней колонки?",
         "Сетка `1fr 2fr 1fr` с промежутком `12px` между колонками стоит на странице шириной **360px** (у `body` стандартные поля `8px`, то есть сетка занимает 344px). Какова ширина **средней** колонки в пикселях? Ответьте числом.",
         "Посчитать доли fr с учётом промежутков.", "—", "Одно число.", [],
         hints("Сначала найдите ширину сетки: 360 минус поля body по 8px с каждой стороны.", "Промежутки (gap) вычитаются из ширины до деления на доли.", "Между тремя колонками два промежутка по 12px.",
               "Свободное место: 344 − 24 = 320. Долей всего 1 + 2 + 1 = 4.", "Одна доля — 80px, а средняя колонка занимает две доли."),
         {"kind": "answer", "expected_answer": "160"}, "160",
         "(344 − 2·12) / 4 = 80px на одну долю; средняя колонка — две доли: 160px.", ["Верное число."],
         [("172", "Промежутки не вычтены: 344 / 4 · 2."), ("107", "Колонки приняты за равные: (344 − 24) / 3."), ("80", "Это ширина крайней колонки, а не средней.")],
         code=CODE1)

# --- Задание 2: шапка на всю ширину ---
SPAN_BASE = """.page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.card { background: #b2dfdb; }"""
S2 = page(SPAN_BODY, style(SPAN_BASE + "\n.top {\n  grid-column: 1 / -1;\n  background: #ffe082;\n}"))
Q = "document.querySelector"
t2 = {"kind": "web", "lang": "html", "cases": [
    {"id": "wide", "expr": "Math.round(" + Q + "('.top').getBoundingClientRect().width) === Math.round(" + Q + "('.page').getBoundingClientRect().width)", "expected": True},
    {"id": "cols", "expr": "new Set([...document.querySelectorAll('.card')].map(c => Math.round(c.getBoundingClientRect().left))).size", "expected": 2},
    {"id": "below", "expr": "Math.round(" + Q + "('.top').getBoundingClientRect().bottom) <= Math.round(" + Q + "('.card').getBoundingClientRect().top)", "expected": True},
    {"id": "five", "hidden": True, "expr": "document.querySelectorAll('.page > div').length", "expected": 5, "hint": "Разметку менять не нужно"},
]}
a2 = asg("a2-span", "write", "Шапка на всю ширину",
         "В сетке из **двух колонок** первый элемент `.top` («Шапка») должен занять **всю ширину** сетки, а четыре карточки `.card` — стоять под ним в две колонки. Разметку и правила `.page`, `.card` не меняйте: добавьте правило для `.top` (цвет фона любой).",
         "Растянуть элемент на все колонки сетки.", "Сетка с шапкой и четырьмя карточками.", "Шапка на всю ширину, карточки под ней в две колонки.",
         ["Правило для .top добавляется в style."],
         hints("Растягивать нужно сам элемент, а не его родителя.", "Положение элемента по колонкам задаёт свойство grid-column.", "Запись «от первой линии до последней»: 1 / -1.", "Минус один всегда означает последнюю линию сетки.",
               ".top { grid-column: 1 / -1; }"),
         t2, S2, "grid-column: 1 / -1 тянет элемент от первой линии сетки до последней, независимо от числа колонок.",
         ["Шапка на всю ширину.", "Карточки в две колонки под шапкой."],
         [(page(SPAN_BODY, style(SPAN_BASE + "\n.top {\n  width: 100%;\n  background: #ffe082;\n}")), "width: 100% относится к ячейке сетки, а ячейка — одна колонка."),
          (page(SPAN_BODY, style(SPAN_BASE + "\n.top {\n  grid-column: 1;\n  background: #ffe082;\n}")), "Элемент остаётся в первой колонке."),
          (page(SPAN_BODY, style(SPAN_BASE.replace("1fr 1fr", "1fr") + "\n.top {\n  background: #ffe082;\n}")), "Сетка превращена в одну колонку: карточки не стоят в две."),
          (page(SPAN_BODY, style(SPAN_BASE + "\n.top {\n  grid-row: 1 / -1;\n  background: #ffe082;\n}")), "grid-row управляет строками, а не колонками.")],
         starter=page(SPAN_BODY, style(SPAN_BASE)))

# --- Задание 3: медиазапрос ---
MQ = ("(() => { const rules = [...document.styleSheets].flatMap(s => [...s.cssRules]).filter(r => r.media && /^\\(min-width:\\s*600px\\)$/.test((r.conditionText || r.media.mediaText).trim())); "
      "return rules.some(r => [...r.cssRules].some(x => { const v = x.style && x.style.gridTemplateColumns; if (!v) return false; const m = v.match(/^repeat\\(\\s*3\\s*,\\s*(.+)\\)$/); "
      "if (m) return true; const p = v.trim().split(/\\s+/); return p.length === 3 && p.every(q => q === p[0]); })); })()")
BASE3 = ".gallery {\n  display: grid;\n  gap: 8px;\n}\n.gallery div { background: #b2dfdb; }"
S3 = gal(BASE3 + "\n@media (min-width: 600px) {\n  .gallery {\n    grid-template-columns: repeat(3, 1fr);\n  }\n}")
t3 = {"kind": "web", "lang": "html", "cases": [
    {"id": "phone", "expr": NCOLS, "expected": 1},
    {"id": "media", "expr": MQ, "expected": True},
    {"id": "six", "hidden": True, "expr": "document.querySelectorAll('.gallery > div').length", "expected": 6, "hint": "Разметку менять не нужно"},
]}
a3 = asg("a3-media", "write", "Три колонки на широком экране",
         "Сейчас галерея — сетка без заданных колонок. Сделайте раскладку **mobile-first**: на узком экране (телефон, 360px) элементы стоят в **одну колонку**, а на экранах шириной **от 600px** — в **три равные колонки**. Разметку и правило `.gallery` не меняйте — добавьте медиазапрос.",
         "Написать адаптивную раскладку в стиле mobile-first.", "Страница с галереей из шести элементов.", "Одна колонка на телефоне, три — от 600px.",
         ["Используйте min-width: 600px."],
         hints("Базовая раскладка уже подходит для телефона: одна колонка.", "Для широких экранов нужен медиазапрос: @media (...) { ... }.", "Условие «от 600px и шире» записывают через min-width.", "Внутри медиазапроса пишут правило для .gallery с колонками.",
               "@media (min-width: 600px) { .gallery { grid-template-columns: repeat(3, 1fr); } }"),
         t3, S3, "Базовые правила описывают телефон, а медиазапрос с min-width добавляет колонки только на широких экранах.",
         ["Одна колонка на узком экране.", "Три колонки от 600px."],
         [(gal(BASE3 + "\n.gallery {\n  grid-template-columns: repeat(3, 1fr);\n}"), "Три колонки заданы всегда, а не только на широких экранах."),
          (gal(BASE3 + "\n@media (max-width: 600px) {\n  .gallery {\n    grid-template-columns: repeat(3, 1fr);\n  }\n}"), "max-width включает три колонки на узких экранах — наоборот."),
          (gal(BASE3 + "\n@media (min-width: 900px) {\n  .gallery {\n    grid-template-columns: repeat(3, 1fr);\n  }\n}"), "Порог 900px, а нужен 600px."),
          (gal(BASE3 + "\n@media (min-width: 600px) {\n  .gallery {\n    grid-template-columns: 1fr 1fr;\n  }\n}"), "Две колонки вместо трёх.")],
         starter=gal(BASE3))

# --- Задание 4: картинка и viewport ---
IMG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='400'%3E%3Crect width='800' height='400' fill='%2380cbc4'/%3E%3C/svg%3E"
BODY4 = f'  <h1>Фото</h1>\n  <img src="{IMG}" alt="Фото" width="800" height="400">'
S4 = page(BODY4, style("img {\n  max-width: 100%;\n  height: auto;\n}") + '  <meta name="viewport" content="width=device-width, initial-scale=1">\n')
t4 = {"kind": "web", "lang": "html", "cases": [
    {"id": "noscroll", "expr": "document.documentElement.scrollWidth <= innerWidth", "expected": True},
    {"id": "fits", "expr": "Math.round(" + Q + "('img').getBoundingClientRect().right) <= innerWidth", "expected": True},
    {"id": "ratio", "expr": "Math.abs(" + Q + "('img').offsetWidth / " + Q + "('img').offsetHeight - 2) < 0.02", "expected": True},
    {"id": "meta", "expr": "((" + Q + "('meta[name=\"viewport\"]') || {}).content || '').replace(/\\s/g, '').includes('width=device-width')", "expected": True},
    {"id": "one", "hidden": True, "expr": "document.querySelectorAll('img').length", "expected": 1, "hint": "Картинку нужно оставить"},
]}
VP = '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
a4 = asg("a4-image", "fix", "Картинка вылезает за экран",
         "Картинка шириной 800px не помещается на экран телефона: страница прокручивается вбок. Исправьте страницу, чтобы картинка **умещалась по ширине** и **сохраняла пропорции** (2 : 1), а в `head` была строка `meta viewport` с `width=device-width`. Тег `img` менять не нужно.",
         "Сделать картинку гибкой и подключить viewport.", "Страница с широкой картинкой.", "Картинка по ширине экрана без искажений, meta viewport на месте.",
         ["Размеры в атрибутах img не меняйте."],
         hints("Картинка шире экрана: страница получила горизонтальную прокрутку.", "Ограничьте ширину: max-width: 100%.", "У тега есть атрибут height=400: без height: auto картинка сплющится.", "Для телефона в head нужна строка meta с name=\"viewport\".",
               "img { max-width: 100%; height: auto; } и <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">."),
         t4, S4, "max-width: 100% не даёт картинке выйти за контейнер, height: auto сохраняет пропорции, а meta viewport говорит телефону, что страницу не нужно уменьшать.",
         ["Нет горизонтальной прокрутки.", "Пропорции сохранены.", "Строка viewport на месте."],
         [(page(BODY4, style("img {\n  max-width: 100%;\n}") + VP), "Высота осталась 400px: картинка сплющена."),
          (page(BODY4, style("img {\n  max-width: 100%;\n  height: auto;\n}")), "Нет строки meta viewport."),
          (page(BODY4, style("body {\n  overflow-x: hidden;\n}") + VP), "Прокрутка спрятана, а картинка по-прежнему обрезана за экраном."),
          (page(BODY4, style("img {\n  width: 100%;\n  height: 400px;\n}") + VP), "Пропорции не сохраняются: высота зафиксирована.")],
         starter=page(BODY4))

# --- Задание 5: auto-fit ---
BASE5 = ".gallery {\n  display: grid;\n  gap: 10px;\n}\n.gallery div { background: #b2dfdb; }"
S5 = gal(BASE5.replace("  gap: 10px;", "  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));\n  gap: 10px;"))
SRC5 = "/repeat\\(\\s*auto-(fit|fill)\\s*,\\s*minmax\\(\\s*80px\\s*,\\s*1fr\\s*\\)\\s*\\)/.test([...document.styleSheets].flatMap(s => [...s.cssRules]).map(r => r.cssText).join(' '))"
t5 = {"kind": "web", "lang": "html", "cases": [
    {"id": "cols", "expr": NCOLS, "expected": 3},
    {"id": "fill", "expr": "Math.round([...document.querySelectorAll('.gallery > div')][2].getBoundingClientRect().right) === innerWidth - 8", "expected": True},
    {"id": "gap", "expr": "(() => { const r = [...document.querySelectorAll('.gallery > div')].map(d => d.getBoundingClientRect()); return Math.round(r[1].left - r[0].right); })()", "expected": 10},
    {"id": "auto", "expr": SRC5, "expected": True},
]}
a5 = asg("a5-autofit", "write", "Каталог с самоподбором колонок",
         "Галерея из шести карточек должна подбирать число колонок сама: каждая колонка **не уже 80px**, а оставшееся место делится между колонками поровну. Промежуток уже задан. Добавьте в `.gallery` свойство колонок на основе `repeat`, `auto-fit` и `minmax` — **без медиазапросов**.",
         "Собрать сетку, число колонок которой зависит от ширины экрана.", "Страница с галереей.", "Три колонки на экране 360px, подбор — автоматический.",
         ["Без медиазапросов.", "Минимальная ширина колонки — 80px."],
         hints("Число колонок должно подбираться по ширине экрана, а не задаваться числом.", "Для этого в repeat вместо числа ставят слово auto-fit.", "Ширину колонки задаёт minmax(минимум, максимум).", "Минимум — 80px, максимум — 1fr: колонки делят остаток поровну.",
               "grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));"),
         t5, S5, "repeat(auto-fit, minmax(80px, 1fr)) создаёт столько колонок не уже 80px, сколько помещается, и растягивает их на всю ширину.",
         ["Колонки подбираются сами.", "Занимают всю ширину.", "Промежуток 10px."],
         [(gal(BASE5.replace("  gap: 10px;", "  grid-template-columns: repeat(3, 1fr);\n  gap: 10px;")), "Три колонки заданы жёстко: число не зависит от ширины экрана."),
          (gal(BASE5.replace("  gap: 10px;", "  grid-template-columns: repeat(auto-fit, 80px);\n  gap: 10px;")), "Колонки по 80px не растягиваются на всю ширину."),
          (gal(BASE5.replace("  gap: 10px;", "  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));\n  gap: 10px;")), "Минимум 150px: получается две колонки вместо трёх."),
          (gal(BASE5.replace("  gap: 10px;", "  grid-template-columns: repeat(auto-fit, minmax(80px, 80px));\n  gap: 10px;")), "Максимум тоже 80px: колонки не растягиваются.")],
         starter=gal(BASE5))

for a in (a2, a3, a4, a5):
    web_verify("html", a)

skills = {"web.grid": "CSS Grid: колонки, fr, gap", "web.responsive": "Адаптивность: viewport, гибкие единицы, картинки", "web.media": "Медиазапросы и mobile-first"}
write_lesson("web-05-grid-responsive", "CSS Grid и адаптивная вёрстка",
             "Раскладывать элементы сеткой и делать страницу, которая хорошо выглядит на любом экране.",
             list(skills), ["web-04-forms"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Нет display: grid у родителя", "fix": "grid-template-columns и gap работают только у элемента с display: grid."},
              {"mistake": "Нет meta viewport", "fix": "Добавьте в head строку с width=device-width, иначе телефон уменьшит страницу."},
              {"mistake": "У картинки max-width без height: auto", "fix": "Пишите оба свойства, иначе пропорции нарушатся."},
              {"mistake": "Медиазапрос max-width вместо min-width", "fix": "Mobile-first: базовые правила для телефона, а min-width добавляет широкие раскладки."}],
             min_pass=4, pack="web-basics", runner="html")
merge_pack("web-basics", "web-05-grid-responsive", skills)

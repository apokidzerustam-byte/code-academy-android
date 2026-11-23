"""Урок веб 3: CSS — блочная модель и раскладка flexbox."""
from webib import *


def preview(code):
    return "Предпросмотр страницы:\n" + page_text(code)


BOX_CSS = """.card {
  width: 100px;
  padding: 10px;
  border: 5px solid teal;
  margin: 20px;
  background: lightyellow;
}"""
BOX = page('  <div class="card" id="b">Блок</div>', style(BOX_CSS))
w_off = measure(BOX, "document.getElementById('b').offsetWidth")
w_out = measure(BOX, "document.getElementById('b').offsetWidth + 2 * 20")
assert (w_off, w_out) == ("130", "170"), (w_off, w_out)

ROW_CSS = """.menu {
  display: flex;
  gap: 12px;
}
.menu a {
  padding: 6px 10px;
  background: #e0f2f1;
}"""
ROW_BODY = '  <nav class="menu">\n    <a href="#">Главная</a>\n    <a href="#">Курсы</a>\n    <a href="#">Контакты</a>\n  </nav>'
ROW = page(ROW_BODY, style(ROW_CSS))
NOFLEX = page(ROW_BODY, style(ROW_CSS.replace("  display: flex;\n", "")))
TOPS = "JSON.stringify([...document.querySelectorAll('.menu a')].map(a => Math.round(a.getBoundingClientRect().top)))"
tops_flex = measure(ROW, TOPS)
tops_block = measure(NOFLEX, TOPS)
assert len(set(eval(tops_flex))) == 1, tops_flex
assert len(set(eval(tops_block))) == 1, tops_block  # ссылки строчные: в одной строке и без flex — используем блочные
LINKS_BLOCK_CSS = ".menu a { display: block; }"
STACK = page(ROW_BODY, style(ROW_CSS.replace("  display: flex;\n", "").replace(".menu a {", ".menu a {\n  display: block;")))
tops_stack = measure(STACK, TOPS)
assert len(set(eval(tops_stack))) == 3, tops_stack

CENTER_CSS = """body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
.box { width: 120px; height: 60px; background: teal; }"""
CENTER = page('  <div class="box" id="c"></div>', style(CENTER_CSS))
CENTER_POS = "(() => { const r = document.getElementById('c').getBoundingClientRect(); return Math.round(r.left + r.width / 2) + ',' + Math.round(r.top + r.height / 2); })()"
center_pos = measure(CENTER, CENTER_POS)
assert center_pos == "180,320", center_pos

use_file("index.html")
scenes = [
    scene("intro", "Всё на странице — коробки", """
      Если разглядеть любую страницу, окажется, что она сложена из прямоугольных коробок: заголовок — коробка, абзац —
      коробка, кнопка — тоже. Чтобы красиво расставить их, нужно понять две вещи. Как устроена одна коробка: у неё есть
      отступы и рамка. И как расположить несколько коробок рядом друг с другом. Сегодня разберём обе.""",
          [NOTE("Каждый элемент — **прямоугольная коробка**. CSS управляет её размерами, отступами и положением.", at="Чтобы красиво")]),
    scene("box", "Блочная модель", """
      У коробки четыре слоя. В центре содержимое, и его размер задаёт width. Вокруг него padding — внутренний отступ.
      Дальше идёт рамка, border, и снаружи margin — внешний отступ, который отодвигает соседей. Возьмём блок шириной сто
      пикселей, с отступом десять, рамкой пять и внешним отступом двадцать. Запускаем и измеряем. Полная ширина с рамкой
      получилась сто тридцать: сто плюс два раза по десять плюс два раза по пять. Margin в неё не входит, он только
      раздвигает соседей.""",
          [CLEAR(), T(BOX, at="У коробки"), HL([7, 8, 9, 10, 11, 12], at="В центре"), HL([8], at="width"), HL([9], at="padding"), HL([10], at="рамка"), HL([11], at="margin"),
           RUN(at="Запускаем"), OUT(preview(BOX), at="Полная ширина"), NOTE("Измерили в браузере: ширина блока с рамкой — **" + w_off + " px**, вместе с margin — **" + w_out + " px**.", at="Полная ширина")]),
    scene("flex", "Flexbox: ряд из элементов", """
      Теперь расположим несколько элементов в ряд. Возьмём меню из трёх ссылок. Достаточно одному родителю, элементу nav,
      написать display: flex, и его дети выстраиваются в строку. Свойство gap задаёт промежуток между ними. Запускаем:
      вертикальные координаты всех трёх ссылок одинаковы, они стоят в одном ряду.""",
          [CLEAR(), T(ROW, at="Теперь расположим"), HL([8], at="display"), HL([9], at="gap"), RUN(at="Запускаем"),
           OUT(preview(ROW), at="вертикальные"), NOTE("Измерили: вертикальные координаты трёх ссылок — **" + tops_flex + "**, все одинаковые.", at="вертикальные")]),
    scene("justify", "Выравнивание: justify и align", """
      Flexbox умеет выравнивать. Свойство justify-content распределяет элементы вдоль ряда: к началу, к центру, по краям или с
      равными промежутками. А align-items выравнивает их поперёк ряда. Самый частый приём: поставить блок ровно по центру страницы.
      Родителю, то есть body, даём display flex, justify-content center и align-items center, а высоту делаем во весь
      экран, min-height сто vh. Запускаем: центр блока находится ровно посередине экрана шириной триста шестьдесят и
      высотой шестьсот сорок пикселей.""",
          [CLEAR(), T(CENTER, at="Flexbox умеет"), HL([11], at="justify-content"), HL([12], at="align-items"), HL([9], at="высоту"),
           RUN(at="Запускаем"), OUT(preview(CENTER), at="центр блока"), NOTE("Измерили: центр блока — точка **" + center_pos + "**, а центр экрана — (180, 320).", at="центр блока")]),
    scene("stack", "Забыли display: flex", """
      Самая частая ошибка новичка: написать gap или justify-content, но забыть display flex у родителя. Тогда свойства просто
      не работают: элементы остаются обычными. Если ссылки стоят в столбик, хотя вы ждали ряд, сначала проверьте, есть ли
      display flex у их родителя. Здесь для наглядности ссылки сделаны блочными: запускаем, и координаты у всех разные.""",
          [CLEAR(), T(STACK, at="Самая частая"), RUN(at="Здесь для наглядности"), OUT(preview(STACK), at="координаты"), NOTE("Измерили: вертикальные координаты — **" + tops_stack + "**, все разные: ссылки в столбик.", at="координаты")]),
    scene("summary", "Итог", """
      Подведём итог. У каждого элемента есть содержимое, внутренний отступ padding, рамка border и внешний отступ margin.
      Чтобы выстроить элементы в ряд, дайте родителю display flex, а промежуток задайте через gap. justify-content
      выравнивает вдоль ряда, align-items поперёк. Если свойства не действуют, проверьте display flex у родителя.""",
          [NOTE("`display: flex` — у **родителя** · `gap` · `justify-content` · `align-items`", at="Чтобы выстроить")]),
]
use_file(None)

notes = """
# CSS: блочная модель и flexbox

```css
.card {
  width: 100px;          /* содержимое */
  padding: 10px;         /* внутренний отступ */
  border: 5px solid teal;
  margin: 20px;          /* внешний отступ */
}
/* ширина с рамкой = 100 + 2·10 + 2·5 = 130 (margin не входит) */

.menu {
  display: flex;         /* дети — в ряд */
  gap: 12px;
  justify-content: space-between;   /* вдоль ряда */
  align-items: center;              /* поперёк */
}
```

| Свойство | Значения |
|---|---|
| `justify-content` | `flex-start`, `center`, `flex-end`, `space-between`, `space-around` |
| `align-items` | `stretch`, `flex-start`, `center`, `flex-end` |
| `flex-direction` | `row` (по умолчанию), `column` |

- `display: flex` пишут **родителю**, а не детям.
- Центр по экрану: `body { display:flex; justify-content:center; align-items:center; min-height:100vh; }`.
- `box-sizing: border-box` — ширина включает padding и рамку.
- Если элементы не встают в ряд, проверьте `display: flex` у родителя.
"""

tp = lambda sel, prop: computed(sel, prop)

# --- Задание 1: блочная модель ---
BODY1 = '  <div class="card">Карточка</div>'
S1 = page(BODY1, style(".card {\n  padding: 12px;\n  border: 3px solid black;\n  margin: 16px;\n}"))
t1 = {"kind": "web", "lang": "html", "cases": [
    {"id": "pad", "expr": tp(".card", "paddingTop") + " + ' ' + " + tp(".card", "paddingLeft"), "expected": "12px 12px"},
    {"id": "border", "expr": tp(".card", "borderTopWidth") + " + ' ' + " + tp(".card", "borderTopStyle"), "expected": "3px solid"},
    {"id": "margin", "expr": tp(".card", "marginBottom"), "expected": "16px"},
    {"id": "all", "hidden": True, "expr": "[...['Top','Right','Bottom','Left']].map(s => getComputedStyle(document.querySelector('.card'))['padding' + s]).join(' ')",
     "expected": "12px 12px 12px 12px", "hint": "Отступ одинаков со всех сторон"},
]}
a1 = asg("a1-box", "write", "Карточка с отступами",
         "Разметку менять не нужно. В `style` оформите элемент с классом `card`:\n\n- внутренний отступ **12px** со всех сторон;\n- рамка толщиной **3px**, сплошная (`solid`), чёрная;\n- внешний отступ **16px**.",
         "Использовать padding, border и margin.", "Страница с одной карточкой.", "Карточка с нужными отступами и рамкой.",
         ["Разметку body не меняйте."],
         hints("Внутренний отступ — padding, внешний — margin.", "Рамка записывается тремя словами: толщина, вид линии, цвет.", "Селектор по классу начинается с точки: .card.", "Значения с единицей измерения: 12px.", "padding: 12px; border: 3px solid black; margin: 16px;"),
         t1, S1, "padding — внутри рамки, margin — снаружи; рамку одним свойством border задают толщина, вид и цвет.",
         ["Три нужных свойства применены."],
         [(page(BODY1, style(".card {\n  margin: 12px;\n  border: 3px solid black;\n  padding: 16px;\n}")), "Отступы перепутаны местами."),
          (page(BODY1, style(".card {\n  padding: 12px;\n  border: 3px;\n  margin: 16px;\n}")), "У рамки не указан вид линии: без solid она не рисуется."),
          (page(BODY1, style("card {\n  padding: 12px;\n  border: 3px solid black;\n  margin: 16px;\n}")), "Селектор без точки ищет тег card.")],
         starter=page(BODY1))

# --- Задание 2: ряд flex ---
BODY2 = '  <nav class="menu">\n    <a href="#">Главная</a>\n    <a href="#">Курсы</a>\n    <a href="#">Контакты</a>\n  </nav>'
BASE2 = "a { display: block; }\n"
S2 = page(BODY2, style(BASE2 + ".menu {\n  display: flex;\n  gap: 20px;\n}"))
ROWCHK = "(() => { const r = [...document.querySelectorAll('.menu a')].map(a => a.getBoundingClientRect()); return r.every(x => Math.round(x.top) === Math.round(r[0].top)) && r[1].left > r[0].right && r[2].left > r[1].right; })()"
GAPCHK = "(() => { const r = [...document.querySelectorAll('.menu a')].map(a => a.getBoundingClientRect()); return Math.round(r[1].left - r[0].right); })()"
t2 = {"kind": "web", "lang": "html", "cases": [
    {"id": "row", "expr": ROWCHK, "expected": True},
    {"id": "gap", "expr": GAPCHK, "expected": 20},
    {"id": "disp", "hidden": True, "expr": tp(".menu", "display"), "expected": "flex", "hint": "Раскладка включается у родителя меню"},
]}
a2 = asg("a2-row", "write", "Меню в ряд",
         "Ссылки меню (`nav` с классом `menu`) сейчас стоят столбиком. Добавьте правило для `.menu`: выстройте ссылки **в ряд** с промежутком **20px** между ними.\n\nПравило `a { display: block; }` не трогайте.",
         "Включать flexbox у родителя и задавать gap.", "Страница с меню из трёх ссылок.", "Три ссылки в ряд, промежуток 20px.",
         ["Правило для a не меняйте.", "Менять нужно родителя, а не ссылки."],
         hints("Элементы в ряд выстраивает Flexbox.", "Раскладку включают у родителя: display: flex.", "Селектор родителя — .menu.", "Промежуток между детьми задаёт gap.", ".menu { display: flex; gap: 20px; }"),
         t2, S2, "display: flex у родителя ставит детей в ряд, gap добавляет промежуток между ними.",
         ["Ссылки в одном ряду.", "Промежуток 20px."],
         [(page(BODY2, style(BASE2 + ".menu {\n  gap: 20px;\n}")), "Нет display: flex: gap без него не работает."),
          (page(BODY2, style(BASE2 + ".menu {\n  display: flex;\n}")), "Ряд есть, но нет промежутка."),
          (page(BODY2, style(BASE2 + ".menu a {\n  display: flex;\n  gap: 20px;\n}")), "Раскладка включена у ссылок, а не у родителя."),
          (page(BODY2, style(BASE2 + ".menu {\n  display: flex;\n  gap: 10px;\n}")), "Промежуток не 20px.")],
         starter=page(BODY2, style(BASE2)))

# --- Задание 3: центр экрана ---
BODY3 = '  <div class="box" id="c"></div>'
BASE3 = "body { margin: 0; min-height: 100vh; }\n.box { width: 120px; height: 60px; background: teal; }\n"
S3 = page(BODY3, style(BASE3 + "body {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}"))
t3 = {"kind": "web", "lang": "html", "cases": [
    {"id": "center", "expr": CENTER_POS, "expected": "180,320"},
    {"id": "size", "hidden": True, "expr": "document.getElementById('c').offsetWidth + 'x' + document.getElementById('c').offsetHeight", "expected": "120x60",
     "hint": "Размер блока менять не нужно"},
]}
a3 = asg("a3-center", "write", "Блок по центру экрана",
         "Квадрат `.box` должен стоять **ровно по центру** экрана — и по горизонтали, и по вертикали. Размеры блока и правило `body` уже заданы; допишите свойства так, чтобы блок оказался по центру.",
         "Центрировать flexbox-ом.", "Страница с блоком.", "Центр блока совпадает с центром экрана.",
         ["Размеры блока не меняйте."],
         hints("Центрирует Flexbox.", "Включить его нужно у родителя блока — у body.", "Выравнивание вдоль ряда — justify-content.", "Выравнивание поперёк — align-items.", "Оба — center, а у body ещё display: flex."),
         t3, S3, "У родителя: display flex включает раскладку, justify-content: center центрирует по горизонтали, align-items: center — по вертикали.",
         ["Блок по центру в обоих направлениях."],
         [(page(BODY3, style(BASE3 + "body {\n  display: flex;\n  justify-content: center;\n}")), "Блок по центру только по горизонтали."),
          (page(BODY3, style(BASE3 + "body {\n  display: flex;\n  align-items: center;\n}")), "Блок по центру только по вертикали."),
          (page(BODY3, style(BASE3 + "body {\n  justify-content: center;\n  align-items: center;\n}")), "Нет display: flex: выравнивание не работает."),
          (page(BODY3, style(BASE3 + ".box {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}")), "Раскладку включили у самого блока, а не у родителя.")],
         starter=page(BODY3, style(BASE3)))

# --- Задание 4: исправить ---
BODY4 = '  <div class="tabs">\n    <span>Один</span>\n    <span>Два</span>\n    <span>Три</span>\n  </div>'
BASE4 = ".tabs span { display: block; }\n"
STARTER4 = page(BODY4, style(BASE4 + ".tabs {\n  justify-content: space-between;\n  align-items: center;\n}"))
S4 = page(BODY4, style(BASE4 + ".tabs {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n}"))
TABCHK = "(() => { const r = [...document.querySelectorAll('.tabs span')].map(a => a.getBoundingClientRect()); return r.every(x => Math.round(x.top) === Math.round(r[0].top)); })()"
SPREAD = "(() => { const r = [...document.querySelectorAll('.tabs span')].map(a => a.getBoundingClientRect()); return Math.round(r[2].right) === innerWidth - 8; })()"
t4 = {"kind": "web", "lang": "html", "cases": [
    {"id": "row", "expr": TABCHK, "expected": True},
    {"id": "spread", "expr": SPREAD, "expected": True},
    {"id": "disp", "hidden": True, "expr": tp(".tabs", "display"), "expected": "flex"},
]}
a4 = asg("a4-fix", "fix", "Вкладки не встают в ряд",
         "Вкладки должны стоять в одном ряду и быть разнесены по краям. Правило написано, но вкладки стоят столбиком. Найдите причину и исправьте.",
         "Находить забытое display: flex.", "Страница с вкладками.", "Три вкладки в одном ряду.",
         ["Лишних свойств не добавляйте."],
         hints("Раскладка в ряд включается не сама собой.", "Посмотрите: чего не хватает в правиле для .tabs?", "justify-content и align-items работают только внутри flex-контейнера.", "Нужно объявить .tabs flex-контейнером.", "display: flex;"),
         t4, S4, "justify-content и align-items — свойства flex-контейнера. Без display: flex у родителя они не действуют.",
         ["Вкладки в ряд."],
         [(page(BODY4, style(BASE4 + ".tabs {\n  display: block;\n  justify-content: space-between;\n}")), "display: block — не раскладка в ряд."),
          (page(BODY4, style(BASE4 + ".tabs span {\n  display: flex;\n}\n.tabs {\n  justify-content: space-between;\n}")), "Flex включён у вкладок, а не у контейнера.")],
         starter=STARTER4)

# --- Задание 5: предсказать ---
CODE5 = page('  <div id="b">Текст</div>', style("#b {\n  width: 80px;\n  padding: 10px;\n  border: 4px solid red;\n  margin: 15px;\n}"))
real5 = measure(CODE5, "document.getElementById('b').offsetWidth")
assert real5 == "108", real5
a5 = asg("a5-predict", "predict", "Какая ширина у блока?",
         "Блок с `width: 80px`, `padding: 10px`, рамкой `4px` и `margin: 15px`. Какова его **полная ширина с рамкой** в пикселях (без внешних отступов)? Ответьте числом.",
         "Считать размеры по блочной модели.", "—", "Одно число.", [],
         hints("Ширина содержимого — 80.", "Padding и рамка есть с обеих сторон — умножьте на два.", "Margin в ширину с рамкой не входит.", "80 + 2·10 + 2·4.", "Ответ: 108."),
         {"kind": "answer", "expected_answer": "108"}, "108",
         "80 (содержимое) + 2·10 (padding) + 2·4 (рамка) = 108. Margin лишь отодвигает соседей.", ["Верное число."],
         [("80", "Это только ширина содержимого."), ("138", "В ширину с рамкой входит margin — а он снаружи."), ("100", "Не учтена рамка.")],
         code=CODE5)

for a in (a1, a2, a3, a4):
    web_verify("html", a)

skills = {"web.boxmodel": "Блочная модель: padding, border, margin", "web.flex": "Flexbox: ряд и выравнивание", "web.layout": "Раскладка страницы"}
write_lesson("web-03-layout", "CSS: блочная модель и flexbox",
             "Понимать размеры блока (padding, рамка, margin) и выстраивать элементы в ряд и по центру через flexbox.",
             list(skills), ["web-01-html-css"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "display: flex у детей, а не у родителя", "fix": "Раскладку включают у контейнера; дети подчиняются сами."},
              {"mistake": "gap или justify-content без display: flex", "fix": "Эти свойства работают только у flex-контейнера."},
              {"mistake": "Рамка без вида линии", "fix": "Пишите border: 3px solid black — без solid рамка не нарисуется."},
              {"mistake": "Ширину считают без padding и рамки", "fix": "Полная ширина = width + 2·padding + 2·border."}],
             min_pass=3, pack="web-basics", runner="html")
merge_pack("web-basics", "web-03-layout", skills)

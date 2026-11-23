"""Мини-проект веба: адаптивное и доступное портфолио (HTML + CSS + JS в трёх файлах, два этапа)."""
from projects import milestone, write_project, hints

RULES = "[...document.styleSheets].flatMap(s => [...s.cssRules])"
LEFTS = "[...document.querySelectorAll('#projects article')].map(a => Math.round(a.getBoundingClientRect().left))"
MQ = ("(() => { const rules = " + RULES + ".filter(r => r.media && /^\\(min-width:\\s*600px\\)$/.test((r.conditionText || r.media.mediaText).trim())); "
      "return rules.some(r => [...r.cssRules].some(x => { const v = x.style && x.style.gridTemplateColumns; if (!v) return false; const m = v.match(/^repeat\\(\\s*3\\s*,\\s*(.+)\\)$/); "
      "if (m) return true; const p = v.trim().split(/\\s+/); return p.length === 3 && p.every(q => q === p[0]); })); })()")
IMG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64'%3E%3Ccircle cx='32' cy='32' r='32' fill='%2380cbc4'/%3E%3C/svg%3E"

HEAD = '''<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Портфолио — Анна</title>
  <link rel="stylesheet" href="style.css">
</head>
'''
BODY1 = '''<body>
  <header>
    <h1>Анна Смирнова</h1>
    <nav>
      <a href="#about">Обо мне</a>
      <a href="#projects">Проекты</a>
      <a href="#contacts">Контакты</a>
    </nav>
  </header>
  <main>
    <section id="about">
      <h2>Обо мне</h2>
      <p>Учусь программировать и делаю небольшие проекты.</p>
    </section>
    <section>
      <h2>Проекты</h2>
      <div id="projects">
        <article><h3>Калькулятор</h3><p>Python</p></article>
        <article><h3>Визитка</h3><p>HTML и CSS</p></article>
        <article><h3>Список дел</h3><p>JavaScript</p></article>
      </div>
    </section>
  </main>
  <footer id="contacts">anna@example.com</footer>
</body>
</html>
'''
HTML1 = HEAD + BODY1
CSS1 = '''body {
  font-family: sans-serif;
  margin: 0;
  padding: 16px;
}

nav a {
  margin-right: 12px;
}

#projects {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

article {
  border: 1px solid #b2dfdb;
  padding: 12px;
}

@media (min-width: 600px) {
  #projects {
    grid-template-columns: repeat(3, 1fr);
  }
}
'''
START1 = HEAD + "<body>\n  <!-- Шапка с меню, раздел «Обо мне», три проекта в блоке #projects, подвал с контактами -->\n</body>\n</html>\n"

t1 = {"kind": "web", "lang": "html", "entry": "index.html", "cases": [
    {"id": "landmarks", "expr": "['header', 'nav', 'main', 'footer'].every(t => document.querySelectorAll(t).length === 1)", "expected": True},
    {"id": "h1", "expr": "document.querySelectorAll('h1').length === 1 && ((document.querySelector('h1') || {}).textContent || '').trim().length > 0", "expected": True},
    {"id": "nav", "expr": "document.querySelectorAll('nav a[href^=\"#\"]').length >= 3 && [...document.querySelectorAll('nav a')].every(a => !!document.querySelector(a.getAttribute('href')))", "expected": True},
    {"id": "cards", "expr": "document.querySelectorAll('#projects article').length >= 3", "expected": True},
    {"id": "phone", "expr": "new Set(" + LEFTS + ").size === 1 && " + LEFTS + ".length >= 3", "expected": True},
    {"id": "media", "expr": MQ, "expected": True, "hint": "Для экранов от 600px нужен медиазапрос с тремя равными колонками"},
    {"id": "viewport", "hidden": True, "expr": "((document.querySelector('meta[name=\"viewport\"]') || {}).content || '').replace(/\\s/g, '').includes('width=device-width')", "expected": True,
     "hint": "В head нужна строка meta viewport"},
    {"id": "grid", "hidden": True, "expr": "getComputedStyle(document.getElementById('projects')).display", "expected": "grid", "hint": "Проекты раскладываются сеткой"},
]}
m1 = milestone(
    "layout", "Этап 1. Структура и адаптивная сетка",
    "Сделайте страницу-портфолио из файлов `index.html` и `style.css` (в `index.html` уже есть `head` с подключением стилей и `meta viewport`).\n\n"
    "**`index.html`** — смысловая структура:\n\n"
    "- `header` с заголовком `h1` (ваше имя) и `nav` минимум из **трёх** ссылок-якорей (`#about`, `#projects`, `#contacts`; каждый якорь должен вести на существующий элемент с таким `id`);\n"
    "- `main` с разделом `#about` и разделом проектов, в котором блок `<div id=\"projects\">` содержит **не меньше трёх** карточек `article`;\n"
    "- `footer` с контактами.\n\n"
    "**`style.css`** — адаптивная сетка проектов: на телефоне (узкий экран) карточки стоят в **одну колонку**, а на экранах **от 600px** — в **три равные колонки** (mobile-first, `display: grid`, `gap`).",
    "Собрать смысловую страницу и адаптивную сетку в стиле mobile-first.",
    hints("Каркас: header, nav, main, footer — по одному разу.", "Ссылки меню — якоря: <a href=\"#projects\">, а у цели должен быть такой id.", "Карточки проектов — три тега article внутри <div id=\"projects\">.",
          "В CSS: #projects { display: grid; grid-template-columns: 1fr; gap: 12px; } — база для телефона.", "@media (min-width: 600px) { #projects { grid-template-columns: repeat(3, 1fr); } }"),
    t1, {"index.html": HTML1, "style.css": CSS1},
    "Смысловые теги дают странице структуру, а сетка с медиазапросом min-width показывает одну колонку на телефоне и три на широком экране.",
    ["Структура header, nav, main, footer.", "Три проекта сеткой: 1 колонка на телефоне, 3 колонки от 600px."],
    [({"index.html": HTML1, "style.css": CSS1.replace("@media (min-width: 600px) {\n  #projects {\n    grid-template-columns: repeat(3, 1fr);\n  }\n}\n", "").replace("grid-template-columns: 1fr;", "grid-template-columns: repeat(3, 1fr);")},
      "Три колонки заданы всегда: на телефоне карточки слишком узкие."),
     ({"index.html": HTML1.replace("<header>", "<div>").replace("</header>", "</div>").replace("<footer", "<div").replace("</footer>", "</div>"), "style.css": CSS1}, "Вместо header и footer — обычные div."),
     ({"index.html": HTML1.replace('  <meta name="viewport" content="width=device-width, initial-scale=1">\n', ""), "style.css": CSS1}, "Нет meta viewport."),
     ({"index.html": HTML1.replace('        <article><h3>Список дел</h3><p>JavaScript</p></article>\n', ""), "style.css": CSS1}, "Проектов только два."),
     ({"index.html": HTML1.replace('<a href="#contacts">', '<a href="#missing">'), "style.css": CSS1}, "Ссылка меню ведёт на несуществующий якорь.")],
    starter={"index.html": START1, "style.css": "/* Оформление и адаптивная сетка */\n"},
    after="web-05-grid-responsive")

# --- Этап 2: доступность и тема ---
HTML2 = HTML1.replace("<body>\n  <header>", '<body>\n  <a class="skip" href="#main">Перейти к содержимому</a>\n  <header>') \
    .replace('    </nav>\n  </header>', '    </nav>\n    <button id="theme" type="button" aria-pressed="false">Тёмная тема</button>\n  </header>') \
    .replace("  <main>", '  <main id="main">') \
    .replace('      <p>Учусь программировать и делаю небольшие проекты.</p>', f'      <img class="avatar" src="{IMG}" alt="Портрет Анны" width="64" height="64">\n      <p>Учусь программировать и делаю небольшие проекты.</p>') \
    .replace("</body>", '  <script src="script.js"></script>\n</body>')
CSS2 = CSS1 + '''
.skip {
  position: absolute;
  left: -999px;
}

.skip:focus {
  left: 8px;
  top: 8px;
  background: #ffffff;
  color: #000000;
  padding: 8px;
}

body {
  background: #ffffff;
  color: #1a1a1a;
  transition: background 0.3s, color 0.3s;
}

body.dark {
  background: #1a1a1a;
  color: #f5f5f5;
}

a {
  color: #00695c;
}

body.dark a {
  color: #80cbc4;
}

a:focus-visible,
button:focus-visible {
  outline: 3px solid orange;
  outline-offset: 2px;
}

.avatar {
  border-radius: 50%;
}

@media (prefers-reduced-motion: reduce) {
  body {
    transition: none;
  }
}
'''
JS2 = '''const button = document.getElementById("theme");

button.addEventListener("click", () => {
  const dark = document.body.classList.toggle("dark");
  button.setAttribute("aria-pressed", String(dark));
});
'''
LUM = ("const lum = (c) => { const m = c.match(/\\d+/g).map(Number); const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; "
       "return 0.2126 * f(m[0]) + 0.7152 * f(m[1]) + 0.0722 * f(m[2]); }; const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };")
CLICK = "document.getElementById('theme').click();"
t2 = {"kind": "web", "lang": "html", "entry": "index.html", "cases": [
    {"id": "skip", "expr": "(() => { const a = document.querySelector('body a'); const m = document.getElementById('main'); return !!a && a.getAttribute('href') === '#main' && !!m && m.tagName === 'MAIN'; })()", "expected": True,
     "hint": "Первой ссылкой должна идти «Перейти к содержимому» с href=\"#main\" на элемент main с id=\"main\""},
    {"id": "alt", "expr": "document.images.length >= 1 && [...document.images].every(i => (i.alt || '').trim().length > 0)", "expected": True},
    {"id": "initial", "expr": "(() => { const b = document.getElementById('theme'); return !!b && b.tagName === 'BUTTON' && b.getAttribute('aria-pressed') === 'false' && !document.body.classList.contains('dark'); })()", "expected": True},
    {"id": "on", "before": CLICK, "expr": "document.body.classList.contains('dark') + ' ' + document.getElementById('theme').getAttribute('aria-pressed')", "expected": "true true"},
    {"id": "off", "hidden": True, "before": CLICK * 2, "expr": "document.body.classList.contains('dark') + ' ' + document.getElementById('theme').getAttribute('aria-pressed')", "expected": "false false",
     "hint": "Второе нажатие возвращает светлую тему и aria-pressed=\"false\""},
    {"id": "contrast-light", "expr": "(() => { " + LUM + " const s = getComputedStyle(document.body); return ratio(s.color, s.backgroundColor) >= 4.5; })()", "expected": True,
     "hint": "Контраст текста светлой темы не меньше 4.5 : 1, фон и цвет задайте у body"},
    {"id": "contrast-dark", "expr": "(() => { " + LUM + " const r = " + RULES + ".find(x => x.selectorText === 'body.dark'); return !!r && !!r.style.color && !!r.style.backgroundColor && ratio(r.style.color, r.style.backgroundColor) >= 4.5; })()", "expected": True,
     "hint": "Стили тёмной темы — в правиле body.dark: цвет и фон с контрастом не меньше 4.5 : 1"},
    {"id": "focus", "expr": RULES + ".some(r => /:focus-visible/.test(r.selectorText || '') && r.style && r.style.outlineStyle && r.style.outlineStyle !== 'none') && !" + RULES + ".some(r => /:focus(?!-visible)/.test(r.selectorText || '') && r.style && r.style.outlineStyle === 'none')", "expected": True,
     "hint": "Нужен видимый контур в :focus-visible, и нельзя оставлять outline: none"},
    {"id": "motion", "hidden": True, "expr": RULES + ".some(r => r.media && /prefers-reduced-motion:\\s*reduce/.test(r.conditionText || r.media.mediaText))", "expected": True,
     "hint": "Анимацию перехода тем нужно отключать при prefers-reduced-motion"},
]}
m2 = milestone(
    "a11y", "Этап 2. Доступность и тёмная тема",
    "Сделайте портфолио доступным и добавьте переключатель темы (файлы `index.html`, `style.css`, `script.js`; `script.js` уже подключён в конце `body`).\n\n"
    "- **Ссылка пропуска**: первая ссылка страницы `<a class=\"skip\" href=\"#main\">Перейти к содержимому</a>` ведёт на `<main id=\"main\">`; визуально она скрыта, но появляется при фокусе клавиатуры;\n"
    "- у **каждой картинки** непустой `alt` (добавьте в раздел «Обо мне» портрет `img`);\n"
    "- **кнопка темы** `<button id=\"theme\" type=\"button\" aria-pressed=\"false\">`: по нажатию переключает класс `dark` у `body` и обновляет `aria-pressed` (`\"true\"`/`\"false\"`);\n"
    "- **контраст**: цвет и фон у `body` задайте явно; для светлой темы и для правила `body.dark` отношение контраста текста не меньше **4.5 : 1**;\n"
    "- **фокус**: видимый контур в `:focus-visible` (без `outline: none`);\n"
    "- переход цветов (`transition`) отключайте в `@media (prefers-reduced-motion: reduce)`.",
    "Сделать страницу доступной и добавить переключатель темы с обновлением состояния.",
    hints("Ссылку пропуска ставят первой в body: <a class=\"skip\" href=\"#main\">, а у main должен быть id=\"main\".", "Картинке нужен alt с описанием; кнопке темы — aria-pressed, который скрипт обновляет.",
          "Скрипт: const dark = document.body.classList.toggle(\"dark\"); затем button.setAttribute(\"aria-pressed\", String(dark));", "Стили: body { background: #fff; color: #1a1a1a; } и body.dark { background: #1a1a1a; color: #f5f5f5; } — контраст высокий.",
          "Фокус: a:focus-visible, button:focus-visible { outline: 3px solid orange; } и @media (prefers-reduced-motion: reduce) { body { transition: none; } }"),
    t2, {"index.html": HTML2, "style.css": CSS2, "script.js": JS2},
    "Ссылка пропуска, alt, aria-pressed, достаточный контраст и видимый фокус делают страницу удобной для людей с разными возможностями, а prefers-reduced-motion учитывает их настройки.",
    ["Ссылка пропуска, alt, подписанная кнопка темы.", "Переключатель меняет тему и aria-pressed.", "Контраст ≥ 4.5 : 1 в обеих темах, видимый фокус, уважение к уменьшению движения."],
    [({"index.html": HTML2, "style.css": CSS2, "script.js": JS2.replace('  button.setAttribute("aria-pressed", String(dark));\n', "")}, "aria-pressed не обновляется."),
     ({"index.html": HTML2, "style.css": CSS2.replace("  background: #1a1a1a;\n  color: #f5f5f5;\n", "  background: #333333;\n  color: #666666;\n"), "script.js": JS2}, "В тёмной теме серый текст на тёмно-сером: контраст ниже нормы."),
     ({"index.html": HTML2.replace('  <a class="skip" href="#main">Перейти к содержимому</a>\n', ""), "style.css": CSS2, "script.js": JS2}, "Нет ссылки пропуска."),
     ({"index.html": HTML2, "style.css": CSS2.replace("a:focus-visible,\nbutton:focus-visible {\n  outline: 3px solid orange;\n  outline-offset: 2px;\n}", "button:focus {\n  outline: none;\n}"), "script.js": JS2}, "Контур фокуса убран."),
     ({"index.html": HTML2.replace(' alt="Портрет Анны"', ' alt=""'), "style.css": CSS2, "script.js": JS2}, "У картинки пустой alt."),
     ({"index.html": HTML2, "style.css": CSS2.replace("@media (prefers-reduced-motion: reduce) {\n  body {\n    transition: none;\n  }\n}\n", ""), "script.js": JS2}, "Переход тем не отключается при уменьшении движения.")],
    starter={"script.js": "// Переключатель темы\n"},
    after="web-06-animation-a11y")

portfolio = {"id": "portfolio", "kind": "mini", "title": "Портфолио",
             "summary": "Адаптивная и доступная страница-портфолио из трёх файлов: смысловая разметка, сетка проектов и переключатель темы.",
             "language": "html", "afterLesson": "web-05-grid-responsive",
             "skills": ["web.semantic", "web.grid", "web.responsive", "web.a11y", "js.dom", "js.events"],
             "milestones": [m1, m2]}

if __name__ == "__main__":
    write_project("web-basics", portfolio)

"""Урок JS 5: страница и DOM — список дел в браузере."""
from jsib import *


def preview(code):
    return "Предпросмотр страницы:\n" + page_text(code)


def after(code, before, expr):
    r = web_check("html", code, {"kind": "web", "lang": "html", "cases": [{"id": "x", "before": before, "expr": expr, "expected": None}]})
    return r["cases"][0]["actual"]


TODO_HEAD = """  <h1>Мои дела</h1>
  <input id="title" placeholder="Что сделать?">
  <button id="add">Добавить</button>
  <ul id="list"></ul>
  <p>Осталось: <span id="left">0</span></p>
"""
SCRIPT = """  <script>
    const input = document.getElementById("title");
    const list = document.getElementById("list");
    const left = document.getElementById("left");

    function update() {
      left.textContent = list.querySelectorAll("li:not(.done)").length;
    }

    document.getElementById("add").addEventListener("click", () => {
      const text = input.value.trim();
      if (text === "") return;
      const li = document.createElement("li");
      li.textContent = text;
      li.addEventListener("click", () => {
        li.classList.toggle("done");
        update();
      });
      list.appendChild(li);
      input.value = "";
      update();
    });
  </script>
"""
TODO = page(TODO_HEAD + SCRIPT, style("li.done { text-decoration: line-through; color: gray; }"))
ADD = lambda t: f"document.getElementById('title').value = '{t}'; document.getElementById('add').click();"
BEFORE = ADD("Молоко") + ADD("Отчёт") + "document.querySelector('#list li').click();"
n_items = after(TODO, BEFORE, "document.querySelectorAll('#list li').length")
n_left = after(TODO, BEFORE, "document.getElementById('left').textContent")
n_done = after(TODO, BEFORE, "document.querySelectorAll('li.done').length")
assert (str(n_items), str(n_left), str(n_done)) == ("2", "1", "1"), (n_items, n_left, n_done)

FIND = """<script>
  const h = document.querySelector("h1");
  h.textContent = "Новый заголовок";
  document.querySelectorAll("li").forEach((li, i) => {
    li.textContent = (i + 1) + ". " + li.textContent;
  });
  document.getElementById("count").textContent = document.getElementById("list").children.length;
</script>"""
FIND_PAGE = page('  <h1>Заголовок</h1>\n  <ul id="list">\n    <li>Хлеб</li>\n    <li>Чай</li>\n  </ul>\n  <p>Пунктов: <span id="count"></span></p>\n  ' + FIND)
XSS = page('  <div id="box"></div>\n  <script>\n    const text = "<b>жирный</b>";\n    document.getElementById("box").textContent = text;\n  </script>')
XSS_HTML = XSS.replace("textContent = text", "innerHTML = text")
t_text = after(XSS, "", "document.getElementById('box').innerHTML")
t_html = after(XSS_HTML, "", "document.getElementById('box').innerHTML")

use_file("index.html")
scenes = [
    scene("intro", "Страница как дерево", """
      Браузер превращает HTML в дерево объектов, которое называется DOM. Каждый тег — узел дерева, и из JavaScript его можно
      найти, прочитать и изменить: поменять текст, добавить элемент, убрать класс. Так работают все живые страницы. Сегодня на
      этой основе соберём настоящий список дел.""",
          [NOTE("**DOM** — дерево элементов страницы. JavaScript находит узлы и меняет их.", at="Каждый тег")]),
    scene("find", "Найти и изменить", """
      Метод querySelector находит первый элемент по CSS-селектору, а querySelectorAll — все подходящие. Меняем текст заголовка
      свойством textContent. Для каждого пункта списка дописываем номер. Свойство children даёт дочерние элементы, у списка их
      два. Запускаем и смотрим результат.""",
          [CLEAR(), T(FIND_PAGE, at="Метод querySelector"), HL([15], at="Метод querySelector"), HL([16], at="Меняем текст"), HL([17, 18, 19], at="Для каждого"), HL([20], at="Свойство children"),
           RUN(at="Запускаем"), OUT(preview(FIND_PAGE), at="результат")]),
    scene("create", "Создать элемент", """
      Новые элементы создают методом createElement, заполняют текстом и добавляют на страницу через appendChild. Обратите внимание:
      пользовательский текст всегда кладите через textContent. Свойство innerHTML разберёт текст как разметку, и если в нём
      окажется чужой тег или скрипт, страница выполнит его. Это основа уязвимости XSS. Запишем строку с тегом через textContent: он
      останется просто текстом.""",
          [CLEAR(), T(XSS, at="Новые элементы"), HL([10, 11], at="пользовательский"), RUN(at="Запишем"), OUT(preview(XSS), at="Запишем"),
           NOTE("textContent сохранил: `" + str(t_text) + "`. Через innerHTML тег стал бы настоящей разметкой.", at="останется")]),
    scene("todo", "Собираем список дел", """
      Теперь соберём всё вместе. По нажатию кнопки читаем поле, убираем лишние пробелы и пропускаем пустую строку. Создаём пункт
      списка, подписываем его на нажатие: клик переключает класс done, и CSS зачёркивает текст. Добавляем пункт в список,
      очищаем поле и обновляем счётчик оставшихся дел. Нажмём добавление дважды и отметим первое дело выполненным.""",
          [CLEAR(), T(TODO, at="Теперь соберём"), HL([26, 27], at="читаем поле"), HL([28, 29], at="Создаём пункт"), HL([30, 31, 32, 33], at="клик"),
           HL([34, 35, 36], at="Добавляем пункт"), RUN(at="Нажмём добавление"), OUT(preview(TODO), at="Нажмём добавление"),
           NOTE("После двух добавлений и отметки первого: пунктов — **" + str(n_items) + "**, осталось — **" + str(n_left) + "**, выполнено — **" + str(n_done) + "**.", at="отметим первое")]),
    scene("mistake", "Частая ошибка: значение читают не в обработчике", """
      Типичная ошибка: прочитать значение поля один раз при загрузке страницы, в самом начале скрипта. Тогда оно навсегда останется
      пустым, и каждое нажатие добавит пустой пункт. Читайте поле внутри обработчика, в момент нажатия.""",
          [NOTE("Читаем `input.value` **внутри** обработчика — тогда берётся текущее значение.", at="Читайте")]),
    scene("summary", "Итог", """
      Подведём итог. DOM — дерево элементов страницы. Находим узлы через querySelector и querySelectorAll, меняем через textContent
      и classList, создаём через createElement и appendChild. События ловим через addEventListener. Пользовательский текст
      вставляем через textContent, а не innerHTML.""",
          [NOTE("`querySelector` · `textContent` · `createElement` · `appendChild` · `classList.toggle` · `addEventListener`", at="Подведём")]),
]
use_file(None)

notes = """
# JavaScript: страница и DOM

```js
const h = document.querySelector("h1");          // первый подходящий
document.querySelectorAll("li");                 // все подходящие
h.textContent = "Новый заголовок";

const li = document.createElement("li");
li.textContent = "Молоко";
document.getElementById("list").appendChild(li);
li.classList.toggle("done");                     // добавить/убрать класс
li.remove();                                     // удалить элемент

button.addEventListener("click", () => { … });   // реакция на событие
```

- Читайте значение поля **внутри** обработчика: `input.value`.
- Пользовательский текст — только через `textContent`. `innerHTML` разбирает разметку: это путь к XSS.
- `list.children.length` — число дочерних элементов.
- События всплывают: один обработчик на `ul` может обслужить все `li` (делегирование): `event.target`.
"""

PAGE_ADD = page(TODO_HEAD + "  <script>\n    // ваш код\n  </script>\n")


def todo_solution(body):
    return page(TODO_HEAD + "  <script>\n" + body + "  </script>\n")


SOL1 = """    const input = document.getElementById("title");
    const list = document.getElementById("list");
    document.getElementById("add").addEventListener("click", () => {
      const text = input.value.trim();
      if (text === "") return;
      const li = document.createElement("li");
      li.textContent = text;
      list.appendChild(li);
      input.value = "";
    });
"""
t1 = {"kind": "web", "lang": "html", "cases": [
    {"id": "one", "before": ADD("Молоко"), "expr": "[...document.querySelectorAll('#list li')].map(li => li.textContent).join('|')", "expected": "Молоко"},
    {"id": "two", "before": ADD("Молоко") + ADD("Отчёт"), "expr": "[...document.querySelectorAll('#list li')].map(li => li.textContent).join('|')", "expected": "Молоко|Отчёт"},
    {"id": "clear", "before": ADD("Хлеб"), "expr": "document.getElementById('title').value", "expected": "", "hint": "После добавления поле очищается"},
    {"id": "empty", "hidden": True, "before": ADD("") + ADD("   "), "expr": "document.querySelectorAll('#list li').length", "expected": 0, "hint": "Пустые дела не добавляются"},
    {"id": "trim", "hidden": True, "before": ADD("  Чай  "), "expr": "document.querySelector('#list li').textContent", "expected": "Чай", "hint": "Пробелы по краям убираются"},
]}
a1 = asg("a1-add", "write", "Добавить дело",
         "На странице есть поле `#title`, кнопка `#add` и пустой список `#list`. Напишите скрипт: по нажатию на кнопку в **конец списка** добавляется пункт `li` с введённым текстом (без пробелов по краям), а поле очищается. **Пустой** текст (в том числе из одних пробелов) не добавляется.",
         "Создавать элементы и реагировать на нажатие.", "Страница с полем, кнопкой и списком.", "Дело появляется в списке, поле очищается.",
         ["Разметку не меняйте — только скрипт."],
         hints("Найдите кнопку через getElementById и подпишитесь на click.", "Внутри обработчика прочитайте input.value и уберите пробелы: trim().", "Пустую строку пропустите: return.", "Создайте пункт: document.createElement(\"li\"), задайте textContent, добавьте appendChild.", "После добавления очистите поле: input.value = \"\"."),
         t1, todo_solution(SOL1), "Читаем поле внутри обработчика, проверяем пустоту, создаём li, добавляем в ul и очищаем поле.",
         ["Пункты добавляются, пустые — нет, поле очищается."],
         [(todo_solution(SOL1.replace('      if (text === "") return;\n', "")), "Нет проверки: добавляются пустые дела."),
          (todo_solution(SOL1.replace('      input.value = "";\n', "")), "Поле не очищается."),
          (todo_solution(SOL1.replace("input.value.trim()", "input.value")), "Пробелы по краям не убираются."),
          (todo_solution(SOL1.replace("li.textContent = text;", "li.textContent = \"дело\";")), "Текст пункта не из поля.")],
         starter=PAGE_ADD)

# --- Задание 2: переключение done ---
LIST2 = '  <ul id="list">\n    <li>Хлеб</li>\n    <li>Чай</li>\n    <li>Сыр</li>\n  </ul>\n'
SOL2 = '    document.querySelectorAll("#list li").forEach((li) => {\n      li.addEventListener("click", () => {\n        li.classList.toggle("done");\n      });\n    });\n'
S2 = page(LIST2 + "  <script>\n" + SOL2 + "  </script>\n")
CLICK = lambda i: f"document.querySelectorAll('#list li')[{i}].click();"
DONE = "[...document.querySelectorAll('#list li')].map(li => li.classList.contains('done') ? 1 : 0).join('')"
t2 = {"kind": "web", "lang": "html", "cases": [
    {"id": "none", "expr": DONE, "expected": "000"},
    {"id": "one", "before": CLICK(1), "expr": DONE, "expected": "010"},
    {"id": "twice", "before": CLICK(1) + CLICK(1), "expr": DONE, "expected": "000", "hint": "Повторное нажатие снимает отметку"},
    {"id": "two", "hidden": True, "before": CLICK(0) + CLICK(2), "expr": DONE, "expected": "101"},
]}
a2 = asg("a2-toggle", "write", "Отметить сделанным",
         "На странице список из трёх пунктов. Напишите скрипт: нажатие на любой пункт **переключает** у него класс `done` (есть — убрать, нет — добавить). Остальные пункты не меняются.",
         "Подписывать на событие несколько элементов.", "Страница со списком.", "Нажатие переключает класс done у своего пункта.",
         ["Разметку не меняйте."],
         hints("Нужно подписать на click каждый пункт.", "Найти все пункты: querySelectorAll(\"#list li\"), обойти forEach.", "Внутри обработчика работаем с тем же li.", "У элемента есть classList.", "li.classList.toggle(\"done\")"),
         t2, S2, "classList.toggle добавляет класс, если его нет, и убирает, если есть. Каждый пункт получает свой обработчик.",
         ["Нажатие переключает done только у своего пункта."],
         [(page(LIST2 + '  <script>\n    document.querySelectorAll("#list li").forEach((li) => {\n      li.addEventListener("click", () => {\n        li.classList.add("done");\n      });\n    });\n  </script>\n'), "add не снимает отметку при повторном нажатии."),
          (page(LIST2 + '  <script>\n    document.querySelector("#list li").addEventListener("click", (e) => {\n      e.target.classList.toggle("done");\n    });\n  </script>\n'), "Обработчик только у первого пункта."),
          (page(LIST2 + '  <script>\n    document.querySelectorAll("#list li").forEach((li) => {\n      li.addEventListener("click", () => {\n        document.querySelectorAll("#list li").forEach((x) => x.classList.toggle("done"));\n      });\n    });\n  </script>\n'), "Переключаются все пункты, а не нажатый.")],
         starter=page(LIST2 + "  <script>\n    // ваш код\n  </script>\n"))

# --- Задание 3: удаление делегированием ---
LIST3 = '  <ul id="list">\n    <li>Хлеб <button>×</button></li>\n    <li>Чай <button>×</button></li>\n    <li>Сыр <button>×</button></li>\n  </ul>\n'
SOL3 = '    document.getElementById("list").addEventListener("click", (e) => {\n      if (e.target.tagName === "BUTTON") {\n        e.target.closest("li").remove();\n      }\n    });\n'
S3 = page(LIST3 + "  <script>\n" + SOL3 + "  </script>\n")
CLICKB = lambda i: f"document.querySelectorAll('#list button')[{i}].click();"
LEFT = "[...document.querySelectorAll('#list li')].map(li => li.firstChild.textContent.trim()).join(',')"
t3 = {"kind": "web", "lang": "html", "cases": [
    {"id": "start", "expr": LEFT, "expected": "Хлеб,Чай,Сыр"},
    {"id": "del-mid", "before": CLICKB(1), "expr": LEFT, "expected": "Хлеб,Сыр"},
    {"id": "del-two", "before": CLICKB(0) + CLICKB(0), "expr": LEFT, "expected": "Сыр", "hint": "После удаления кнопки сдвигаются"},
    {"id": "text-click", "hidden": True, "before": "document.querySelectorAll('#list li')[0].click();", "expr": LEFT, "expected": "Хлеб,Чай,Сыр",
     "hint": "Удалять нужно только по нажатию на кнопку, а не на текст пункта"},
]}
a3 = asg("a3-delete", "write", "Удалить дело",
         "В каждом пункте списка есть кнопка `×`. Напишите скрипт: нажатие на кнопку **удаляет её пункт** целиком. Нажатие на сам текст пункта ничего не делает. Сделайте это **одним обработчиком на список** (делегирование событий).",
         "Использовать event.target и closest.", "Список с кнопками.", "Нажатая кнопка удаляет свой пункт.",
         ["Один обработчик на ul."],
         hints("Событие нажатия всплывает от кнопки вверх до списка.", "Подпишитесь на click у самого списка.", "Нажатый элемент — e.target; проверьте, что это кнопка: tagName === \"BUTTON\".", "Пункт, в котором кнопка, находит closest(\"li\").", "Удаляет элемент метод remove()."),
         t3, S3, "Событие всплывает: обработчик на ul видит нажатие на любую кнопку внутри. closest(\"li\") находит пункт, remove() убирает.",
         ["Кнопка удаляет только свой пункт."],
         [(page(LIST3 + '  <script>\n    document.getElementById("list").addEventListener("click", (e) => {\n      e.target.closest("li").remove();\n    });\n  </script>\n'), "Удаляется пункт и при нажатии на текст."),
          (page(LIST3 + '  <script>\n    document.getElementById("list").addEventListener("click", (e) => {\n      if (e.target.tagName === "BUTTON") {\n        document.getElementById("list").innerHTML = "";\n      }\n    });\n  </script>\n'), "Удаляется весь список.")],
         starter=page(LIST3 + "  <script>\n    // ваш код\n  </script>\n"))

# --- Задание 4: исправить ---
STARTER4 = todo_solution(SOL1.replace('    document.getElementById("add").addEventListener("click", () => {\n      const text = input.value.trim();\n',
                                       '    const text = input.value.trim();\n    document.getElementById("add").addEventListener("click", () => {\n'))
a4 = asg("a4-fix", "fix", "Всегда пустые дела",
         "Скрипт добавляет дела, но каждый новый пункт получается **пустым**, а проверка на пустоту всегда срабатывает. Найдите причину и исправьте.",
         "Читать значение поля в нужный момент.", "Страница с ошибкой в скрипте.", "Дело добавляется с введённым текстом.",
         ["Разметку не меняйте."],
         hints("Введите дело и нажмите кнопку: что происходит?", "Посмотрите, где именно читается input.value.", "Строка с чтением значения стоит вне обработчика.", "Она выполняется один раз при загрузке страницы, когда поле ещё пусто.", "Перенесите чтение внутрь обработчика нажатия."),
         t1, todo_solution(SOL1), "Значение читалось при загрузке страницы (оно пустое) и больше не обновлялось. Чтение внутри обработчика берёт текущий текст.",
         ["Дела добавляются с введённым текстом."],
         [(todo_solution(SOL1.replace('      const text = input.value.trim();\n', '      const text = input.value;\n').replace("      if (text === \"\") return;\n", "")), "Чтение внутри обработчика, но пропали проверка и trim.")],
         starter=STARTER4)

CODE5 = page('  <ul id="list"></ul>\n  <script>\n    const list = document.getElementById("list");\n    for (const t of ["а", "б", "в", "г"]) {\n      const li = document.createElement("li");\n      li.textContent = t;\n      list.appendChild(li);\n    }\n    list.children[0].classList.add("done");\n    list.children[2].classList.add("done");\n    list.children[1].remove();\n    list.lastElementChild.classList.add("done");\n  </script>')
ans5 = str(page_text(CODE5, "document.querySelectorAll('li.done').length"))
assert ans5 == "3", ans5
a5 = asg("a5-predict", "predict", "Сколько дел отмечено?",
         "Что произойдёт, когда скрипт отработает? Сколько пунктов будет с классом `done`? Ответьте числом.",
         "Читать код, работающий с DOM.", "—", "Одно число.", [],
         hints("Идите по строкам скрипта по порядку.", "Сначала создаются четыре пункта: а, б, в, г.", "Класс done получают первый и третий (а и в).", "Второй пункт (б) удаляется, остаются а, в, г.", "Последний (г) тоже получает done."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "Остаются а, в, г: у а и в класс добавлен раньше, у г — последним действием. Итого три.", ["Верное число."],
         [("2", "Последняя строка тоже добавляет класс (пункту г)."), ("4", "Пункт «б» удалён, и пунктов только три."), ("1", "Отмечены не один, а три пункта.")],
         code=CODE5)

for a in (a1, a2, a3):
    web_verify("html", a)
web_verify("html", a4)

skills = {"js.dom2": "DOM: поиск и изменение элементов", "js.events2": "События и делегирование", "js.safe-html": "textContent и безопасность (XSS)"}
write_lesson("js-05-dom", "JavaScript: страница и список дел",
             "Находить и менять элементы страницы, создавать новые, обрабатывать события и собрать рабочий список дел.",
             list(skills), ["js-04-async"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Значение поля читают вне обработчика", "fix": "Читайте input.value внутри обработчика нажатия."},
              {"mistake": "innerHTML для пользовательского текста", "fix": "Используйте textContent: innerHTML выполнит чужую разметку (XSS)."},
              {"mistake": "Обработчик только на первом элементе", "fix": "querySelector находит один элемент; для всех — querySelectorAll и forEach или делегирование."},
              {"mistake": "classList.add вместо toggle", "fix": "toggle переключает класс туда и обратно."}],
             min_pass=3, pack="javascript", runner="html")
merge_js_lesson("js-05-dom", skills)

from lib import *

begin()
scenes = [
 S("intro", "Данные должны жить дольше программы", """
  Всё, что хранится в переменных, исчезает, как только программа завершилась. Для заметок, списка трат, настроек и результатов
  игры этого мало. Данные нужно сохранять на диск, то есть в файлы. Python умеет открывать файл, записывать в него текст и
  читать его обратно. В этом уроке разберём три действия: запись, чтение и дозапись, а также обработаем ситуацию, когда
  нужного файла нет. Приложение работает в защищённой песочнице, и файлы, которые вы создаёте в заданиях, видны только вашей
  программе.""",
  nt("**Файл** — способ сохранить данные между запусками программы", at="Данные нужно")),
 S("write", "Запись в файл", """
  Файл открывают функцией open: первым аргументом идёт имя, вторым — режим. Режим w означает запись: если файла нет, он
  создаётся, а если есть, его старое содержимое стирается. Для русского текста всегда указывайте кодировку utf-8. Лучше
  всего открывать файл в конструкции with: она сама закроет файл, даже если внутри произойдёт ошибка. Метод write записывает
  строку, а перевод строки мы добавляем сами символом обратная косая и n.""",
  clr(), t('with open("notes.txt", "w", encoding="utf-8") as f:\n    f.write("Купить хлеб\\n")\n    f.write("Позвонить маме\\n")\nprint("записано")\n', at="Файл открывают"), run("Метод write")),
 S("read", "Чтение файла", """
  Для чтения используют режим r, который можно не указывать. Метод read возвращает весь текст одной строкой. Метод readlines
  возвращает список строк, но каждая строка заканчивается символом перевода строки, который убирают методом strip. Чаще
  всего файл читают построчно прямо циклом for: так можно работать даже с очень большими файлами, не загружая их в память целиком.""",
  clr(), t('with open("notes.txt", "w", encoding="utf-8") as f:\n    f.write("Купить хлеб\\nПозвонить маме\\n")\n\n', at="Для чтения"),
  t('with open("notes.txt", encoding="utf-8") as f:\n    text = f.read()\nprint(repr(text))\n', at="Метод read"),
  t('with open("notes.txt", encoding="utf-8") as f:\n    for line in f:\n        print(line.strip())\n', at="Чаще"), run("Чаще")),
 S("append", "Дозапись", """
  Режим a, от слова append, добавляет текст в конец файла, не стирая старое. Так делают журналы и списки дел. А вот
  режим w при каждом открытии начинает файл с чистого листа, и это частая причина потерянных данных. Допишем в файл
  новую заметку и прочитаем всё содержимое: теперь в нём три строки.""",
  clr(), t('with open("log.txt", "w", encoding="utf-8") as f:\n    f.write("1\\n2\\n")\n', at="Режим a"),
  t('with open("log.txt", "a", encoding="utf-8") as f:\n    f.write("3\\n")\n', at="Допишем"),
  t('with open("log.txt", encoding="utf-8") as f:\n    print(f.read().split())\n', at="Допишем"), run("теперь в нём")),
 S("missing", "Файла нет", """
  Если открыть для чтения файл, которого не существует, Python вызовет FileNotFoundError. Это нормальная ситуация: например,
  при первом запуске программы файла настроек ещё нет. Поэтому чтение часто оборачивают в try и except. Если файла
  нет, берём значение по умолчанию. Тот же приём спасает от ошибок, когда пользователь ввёл неверное имя файла.""",
  clr(), t('try:\n    with open("settings.txt", encoding="utf-8") as f:\n        data = f.read()\nexcept FileNotFoundError:\n    data = "настроек пока нет"\nprint(data)\n', at="Поэтому чтение"), run("Тот же приём")),
 S("parse", "Разбор строк файла", """
  Файлы часто хранят таблицы: на каждой строке несколько значений, разделённых точкой с запятой. Допустим, это список покупок: название,
  количество и цена. Мы читаем файл построчно, разбиваем строку методом split по разделителю и превращаем числа из строк
  в числа. Затем считаем общую стоимость. Это и есть основа обработки данных: прочитать, разобрать, посчитать.""",
  clr(), t('with open("cart.txt", "w", encoding="utf-8") as f:\n    f.write("хлеб;2;40\\nмолоко;1;90\\n")\n\n', at="Допустим"),
  t("total = 0\nwith open(\"cart.txt\", encoding=\"utf-8\") as f:\n    for line in f:\n        name, qty, price = line.strip().split(\";\")\n        total += int(qty) * int(price)\nprint(total)\n", at="Мы читаем"), run("Затем считаем")),
 S("summary", "Итог", """
  Подведём итог. Файл открывается функцией open с режимом: w — запись с очисткой, r — чтение, a — дозапись. Всегда указывайте кодировку
  utf-8 и открывайте файлы через with, чтобы они закрывались автоматически. Читать можно целиком методом read или построчно
  циклом for. Отсутствующий файл вызывает FileNotFoundError, который обрабатывают через try. Строки таблиц разбирают
  методом split. Следующий шаг — формат JSON, в котором хранят структурированные данные.""",
  nt('`open(имя, "w"/"r"/"a", encoding="utf-8")` · `with` · `for line in f` · `FileNotFoundError`', at="Подведём итог")),
]

notes = """
# Файлы

```python
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("Купить хлеб\\n")
    f.write("Позвонить маме\\n")

with open("notes.txt", encoding="utf-8") as f:
    for line in f:
        print(line.strip())
```

| Режим | Что делает |
| --- | --- |
| `"r"` | чтение (по умолчанию); файла нет — `FileNotFoundError` |
| `"w"` | запись; **стирает** старое содержимое |
| `"a"` | дозапись в конец |

## Файла нет

```python
try:
    with open("settings.txt", encoding="utf-8") as f:
        data = f.read()
except FileNotFoundError:
    data = "настроек пока нет"
print(data)
```

## Разбор таблицы

```python
with open("cart.txt", "w", encoding="utf-8") as f:
    f.write("хлеб;2;40\\nмолоко;1;90\\n")

total = 0
with open("cart.txt", encoding="utf-8") as f:
    for line in f:
        name, qty, price = line.strip().split(";")
        total += int(qty) * int(price)
print(total)    # 170
```

## Запомните

1. Всегда `with open(...)` и `encoding="utf-8"`.
2. `"w"` стирает файл — для дозаписи используйте `"a"`.
3. `strip()` убирает перевод строки в конце.
"""

a1 = stdout_task("a1-roundtrip", "Записать и прочитать", "Прочитайте строку, запишите её в файл `note.txt`, затем прочитайте файл и выведите его содержимое **в верхнем регистре**.\n\nВвод:\n```\nпривет, мир\n```\nВывод:\n```\nПРИВЕТ, МИР\n```",
  'text = input()\nwith open("note.txt", "w", encoding="utf-8") as f:\n    f.write(text)\nwith open("note.txt", encoding="utf-8") as f:\n    print(f.read().upper())\n',
  ["привет, мир\n", ("Python\n", True), ("а\n", True), ("Ёжик в тумане\n", True)],
  [('text = input()\nwith open("note.txt", "w", encoding="utf-8") as f:\n    f.write(text)\nwith open("note.txt", "w", encoding="utf-8") as f:\n    print(f.read().upper())\n', "Файл для чтения открыт в режиме w: чтение невозможно (и старое содержимое стёрто)."),
   ('text = input()\nwith open("note.txt", "w", encoding="utf-8") as f:\n    f.write(text)\nwith open("note.txt", encoding="utf-8") as f:\n    print(f.read())\n', "Регистр не изменён.")],
  hints("Нужны два шага: записать, потом прочитать.", "Откройте файл в режиме w и вызовите write.", "Затем откройте его снова для чтения (режим по умолчанию).", "Содержимое получают методом read.", "print(f.read().upper())."),
  "Сначала файл открывается на запись, закрывается блоком with, затем открывается заново для чтения.")

a2 = fn_task("a2-save-lines", "Сохранить список строк", "Напишите функцию `save_lines(lines)`: она записывает каждую строку списка `lines` в файл `lines.txt` **на отдельной строке**, затем читает файл и возвращает список прочитанных строк (без символов перевода строки).\n\nПример: `save_lines([\"а\", \"б\"])` → `[\"а\", \"б\"]`.",
  "save_lines", 'def save_lines(lines):\n    with open("lines.txt", "w", encoding="utf-8") as f:\n        for line in lines:\n            f.write(line + "\\n")\n    with open("lines.txt", encoding="utf-8") as f:\n        return [row.strip() for row in f]\n',
  [[["а", "б"]], [[]], ([["один"]], True), ([["привет мир", "ещё строка", "и ещё"]], True)],
  [('def save_lines(lines):\n    with open("lines.txt", "w", encoding="utf-8") as f:\n        for line in lines:\n            f.write(line)\n    with open("lines.txt", encoding="utf-8") as f:\n        return [row.strip() for row in f]\n', "Не добавлен перевод строки: всё записано в одну строку."),
   ('def save_lines(lines):\n    with open("lines.txt", "w", encoding="utf-8") as f:\n        for line in lines:\n            f.write(line + "\\n")\n    with open("lines.txt", encoding="utf-8") as f:\n        return list(f)\n', "Строки возвращены вместе с символом перевода строки."),
   ('def save_lines(lines):\n    with open("lines.txt", "a", encoding="utf-8") as f:\n        for line in lines:\n            f.write(line + "\\n")\n    with open("lines.txt", encoding="utf-8") as f:\n        return [row.strip() for row in f]\n', "Режим a дописывает: строки из прошлых вызовов остаются в файле.")],
  hints("Сначала запись, затем чтение — два блока with.", "Запишите в цикле: каждую строку плюс символ перевода строки.", "Перевод строки в тексте программы пишется как \\n.", "При чтении каждая строка заканчивается переводом строки — уберите его методом strip.", "return [row.strip() for row in f]."),
  "Запись и чтение — два отдельных блока with. strip() убирает символ перевода строки, который остаётся при чтении.")

a3 = stdout_task("a3-cart", "Стоимость корзины из файла", "Первая строка — число позиций `n`. Далее `n` строк `название;количество;цена`. Запишите их в файл `cart.txt`, прочитайте файл и выведите общую стоимость (сумма количество × цена).\n\nВвод:\n```\n2\nхлеб;2;40\nмолоко;1;90\n```\nВывод:\n```\n170\n```",
  'n = int(input())\nlines = [input() for _ in range(n)]\nwith open("cart.txt", "w", encoding="utf-8") as f:\n    for line in lines:\n        f.write(line + "\\n")\ntotal = 0\nwith open("cart.txt", encoding="utf-8") as f:\n    for line in f:\n        name, qty, price = line.strip().split(";")\n        total += int(qty) * int(price)\nprint(total)\n',
  ["2\nхлеб;2;40\nмолоко;1;90\n", ("1\nчай;3;100\n", True), ("3\nа;1;1\nб;2;2\nв;3;3\n", True), ("0\n", True)],
  [('n = int(input())\nlines = [input() for _ in range(n)]\ntotal = 0\nfor line in lines:\n    name, qty, price = line.split(";")\n    total += int(qty) + int(price)\nprint(total)\n', "Количество и цена складываются вместо умножения."),
   ('n = int(input())\nlines = [input() for _ in range(n)]\ntotal = 0\nfor line in lines:\n    name, qty, price = line.split(";")\n    total = int(qty) * int(price)\nprint(total)\n', "Сумма не накапливается: остаётся стоимость последней позиции.")],
  hints("Разберите задачу на этапы: прочитать, записать в файл, прочитать файл, посчитать.", "Позиции читаем в цикле input().", "Каждую позицию записываем в файл с переводом строки.", "Файл читаем построчно, строку разбиваем по точке с запятой.", "total += int(qty) * int(price)."),
  "Данные проходят полный цикл: ввод → файл → разбор → сумма. Накопитель total увеличивается на каждой строке.")

a4 = predict_task("a4-modes", "Режимы открытия", 'with open("a.txt", "w", encoding="utf-8") as f:\n    f.write("1\\n2\\n")\nwith open("a.txt", "a", encoding="utf-8") as f:\n    f.write("3\\n")\nwith open("a.txt", encoding="utf-8") as f:\n    lines = f.read().split()\nprint(len(lines), lines[-1])\nwith open("a.txt", "w", encoding="utf-8") as f:\n    f.write("x")\nwith open("a.txt", encoding="utf-8") as f:\n    print(f.read())\n',
  [("3 3\n1\n2\n3\nx\n", "Режим w стирает файл: после него в файле только «x»."),
   ("2 2\nx\n", "Режим a дописывает в конец: строк в файле три, последняя — «3».")],
  hints("Следите за содержимым файла после каждого блока with.", "После первого блока в файле «1» и «2».", "Режим a добавляет «3» в конец.", "split() вернёт три элемента, последний — «3».", "Последний блок стирает всё и записывает «x»."),
  "w перезаписывает, a дополняет. После трёх записей в файле три строки, а последняя запись в режиме w оставляет единственную «x».")

a5 = fn_task("a5-read-or-default", "Чтение с запасным вариантом", "Напишите функцию `read_text(name)`: возвращает содержимое файла `name`, а если файла не существует — пустую строку `\"\"`.",
  "read_text", 'def read_text(name):\n    try:\n        with open(name, encoding="utf-8") as f:\n            return f.read()\n    except FileNotFoundError:\n        return ""\n',
  [["такого-файла-нет.txt"], ["data/missing.txt"], (["x.txt"], True), (["config.ini"], True)],
  [('def read_text(name):\n    with open(name, encoding="utf-8") as f:\n        return f.read()\n', "Для отсутствующего файла возникает FileNotFoundError."),
   ('def read_text(name):\n    try:\n        with open(name, encoding="utf-8") as f:\n            return f.read()\n    except FileNotFoundError:\n        return None\n', "Вместо пустой строки возвращается None.")],
  hints("Открытие отсутствующего файла вызывает исключение.", "Нужен блок try с чтением файла внутри.", "Перехватывайте именно FileNotFoundError.", "В except верните пустую строку.", "try: with open(...) as f: return f.read(); except FileNotFoundError: return ''."),
  "Тип исключения указан конкретно, поэтому остальные ошибки (например, неверная кодировка) не скрываются.")

mistakes = [
 {"mistake": "Открывают для записи в режиме w файл, который хотели дополнить", "fix": "Для дозаписи используйте режим a: w стирает прежнее содержимое."},
 {"mistake": "Не указывают encoding='utf-8' для русского текста", "fix": "Всегда указывайте encoding='utf-8'."},
 {"mistake": "Забывают убрать перевод строки при чтении", "fix": "Используйте line.strip() или line.rstrip('\\n')."},
 {"mistake": "Открывают файл без with и забывают закрыть", "fix": "Конструкция with закрывает файл автоматически."}]

finish("py-17-files", "Файлы", "Записывать, читать и дописывать текстовые файлы, обрабатывать отсутствующий файл и разбирать строки таблицы.",
  {"python.files": "Файлы: open и with", "python.files.modes": "Режимы w, r, a", "python.files.parse": "Разбор строк файла"},
  ["py-16-exceptions"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="python-core")

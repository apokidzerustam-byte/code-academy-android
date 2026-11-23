from lib import *

begin()
scenes = [
 S("intro", "Как разговаривают программы", """
  Когда вы открываете сайт или приложение загружает ленту новостей, ваше устройство отправляет серверу запрос, а сервер
  возвращает ответ. Правила этого разговора называются протоколом HTTP. В нашем приложении нет доступа к сети, и это
  намеренно, но структуру запросов и ответов можно изучить и без неё: это обычный текст, который Python легко разбирает.
  Сегодня мы научимся читать адреса, понимать методы и коды состояния и разбирать сырой ответ сервера.""",
  nt("**HTTP** — текстовый протокол: запрос → ответ", at="Правила этого разговора")),
 S("url", "Из чего состоит адрес", """
  Адрес, или URL, состоит из нескольких частей: схема, например https, хост, то есть имя сервера, путь к ресурсу и параметры
  запроса после вопросительного знака. Модуль urllib точка parse умеет разбирать адрес на части. Функция urlparse возвращает
  объект, у которого есть поля scheme, netloc и path. А параметры запроса превращаются в словарь функцией parse_qs. Значения
  в нём — списки, потому что один параметр может встречаться несколько раз.""",
  clr(), t('from urllib.parse import urlparse, parse_qs\n\nurl = "https://api.example.com/tasks?status=open&limit=5"\nparts = urlparse(url)\n', at="Модуль urllib"),
  t("print(parts.scheme, parts.netloc, parts.path)\n", at="Функция urlparse"),
  t("print(parse_qs(parts.query))\n", at="А параметры запроса"), run("Значения")),
 S("build", "Сборка параметров", """
  Обратная задача: собрать строку параметров из словаря. Для этого есть функция urlencode. Она заботится об экранировании: пробелы и
  русские буквы заменяются безопасными последовательностями. Нельзя склеивать параметры вручную, иначе символ амперсанд или
  пробел в значении сломает запрос.""",
  clr(), t('from urllib.parse import urlencode\n\nparams = {"q": "учёт расходов", "page": 2}\n', at="Для этого есть"),
  t('print(urlencode(params))\n', at="Она заботится"), run("Нельзя склеивать")),
 S("methods", "Методы и коды состояния", """
  В запросе указан метод: GET — получить данные, POST — создать новые, PUT — заменить, DELETE — удалить. Ответ начинается с
  трёхзначного кода состояния. Коды на двести означают успех, на четыреста — ошибку клиента, например четыреста четыре — ресурс не
  найден, а на пятьсот — ошибку сервера. Напишем функцию, которая по коду определяет, как действовать приложению.""",
  clr(), t('def describe(code):\n    if 200 <= code < 300:\n        return "успех"\n    if 400 <= code < 500:\n        return "ошибка клиента"\n    if 500 <= code < 600:\n        return "ошибка сервера"\n    return "другое"\n\n', at="Напишем функцию"),
  t("for code in (200, 201, 404, 500, 301):\n    print(code, describe(code))\n", at="Напишем функцию"), run("Напишем функцию")),
 S("raw", "Разбор сырого ответа", """
  Сырой ответ сервера — это обычный текст. Первая строка содержит версию протокола, код состояния и пояснение. Дальше идут
  заголовки в формате «имя двоеточие значение», затем пустая строка и тело ответа. Разберём такой ответ вручную: разделим
  по пустой строке на голову и тело, а голову — по строкам. Тело в формате JSON превратим в данные.""",
  clr(), t('import json\n\nraw = "HTTP/1.1 200 OK\\nContent-Type: application/json\\nContent-Length: 27\\n\\n{\\"id\\": 7, \\"done\\": false}"\n', at="Сырой ответ"),
  t('head, body = raw.split("\\n\\n", 1)\nlines = head.split("\\n")\nstatus = int(lines[0].split()[1])\n', at="Разберём такой"),
  t('headers = dict(line.split(": ", 1) for line in lines[1:])\ndata = json.loads(body)\n', at="Разберём такой"),
  t("print(status, headers[\"Content-Type\"], data)\n", at="Тело в формате"), run("Тело в формате")),
 S("summary", "Итог", """
  Подведём итог. HTTP — это запросы и ответы в текстовом виде. Адрес состоит из схемы, хоста, пути и параметров, и разбирать его
  нужно через urllib точка parse, а не вручную. Методы GET, POST, PUT и DELETE описывают намерение клиента, а код состояния
  в ответе сообщает, чем всё закончилось. Если приложению придёт ответ с кодом четыреста четыре или пятьсот, оно должно
  уметь корректно это обработать. Следующий шаг в курсе — переход к алгоритмам.""",
  nt("`GET/POST/PUT/DELETE` · `2xx` успех · `4xx` ошибка клиента · `5xx` ошибка сервера", at="Подведём итог")),
]

notes = """
# HTTP без сети

```python
from urllib.parse import urlparse, parse_qs, urlencode

url = "https://api.example.com/tasks?status=open&limit=5"
parts = urlparse(url)
print(parts.scheme, parts.netloc, parts.path)   # https api.example.com /tasks
print(parse_qs(parts.query))                    # {'status': ['open'], 'limit': ['5']}
print(urlencode({"q": "учёт", "page": 2}))
```

## Коды состояния

| Код | Смысл |
|---|---|
| 200 | OK |
| 201 | Создано |
| 301 | Перенаправление |
| 404 | Не найдено |
| 500 | Ошибка сервера |

## Сырой ответ

```python
import json

raw = "HTTP/1.1 200 OK\\nContent-Type: application/json\\n\\n{\\"id\\": 7}"
head, body = raw.split("\\n\\n", 1)
lines = head.split("\\n")
status = int(lines[0].split()[1])
headers = dict(line.split(": ", 1) for line in lines[1:])
print(status, headers["Content-Type"], json.loads(body))
```

## Запомните

1. Адрес разбирайте через `urllib.parse`.
2. Параметры собирайте через `urlencode` — он экранирует символы.
3. Всегда проверяйте код состояния, прежде чем читать тело.
"""

a1 = fn_task("a1-parse-url", "Разбор адреса", "Напишите функцию `parse_url(url)`, которая возвращает словарь с ключами `\"host\"` (имя сервера), `\"path\"` и `\"params\"` (словарь параметров запроса, где значение — **строка**, а при повторе параметра берётся первое значение).\n\nПример: `parse_url(\"https://api.example.com/tasks?status=open&limit=5\")` → `{\"host\": \"api.example.com\", \"path\": \"/tasks\", \"params\": {\"status\": \"open\", \"limit\": \"5\"}}`.",
  "parse_url", 'from urllib.parse import urlparse, parse_qs\n\n\ndef parse_url(url):\n    parts = urlparse(url)\n    params = {key: values[0] for key, values in parse_qs(parts.query).items()}\n    return {"host": parts.netloc, "path": parts.path, "params": params}\n',
  [["https://api.example.com/tasks?status=open&limit=5"], ["http://site.org/"], (["https://a.b/c/d?x=1&x=2"], True), (["https://shop.pl/items?q=%D1%87%D0%B0%D0%B9"], True), (["https://h.com/p"], True)],
  [('from urllib.parse import urlparse, parse_qs\n\n\ndef parse_url(url):\n    parts = urlparse(url)\n    return {"host": parts.netloc, "path": parts.path, "params": parse_qs(parts.query)}\n', "Значения параметров остались списками вместо строк."),
   ('from urllib.parse import urlparse, parse_qs\n\n\ndef parse_url(url):\n    parts = urlparse(url)\n    params = {key: values[-1] for key, values in parse_qs(parts.query).items()}\n    return {"host": parts.netloc, "path": parts.path, "params": params}\n', "При повторе параметра берётся последнее значение, а нужно первое.")],
  hints("Адрес состоит из схемы, хоста, пути и параметров.", "Для разбора есть urllib.parse.urlparse.", "Поле netloc — хост, path — путь, query — строка параметров.", "parse_qs превращает строку параметров в словарь со значениями-списками.", "Возьмите у каждого списка первый элемент: {k: v[0] ...}."),
  "urlparse разбирает адрес, parse_qs — параметры и одновременно декодирует экранированные символы.")

a2 = fn_task("a2-build-url", "Сборка адреса", "Напишите функцию `build_url(base, params)`: добавляет параметры к адресу `base` (в котором параметров ещё нет) с помощью `urlencode`. Для пустого словаря верните `base` без вопросительного знака.\n\nПримеры: `build_url(\"https://x.com/search\", {\"q\": \"чай\", \"page\": 2})` → `\"https://x.com/search?q=%D1%87%D0%B0%D0%B9&page=2\"`; `build_url(\"https://x.com\", {})` → `\"https://x.com\"`.",
  "build_url", 'from urllib.parse import urlencode\n\n\ndef build_url(base, params):\n    if not params:\n        return base\n    return base + "?" + urlencode(params)\n',
  [["https://x.com/search", {"q": "чай", "page": 2}], ["https://x.com", {}], (["https://a.pl/p", {"name": "Аня Б", "x": "a&b"}], True), (["https://a.pl/p", {"k": 1}], True)],
  [('def build_url(base, params):\n    return base + "?" + "&".join(f"{k}={v}" for k, v in params.items())\n', "Параметры склеены вручную: нет экранирования и лишний «?» при пустом словаре."),
   ('from urllib.parse import urlencode\n\n\ndef build_url(base, params):\n    return base + "?" + urlencode(params)\n', "Для пустого словаря добавлен лишний вопросительный знак.")],
  hints("Параметры нельзя склеивать вручную: пробелы и спецсимволы сломают адрес.", "В urllib.parse есть функция urlencode.", "urlencode принимает словарь и возвращает строку параметров.", "Между адресом и параметрами ставится вопросительный знак.", "Если параметров нет, верните base без изменений."),
  "urlencode экранирует спецсимволы и кириллицу; без параметров вопросительный знак не нужен.")

a3 = fn_task("a3-status", "Что делать с кодом", "Напишите функцию `action(code)`: для кодов 200–299 вернуть `\"ok\"`, для 301 и 302 — `\"redirect\"`, для 404 — `\"not_found\"`, для остальных 400–499 — `\"client_error\"`, для 500–599 — `\"retry\"`, для всего прочего — `\"unknown\"`.",
  "action", 'def action(code):\n    if 200 <= code < 300:\n        return "ok"\n    if code in (301, 302):\n        return "redirect"\n    if code == 404:\n        return "not_found"\n    if 400 <= code < 500:\n        return "client_error"\n    if 500 <= code < 600:\n        return "retry"\n    return "unknown"\n',
  [[200], [404], [500], ([201], True), ([299], True), ([300], True), ([302], True), ([403], True), ([503], True), ([100], True), ([600], True)],
  [('def action(code):\n    if 200 <= code < 300:\n        return "ok"\n    if code in (301, 302):\n        return "redirect"\n    if 400 <= code < 500:\n        return "client_error"\n    if code == 404:\n        return "not_found"\n    if 500 <= code < 600:\n        return "retry"\n    return "unknown"\n', "Проверка 4xx стоит раньше 404, поэтому «not_found» недостижим."),
   ('def action(code):\n    if 200 <= code <= 300:\n        return "ok"\n    if code in (301, 302):\n        return "redirect"\n    if code == 404:\n        return "not_found"\n    if 400 <= code < 500:\n        return "client_error"\n    if 500 <= code < 600:\n        return "retry"\n    return "unknown"\n', "Граница включает код 300 (он не успех)."),
   ('def action(code):\n    if 200 <= code < 300:\n        return "ok"\n    if code in (301, 302):\n        return "redirect"\n    if code == 404:\n        return "not_found"\n    if 400 <= code < 500:\n        return "client_error"\n    if 500 <= code <= 600:\n        return "retry"\n    return "unknown"\n', "Граница включает код 600, которого не существует среди серверных ошибок.")],
  hints("Код определяет, как действовать: принять, перейти, исправить запрос или повторить.", "Диапазоны удобно записывать цепочкой сравнений: 200 <= code < 300.", "Конкретные коды (301, 302, 404) проверяйте раньше общих диапазонов.", "Правая граница диапазона не включается: 300 уже не успех.", "В конце верните «unknown» для всего, что не подошло."),
  "Сначала частные случаи (404), потом общий диапазон (4xx) — иначе частный случай никогда не сработает.")

a4 = fn_task("a4-parse-response", "Разбор ответа сервера", "Напишите функцию `parse_response(raw)`: `raw` — текст ответа. Первая строка `HTTP/1.1 КОД ТЕКСТ`, затем заголовки `Имя: значение`, пустая строка и тело. Верните словарь `{\"status\": код (int), \"headers\": словарь заголовков, \"body\": тело (строка)}`. Тело может быть пустым.",
  "parse_response", 'def parse_response(raw):\n    head, _, body = raw.partition("\\n\\n")\n    lines = head.split("\\n")\n    status = int(lines[0].split()[1])\n    headers = dict(line.split(": ", 1) for line in lines[1:] if line)\n    return {"status": status, "headers": headers, "body": body}\n',
  [["HTTP/1.1 200 OK\nContent-Type: text/plain\n\nпривет"], ["HTTP/1.1 404 Not Found\nContent-Length: 0\n\n"], (["HTTP/1.1 201 Created\nContent-Type: application/json\nX-Id: 7\n\n{\"id\": 7}"], True), (["HTTP/1.1 500 Server Error\n\nошибка\n\nна сервере"], True)],
  [('def parse_response(raw):\n    head, body = raw.split("\\n\\n")\n    lines = head.split("\\n")\n    headers = dict(line.split(": ", 1) for line in lines[1:])\n    return {"status": int(lines[0].split()[1]), "headers": headers, "body": body}\n', "Разделение по всем пустым строкам ломает тело с пустой строкой внутри, а при отсутствии заголовков падает."),
   ('def parse_response(raw):\n    head, _, body = raw.partition("\\n\\n")\n    lines = head.split("\\n")\n    headers = dict(line.split(": ", 1) for line in lines[1:] if line)\n    return {"status": lines[0].split()[1], "headers": headers, "body": body}\n', "Код состояния оставлен строкой, а нужно число.")],
  hints("Ответ делится на голову и тело пустой строкой.", "Голова — это первая строка (статус) и заголовки.", "raw.partition('\\n\\n') делит только по первому разделителю и не падает, если тела нет.", "Код — второе слово первой строки; превратите в int.", "Заголовки: dict(line.split(': ', 1) for line in остальные_строки)."),
  "partition делит по первому разделителю, поэтому тело может содержать пустые строки; код состояния превращаем в число для сравнений.")

a5 = predict_task("a5-qs", "Параметры запроса", 'from urllib.parse import urlparse, parse_qs\n\nparts = urlparse("https://x.org/a/b?tag=py&tag=sql&n=3")\nq = parse_qs(parts.query)\nprint(parts.path, q["tag"], int(q["n"][0]) + 1)\n',
  [("/a/b py 4\n", "Значения parse_qs — списки: q['tag'] печатается как список."),
   ("/a/b ['py', 'sql'] 3\n", "К n прибавляется единица: 3 + 1 = 4.")],
  hints("path — это часть адреса после хоста.", "parse_qs возвращает словарь со значениями-списками.", "tag встречается дважды, поэтому в списке два значения.", "q['n'] — список ['3'], берём первый элемент.", "int('3') + 1 = 4."),
  "parse_qs собирает повторяющиеся параметры в список; значения всегда строки.")

mistakes = [
 {"mistake": "Склеивают адрес и параметры строками вручную", "fix": "Используйте urlencode: он экранирует пробелы и спецсимволы."},
 {"mistake": "Забывают, что значения parse_qs — списки", "fix": "Берите нужный элемент: q['n'][0]."},
 {"mistake": "Читают тело ответа, не проверив код состояния", "fix": "Сначала проверьте status: при 4xx/5xx тело может быть сообщением об ошибке."},
 {"mistake": "Сравнивают код состояния как строку", "fix": "Преобразуйте в int: int('404')."}]

finish("py-23-http", "HTTP и работа с адресами", "Разбирать адреса и параметры, понимать методы и коды состояния, читать сырой HTTP-ответ.",
  {"python.http": "Основы HTTP", "python.http.url": "Адреса и параметры (urllib.parse)", "python.http.status": "Коды состояния"},
  ["py-22-async"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="python-core")

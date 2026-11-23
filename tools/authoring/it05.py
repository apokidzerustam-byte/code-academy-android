from lib import *

begin()
scenes = [
 S("intro", "Клиент и сервер", """
  Когда вы открываете сайт или приложение, ваше устройство отправляет запрос, а другой компьютер, сервер, присылает ответ.
  Устройство, которое просит, называется клиентом. Компьютер, который отвечает, — сервером. Клиентская часть, фронтенд, — это то,
  что вы видите на экране. Серверная часть, бэкенд, хранит данные и выполняет вычисления, которые не должны попадать
  на устройство пользователя.""",
  nt("**Клиент** просит · **сервер** отвечает · фронтенд ↔ бэкенд", at="Клиентская часть")),
 S("url", "Адрес в сети", """
  Каждый ресурс в сети имеет адрес — URL. В нём несколько частей: схема, например https, имя сервера, путь к странице и
  параметры запроса после знака вопроса. В Python разобрать адрес на части умеет модуль urllib.parse. Функция urlparse
  вернёт схему, хост и путь, а функция parse_qs превратит параметры в словарь.""",
  clr(), t('from urllib.parse import urlparse, parse_qs\n\nurl = "https://example.com/search?q=python&page=2"\nparts = urlparse(url)\nprint(parts.scheme)\nprint(parts.netloc)\nprint(parts.path)\nprint(parse_qs(parts.query))\n', at="В Python"), run("В Python")),
 S("http", "Запрос и ответ HTTP", """
  Клиент и сервер общаются по протоколу HTTP. Запрос состоит из метода, пути и заголовков. Метод GET означает «дай данные»,
  POST — «прими данные», PUT — «обнови», DELETE — «удали». Ответ начинается с кода состояния и содержит тело. Запрос и
  ответ — всего лишь текст, и его можно разобрать на части обычными строковыми методами.""",
  clr(), t('request = "GET /users/7 HTTP/1.1"\nmethod, path, version = request.split()\nprint(method)\nprint(path)\nprint(version)\n', at="Запрос и"), run("Запрос и")),
 S("status", "Коды состояния", """
  Код состояния в ответе сообщает, чем всё закончилось. Коды на двести означают успех. Коды на триста — перенаправление. Коды на
  четыреста говорят об ошибке клиента: например, четыреста четыре — страница не найдена. Коды на пятьсот — ошибка сервера.
  Достаточно знать первую цифру, чтобы понять, чья это проблема.""",
  clr(), t('def kind(code):\n    first = code // 100\n    return {2: "успех", 3: "перенаправление", 4: "ошибка клиента", 5: "ошибка сервера"}.get(first, "неизвестно")\n\n\n', at="Код состояния"),
  t('for code in [200, 301, 404, 500]:\n    print(code, kind(code))\n', at="Достаточно"), run("Достаточно")),
 S("json", "Формат JSON", """
  Данные между клиентом и сервером чаще всего передают в формате JSON. Он выглядит как словарь Python: ключи в двойных
  кавычках, значения — числа, строки, списки и вложенные объекты. Модуль json превращает строку в объекты Python и обратно.
  Когда мы будем писать сервер на FastAPI, он будет делать это автоматически.""",
  clr(), t('import json\n\ntext = \'{"name": "Анна", "age": 21, "langs": ["python", "sql"]}\'\ndata = json.loads(text)\nprint(data["name"])\nprint(len(data["langs"]))\nprint(json.dumps({"ok": True}))\n', at="Модуль json"), run("Модуль json")),
 S("summary", "Итог", """
  Подведём итог. Клиент отправляет запрос, сервер возвращает ответ. Адрес состоит из схемы, хоста, пути и параметров. Запрос
  HTTP начинается с метода, а ответ — с кода состояния: первая цифра подскажет, чья ошибка. Данные обычно передают в JSON.
  На этом знакомство с основами закончено: дальше вы настроите телефон и начнёте писать настоящий код.""",
  nt("метод + путь → ответ + код · JSON — формат обмена", at="Подведём итог")),
]

notes = """
# Клиент, сервер и HTTP

```python
from urllib.parse import urlparse, parse_qs

parts = urlparse("https://example.com/search?q=python&page=2")
print(parts.netloc)          # example.com
print(parse_qs(parts.query)) # {'q': ['python'], 'page': ['2']}
```

| Метод | Смысл |
|---|---|
| GET | получить данные |
| POST | отправить данные |
| PUT | обновить |
| DELETE | удалить |

| Код | Значение |
|---|---|
| 2xx | успех |
| 3xx | перенаправление |
| 4xx | ошибка клиента |
| 5xx | ошибка сервера |
"""

a1 = predict_task("a1-url", "Части адреса",
  'from urllib.parse import urlparse\n\np = urlparse("https://shop.example.org/items/42?color=red")\nprint(p.scheme)\nprint(p.netloc)\nprint(p.path)\nprint(p.query)\n',
  [("https\nshop.example.org\n/items/42?color=red\ncolor=red", "Путь не включает параметры после знака вопроса."), ("http\nshop.example.org\n/items/42\ncolor=red", "Схема здесь https.")],
  hints("Адрес делится на схему, хост, путь и параметры.", "Схема — всё до двоеточия.", "Хост идёт после двух слешей.", "Путь заканчивается перед знаком вопроса.", "Параметры — после знака вопроса, без самого знака."),
  "urlparse раскладывает адрес: схема https, хост shop.example.org, путь /items/42, запрос color=red.")

a2 = fn_task("a2-status-kind", "Что означает код",
  "Напишите `status_kind(code)`: верните `\"success\"` для кодов 200–299, `\"redirect\"` для 300–399, `\"client_error\"` для 400–499, `\"server_error\"` для 500–599, иначе `\"unknown\"`.",
  "status_kind", "def status_kind(code):\n    if 200 <= code < 300:\n        return \"success\"\n    if 300 <= code < 400:\n        return \"redirect\"\n    if 400 <= code < 500:\n        return \"client_error\"\n    if 500 <= code < 600:\n        return \"server_error\"\n    return \"unknown\"\n",
  [[200], [404], ([301], True), ([500], True), ([299], True), ([399], True), ([100], True), ([600], True), ([499], True)],
  [("def status_kind(code):\n    if code <= 299:\n        return \"success\"\n    if code <= 399:\n        return \"redirect\"\n    if code <= 499:\n        return \"client_error\"\n    return \"server_error\"\n", "Коды ниже 200 и выше 599 не распознаются как неизвестные.")],
  hints("Код определяется диапазоном.", "Сравнивайте со сотнями.", "200 ≤ код < 300 — успех.", "Остальные диапазоны — по тому же принципу.", "Всё, что не попало ни в один диапазон, — неизвестный код."),
  "Диапазоны кодов HTTP: 2xx успех, 3xx перенаправление, 4xx ошибка клиента, 5xx ошибка сервера.")

a3 = fn_task("a3-parse-request", "Разбор запроса",
  "Напишите `parse_request(line)`: по строке вида `\"GET /users/7 HTTP/1.1\"` верните кортеж `(method, path)`.",
  "parse_request", "def parse_request(line):\n    method, path, _ = line.split()\n    return (method, path)\n",
  [["GET /users/7 HTTP/1.1"], ["POST /login HTTP/1.1"], (["DELETE /items/3 HTTP/1.1"], True), (["GET / HTTP/1.1"], True), (["PUT /a/b/c HTTP/2"], True)],
  [("def parse_request(line):\n    parts = line.split()\n    return (parts[0], parts[1], parts[2])\n", "Возвращается лишний элемент — версия протокола.")],
  hints("Строка запроса — три слова через пробел.", "Разделите её по пробелам.", "Метод — первое слово, путь — второе.", "Версия протокола в ответ не нужна.", "Верните кортеж из двух элементов."),
  "split() по пробелам делит строку запроса на метод, путь и версию протокола.")

a4 = fn_task("a4-query", "Параметры запроса",
  "Напишите `get_param(url, name)`: верните значение параметра `name` из адреса `url` (первое, если их несколько) или `None`, если такого параметра нет. Используйте `urllib.parse`.",
  "get_param", "from urllib.parse import urlparse, parse_qs\n\n\ndef get_param(url, name):\n    values = parse_qs(urlparse(url).query).get(name)\n    return values[0] if values else None\n",
  [["https://a.com/s?q=python&page=2", "q"], ["https://a.com/s?q=python&page=2", "page"], (["https://a.com/s", "q"], True), (["https://a.com/s?x=1&x=2", "x"], True), (["https://a.com/s?q=a", "z"], True)],
  [("from urllib.parse import urlparse, parse_qs\n\n\ndef get_param(url, name):\n    return parse_qs(urlparse(url).query).get(name)\n", "Возвращается список, а не строка.")],
  hints("Параметры лежат в части запроса адреса.", "Часть запроса получите из разобранного адреса.", "Превратите её в словарь специальной функцией из того же модуля.", "Значения в словаре — списки.", "Если параметра нет, верните None."),
  "parse_qs возвращает словарь «имя → список значений»: нужное значение — первый элемент списка.")

a5 = predict_task("a5-json", "JSON и Python",
  'import json\n\ntext = \'{"items": [{"price": 10}, {"price": 25}], "tax": 0.2}\'\ndata = json.loads(text)\ntotal = sum(i["price"] for i in data["items"])\nprint(total)\nprint(total * (1 + data["tax"]))\nprint(type(data["items"]).__name__)\n',
  [("35\n35.2\nlist", "Налог 0.2 — это 20 %, а не 0.2 единицы."), ("35\n42.0\ndict", "Массив JSON превращается в список Python.")],
  hints("loads превращает текст в объекты Python.", "data[\"items\"] — список из двух словарей.", "Сумма цен: 10 + 25.", "Налог 20 % увеличивает сумму в 1.2 раза.", "Массив JSON — это list."),
  "JSON-объект становится словарём, массив — списком; числа и вложенность сохраняются.")

mistakes = [
 {"mistake": "Путают клиента и сервер", "fix": "Клиент отправляет запрос, сервер отвечает."},
 {"mistake": "Считают, что значение параметра в parse_qs — строка", "fix": "Это список строк."},
 {"mistake": "Не различают коды 4xx и 5xx", "fix": "4xx — ошибка клиента, 5xx — сервера."},
 {"mistake": "Пишут JSON с одинарными кавычками", "fix": "В JSON — только двойные."}]

finish("it-05-client-server", "Клиент, сервер и HTTP", "Объяснять, как клиент и сервер обмениваются данными, и разбирать адреса, запросы и JSON.",
  {"it.http": "HTTP и URL", "it.client-server": "Клиент и сервер", "it.json": "Формат JSON"},
  ["it-04-algorithms"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="it-intro")

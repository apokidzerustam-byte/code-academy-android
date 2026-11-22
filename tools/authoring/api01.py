"""Урок FastAPI 1: веб-API на Python. Запросы выполняются TestClient'ом без сети (режим A — Chaquopy).
Вывод сцен сверяет валидатор в CI настоящим FastAPI (pip fastapi==0.125.0, pydantic==1.10.27)."""
from mk import *

HEAD = "from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\n"
C1 = HEAD + '\n\n@app.get("/")\ndef root():\n    return {"message": "Привет"}\n'
REQ1 = '\n\nclient = TestClient(app)\nr = client.get("/")\nprint(r.status_code, r.json())\n'
C2 = HEAD + '\n\n@app.get("/items/{item_id}")\ndef get_item(item_id: int):\n    return {"item_id": item_id, "double": item_id * 2}\n'
REQ2 = '\n\nclient = TestClient(app)\nprint(client.get("/items/5").json())\nprint(client.get("/items/abc").status_code)\n'
C3 = HEAD + '\n\n@app.get("/search")\ndef search(q: str = "", limit: int = 3):\n    words = ["кот", "код", "компот", "кофе", "сок"]\n    found = [w for w in words if q in w]\n    return {"q": q, "found": found[:limit]}\n'
REQ3 = '\n\nclient = TestClient(app)\nprint(client.get("/search", params={"q": "ко"}).json())\nprint(client.get("/search", params={"q": "ко", "limit": 1}).json())\n'
C4 = ("from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\nfrom pydantic import BaseModel\n\napp = FastAPI()\n\n\n"
      "class Item(BaseModel):\n    name: str\n    price: float\n    qty: int = 1\n\n\n"
      '@app.post("/items")\ndef create_item(item: Item):\n    return {"name": item.name, "total": item.price * item.qty}\n')
REQ4 = ('\n\nclient = TestClient(app)\nr = client.post("/items", json={"name": "Чай", "price": 2.5, "qty": 4})\nprint(r.status_code, r.json())\n'
        'r = client.post("/items", json={"name": "Чай"})\nprint(r.status_code)\n')
C5 = ("from fastapi import FastAPI, HTTPException\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\n"
      'BOOKS = {1: "Война и мир", 2: "Мастер и Маргарита"}\n\n\n'
      '@app.get("/books/{book_id}")\ndef get_book(book_id: int):\n    if book_id not in BOOKS:\n'
      '        raise HTTPException(status_code=404, detail="Книга не найдена")\n    return {"id": book_id, "title": BOOKS[book_id]}\n')
REQ5 = '\n\nclient = TestClient(app)\nprint(client.get("/books/2").json())\nr = client.get("/books/7")\nprint(r.status_code, r.json())\n'

O1 = "200 {'message': 'Привет'}\n"
O2 = "{'item_id': 5, 'double': 10}\n422\n"
O3 = "{'q': 'ко', 'found': ['кот', 'код', 'компот']}\n{'q': 'ко', 'found': ['кот']}\n"
O4 = "200 {'name': 'Чай', 'total': 10.0}\n422\n"
O5 = "{'id': 2, 'title': 'Мастер и Маргарита'}\n404 {'detail': 'Книга не найдена'}\n"

scenes = [
    scene("intro", "Что такое веб-API", """
      Когда приложение в телефоне показывает погоду или список заказов, оно обращается к серверу по адресу и
      получает данные, обычно в формате JSON. Такой набор адресов и правил называется веб-API. Запрос состоит из
      метода и пути: GET — получить данные, POST — отправить новые. Сервер отвечает кодом: двести — всё хорошо,
      четыреста четыре — не найдено, четыреста двадцать два — неверные данные. Сегодня напишем свой API на
      Питоне с помощью библиотеки FastAPI.""",
          [NOTE("Запрос: **метод** (GET, POST) + **путь** (`/items/5`). Ответ: **код** (200, 404, 422) + **JSON**.", at="Запрос состоит"),
           NOTE("Коды: `200` — ок, `404` — не найдено, `422` — неверные данные.", at="Сервер отвечает")]),
    scene("first", "Первое приложение", """
      Импортируем FastAPI и создаём приложение app. Обработчик — обычная функция, а строка с собакой над ней,
      декоратор, говорит: на запрос GET по пути косая черта вызывай эту функцию. Функция возвращает словарь,
      а FastAPI сам превращает его в JSON.""",
          [CLEAR(), T(C1, at="Импортируем"), HL([4], at="Импортируем"), HL([7, 8, 9], at="Обработчик"), HL([9], at="Функция возвращает")]),
    scene("client", "Запрос без сети", """
      На компьютере такое приложение запускают сервером uvicorn и открывают в браузере. В приложении сеть закрыта,
      поэтому используем тестовый клиент: он передаёт запрос прямо в app, как настоящий браузер, но без интернета.
      client точка get отправляет запрос, у ответа есть код status_code и метод json. Запускаем. Код двести и наш словарь.""",
          [T(REQ1, at="поэтому используем"), HL([12, 13, 14], at="client точка get"), RUN(at="Запускаем"), OUT(O1, at="Запускаем")]),
    scene("path", "Параметр в пути", """
      Часть пути может быть параметром: фигурные скобки item_id. FastAPI передаёт его в функцию с тем же именем.
      Аннотация двоеточие int важна: FastAPI сам превратит текст из адреса в число и проверит его. Запросим
      пятый товар — получаем число и удвоенное число. А если в пути не число, FastAPI отвечает кодом четыреста
      двадцать два, и наша функция даже не вызывается.""",
          [CLEAR(), T(C2 + REQ2, at="Часть пути"), HL([7], at="Часть пути"), HL([8], at="Аннотация"), RUN(at="Запросим"),
           OUT(O2, at="Запросим"), HL([14], at="А если в пути")]),
    scene("query", "Параметры запроса", """
      Параметры, которых нет в пути, FastAPI берёт из строки запроса после вопросительного знака, например
      search вопрос q равно ко. У параметров могут быть значения по умолчанию: limit равен трём, если его не
      передали. Тестовый клиент передаёт их словарём params. Запускаем.""",
          [CLEAR(), T(C3 + REQ3, at="Параметры, которых"), HL([8], at="У параметров"), HL([15, 16], at="Тестовый клиент"),
           RUN(at="Запускаем"), OUT(O3, at="Запускаем")]),
    scene("post", "POST и модель данных", """
      Для отправки данных используют POST, а форму данных описывают классом-моделью на основе BaseModel из
      библиотеки pydantic. У товара есть название, цена и количество, по умолчанию один. Обработчик получает уже
      проверенный объект item. Отправим JSON с чаем: итог десять. А если цены нет, FastAPI сам вернёт
      четыреста двадцать два с описанием, какого поля не хватает.""",
          [CLEAR(), T(C4 + REQ4, at="Для отправки"), HL([8, 9, 10, 11], at="форму данных"), HL([14, 15, 16], at="Обработчик получает"),
           RUN(at="Отправим"), OUT(O4, at="Отправим")]),
    scene("errors", "Свои ошибки: 404", """
      Иногда ошибку должен вернуть сам обработчик, например если книги с таким номером нет. Для этого
      поднимают исключение HTTPException с кодом и пояснением detail. Запросим вторую книгу и седьмую.
      Вторая нашлась, а для седьмой код четыреста четыре и наше сообщение.""",
          [CLEAR(), T(C5 + REQ5, at="Иногда"), HL([10, 11], at="поднимают"), RUN(at="Запросим"), OUT(O5, at="Вторая нашлась")]),
    scene("summary", "Итоги", """
      Итак: app равно FastAPI, декораторы get и post связывают путь с функцией, параметры берутся из пути и строки
      запроса, а тело запроса описывает модель BaseModel. Аннотации типов включают проверку, неверные данные
      дают четыреста двадцать два, а свою ошибку возвращают через HTTPException. В заданиях проверка
      отправляет запросы к вашему app и сравнивает код и JSON ответа.""",
          [NOTE("На компьютере: `pip install fastapi uvicorn`, затем `uvicorn main:app --reload` и адрес http://127.0.0.1:8000/docs.", at="Итак")]),
]

notes = """
# FastAPI: свой веб-API

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/items/{item_id}")          # параметр пути
def get_item(item_id: int, q: str = ""):   # q — параметр запроса ?q=...
    return {"item_id": item_id, "q": q}

class Item(BaseModel):                # тело запроса (JSON)
    name: str
    price: float

@app.post("/items")
def create(item: Item):
    return {"name": item.name}

@app.get("/books/{book_id}")
def book(book_id: int):
    raise HTTPException(status_code=404, detail="Не найдено")
```

## Проверка в приложении — без сети
```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int, q: str = ""):
    return {"item_id": item_id, "q": q}

client = TestClient(app)
r = client.get("/items/5", params={"q": "чай"})
print(r.status_code, r.json())   # 200 {'item_id': 5, 'q': 'чай'}
```

## Коды ответа
| Код | Когда |
|---|---|
| 200 | всё хорошо |
| 404 | не найдено (`HTTPException(404)`) |
| 422 | данные не прошли проверку типов (FastAPI сам) |

## На компьютере
`pip install fastapi uvicorn`, затем `uvicorn main:app --reload` → http://127.0.0.1:8000/docs — автоматическая документация.

## Частые ошибки
- Нет аннотации типа: `def add(a, b)` — параметры придут строками, `a + b` склеит их.
- Имя параметра в пути и в функции не совпадает.
- Функция ничего не возвращает — ответ `null`.
- Забыли `app = FastAPI()` или назвали приложение иначе.
"""

IMP = "from fastapi import FastAPI\n\napp = FastAPI()\n"

# --- Задание 1: первый обработчик --------------------------------------------------
S1 = IMP + '\n\n@app.get("/hello")\ndef hello():\n    return {"text": "Привет, API!"}\n'
t1 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "GET", "path": "/hello", "expected_status": 200, "expected_json": {"text": "Привет, API!"}},
    {"id": "h2", "hidden": True, "method": "POST", "path": "/hello", "expected_status": 405,
     "hint": "Обработчик — для метода GET"},
]}
a1 = asg("a1-hello", "write", "Первый адрес API",
         "Добавьте в приложение обработчик: на запрос **GET** `/hello` он возвращает JSON `{\"text\": \"Привет, API!\"}`.",
         "Связывать путь и функцию декоратором.", "Запрос GET /hello.", "Код 200 и JSON с ключом text.",
         ["Приложение должно называться app.", "Нажмите «Запустить», чтобы проверить, что код без ошибок."],
         hints("Обработчик — функция с декоратором над ней.",
               "Декоратор для GET: @app.get(\"путь\").",
               "Путь начинается с косой черты: \"/hello\".",
               "Функция возвращает словарь — FastAPI превратит его в JSON.",
               "@app.get(\"/hello\")\ndef hello():\n    return {\"text\": \"Привет, API!\"}"),
         t1, S1, "@app.get(\"/hello\") связывает GET-запрос по пути /hello с функцией; словарь становится JSON-ответом.",
         ["GET /hello → 200 и нужный JSON.", "Другие пути и методы не отвечают."],
         [(IMP + '\n\n@app.get("/")\ndef hello():\n    return {"text": "Привет, API!"}\n', "Путь «/» вместо «/hello»."),
          (IMP + '\n\n@app.post("/hello")\ndef hello():\n    return {"text": "Привет, API!"}\n', "Нужен GET, а не POST."),
          (IMP + '\n\n@app.get("/hello")\ndef hello():\n    return "Привет, API!"\n', "Вернулась строка, а нужен JSON-объект с ключом text."),
          (IMP + '\n\n@app.get("/hello")\ndef hello():\n    print({"text": "Привет, API!"})\n', "Функция печатает, а не возвращает — ответ null.")],
         starter=IMP + "\n# ваш обработчик\n")

# --- Задание 2: параметр пути ---------------------------------------------------------
S2 = IMP + '\n\n@app.get("/square/{n}")\ndef square(n: int):\n    return {"n": n, "square": n * n}\n'
t2 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/square/4", "expected_json": {"n": 4, "square": 16}},
    {"id": "v2", "path": "/square/0", "expected_json": {"n": 0, "square": 0}},
    {"id": "h1", "hidden": True, "path": "/square/-3", "expected_json": {"n": -3, "square": 9}, "hint": "Отрицательные числа тоже"},
    {"id": "h2", "hidden": True, "path": "/square/12", "expected_json": {"n": 12, "square": 144}},
    {"id": "h3", "hidden": True, "path": "/square/abc", "expected_status": 422,
     "hint": "Не число в пути должно давать 422 — укажите тип параметра"},
]}
a2 = asg("a2-square", "write", "Квадрат числа",
         "Сделайте адрес **GET** `/square/{n}`: он возвращает `{\"n\": n, \"square\": n²}`.\n\n"
         "Например, `/square/4` → `{\"n\": 4, \"square\": 16}`. Если в пути не число — код **422**.",
         "Принимать параметр из пути с типом int.", "Целое n в пути.", "JSON с n и квадратом.",
         ["n — целое, может быть отрицательным."],
         hints("Параметр пути пишут в фигурных скобках: \"/square/{n}\".",
               "Имя в скобках и имя параметра функции совпадают.",
               "Укажите тип: n: int — тогда FastAPI сам проверит и превратит в число.",
               "Квадрат — n * n.",
               "@app.get(\"/square/{n}\")\ndef square(n: int):\n    return {\"n\": n, \"square\": n * n}"),
         t2, S2, "{n} в пути передаётся в функцию; аннотация int превращает текст в число, а «abc» даёт 422.",
         ["Верно для любых целых.", "Не число → 422."],
         [(IMP + '\n\n@app.get("/square/{n}")\ndef square(n):\n    return {"n": n, "square": n * n}\n',
           "Без типа n — строка: умножение строки на строку падает."),
          (IMP + '\n\n@app.get("/square/{n}")\ndef square(n: int):\n    return {"n": n, "square": n * 2}\n', "n * 2 — это удвоение, а не квадрат."),
          (IMP + '\n\n@app.get("/square/{num}")\ndef square(n: int):\n    return {"n": n, "square": n * n}\n',
           "Имя в пути (num) не совпадает с параметром функции (n).")],
         starter=IMP + "\n# ваш обработчик\n")

# --- Задание 3: исправить сложение строк -----------------------------------------------------
STARTER3 = IMP + '\n\n@app.get("/add")\ndef add(a, b):\n    return {"sum": a + b}\n'
S3 = STARTER3.replace("def add(a, b)", "def add(a: int, b: int)")
t3 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/add", "params": {"a": 2, "b": 3}, "expected_json": {"sum": 5}},
    {"id": "v2", "path": "/add", "params": {"a": 10, "b": -4}, "expected_json": {"sum": 6}},
    {"id": "h1", "hidden": True, "path": "/add", "params": {"a": 0, "b": 0}, "expected_json": {"sum": 0}},
    {"id": "h2", "hidden": True, "path": "/add", "params": {"a": "x", "b": 1}, "expected_status": 422,
     "hint": "Не число должно давать 422"},
    {"id": "h3", "hidden": True, "path": "/add", "params": {"a": 1}, "expected_status": 422,
     "hint": "Оба параметра обязательны"},
]}
a3 = asg("a3-fix", "fix", "2 + 3 = 23?",
         "Запрос `/add?a=2&b=3` должен вернуть `{\"sum\": 5}`, а возвращает `{\"sum\": \"23\"}`. Исправьте обработчик.",
         "Понимать, зачем нужны аннотации типов в FastAPI.", "Параметры запроса a и b.", "Сумма чисел.",
         ["Оба параметра обязательны.", "Не числа должны давать код 422."],
         hints("Запустите и подумайте: почему 2 и 3 «склеились»?",
               "Из адреса всё приходит текстом.",
               "FastAPI превращает текст в число, только если знает тип параметра.",
               "Добавьте аннотации типов обоим параметрам.",
               "def add(a: int, b: int):"),
         t3, S3, "Без аннотаций параметры — строки, и + склеивает их. С a: int, b: int FastAPI превращает их в числа и отвечает 422 на не числа.",
         ["Сумма чисел.", "Не число → 422."],
         [(STARTER3.replace("a + b", "int(a) + int(b)"), "Сумма верна, но «x» вызывает ошибку 500 вместо понятного 422."),
          (STARTER3.replace("def add(a, b)", "def add(a: int, b)"), "Тип указан только у a."),
          (STARTER3.replace("def add(a, b)", "def add(a: str, b: str)"), "Тип str — по-прежнему строки.")],
         starter=STARTER3)

# --- Задание 4: POST с моделью ------------------------------------------------------------
IMP4 = "from fastapi import FastAPI\nfrom pydantic import BaseModel\n\napp = FastAPI()\n"
S4 = (IMP4 + "\n\nclass Order(BaseModel):\n    product: str\n    qty: int\n    price: float\n\n\n"
      '@app.post("/orders")\ndef create_order(order: Order):\n    return {"product": order.product, "total": order.qty * order.price}\n')
t4 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "POST", "path": "/orders", "json": {"product": "Кофе", "qty": 2, "price": 3.5},
     "expected_json": {"product": "Кофе", "total": 7.0}},
    {"id": "h1", "hidden": True, "method": "POST", "path": "/orders", "json": {"product": "Сок", "qty": 3, "price": 1.25},
     "expected_json": {"product": "Сок", "total": 3.75}},
    {"id": "h2", "hidden": True, "method": "POST", "path": "/orders", "json": {"product": "Сок", "price": 1.25},
     "expected_status": 422, "hint": "Без qty заказ неполный — 422"},
    {"id": "h3", "hidden": True, "method": "POST", "path": "/orders", "json": {"product": "Сок", "qty": "много", "price": 1},
     "expected_status": 422, "hint": "qty должно быть целым числом"},
    {"id": "h4", "hidden": True, "method": "GET", "path": "/orders", "expected_status": 405, "hint": "Заказ создаётся методом POST"},
]}
a4 = asg("a4-order", "write", "Создать заказ",
         "Опишите модель `Order` с полями `product` (строка), `qty` (целое) и `price` (дробное). "
         "Сделайте **POST** `/orders`: он принимает заказ и возвращает `{\"product\": …, \"total\": qty × price}`.\n\n"
         "Если поля нет или тип неверный — код **422** (FastAPI сделает это сам).",
         "Принимать JSON через модель BaseModel.", "JSON заказа.", "JSON с product и total.",
         ["Все три поля обязательны."],
         hints("Модель — класс, унаследованный от BaseModel.",
               "Поля модели — аннотации: product: str, qty: int, price: float.",
               "Обработчик POST: @app.post(\"/orders\").",
               "Параметр функции с типом модели — это тело запроса: def create_order(order: Order).",
               "class Order(BaseModel):\n    product: str\n    qty: int\n    price: float\n\n@app.post(\"/orders\")\ndef create_order(order: Order):\n    return {\"product\": order.product, \"total\": order.qty * order.price}"),
         t4, S4, "BaseModel описывает тело запроса и проверяет типы; total считается из полей объекта.",
         ["Итог qty × price.", "Неполный заказ → 422."],
         [(IMP4 + "\n\nclass Order(BaseModel):\n    product: str\n    qty: int = 1\n    price: float\n\n\n"
           '@app.post("/orders")\ndef create_order(order: Order):\n    return {"product": order.product, "total": order.qty * order.price}\n',
           "qty необязательно — заказ без количества принимается."),
          (IMP4 + "\n\nclass Order(BaseModel):\n    product: str\n    qty: int\n    price: float\n\n\n"
           '@app.post("/orders")\ndef create_order(order: Order):\n    return {"product": order.product, "total": order.qty + order.price}\n',
           "Сложение вместо умножения."),
          (IMP4 + "\n\nclass Order(BaseModel):\n    product: str\n    qty: int\n    price: float\n\n\n"
           '@app.get("/orders")\ndef create_order(order: Order):\n    return {"product": order.product, "total": order.qty * order.price}\n',
           "Создание — метод POST, а не GET.")],
         starter=IMP4 + "\n# модель Order и обработчик POST /orders\n")

# --- Задание 5: 404 ---------------------------------------------------------------------
IMP5 = 'from fastapi import FastAPI, HTTPException\n\napp = FastAPI()\nUSERS = {1: "Аня", 2: "Борис", 3: "Вика"}\n'
S5 = (IMP5 + '\n\n@app.get("/users/{user_id}")\ndef get_user(user_id: int):\n    if user_id not in USERS:\n'
      '        raise HTTPException(status_code=404, detail="Пользователь не найден")\n    return {"id": user_id, "name": USERS[user_id]}\n')
t5 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/users/1", "expected_json": {"id": 1, "name": "Аня"}},
    {"id": "v2", "path": "/users/9", "expected_status": 404, "expected_json": {"detail": "Пользователь не найден"}},
    {"id": "h1", "hidden": True, "path": "/users/3", "expected_json": {"id": 3, "name": "Вика"}},
    {"id": "h2", "hidden": True, "path": "/users/0", "expected_status": 404, "expected_json": {"detail": "Пользователь не найден"}},
]}
a5 = asg("a5-404", "write", "Пользователь не найден",
         "В словаре `USERS` три пользователя. Сделайте **GET** `/users/{user_id}`:\n\n"
         "- если пользователь есть — `{\"id\": …, \"name\": …}`;\n"
         "- если нет — код **404** и `{\"detail\": \"Пользователь не найден\"}`.",
         "Возвращать свои ошибки через HTTPException.", "Номер пользователя в пути.", "200 с данными или 404.",
         ["Словарь USERS не меняйте."],
         hints("Сначала проверьте, есть ли user_id в словаре: оператор in.",
               "Ошибку не возвращают, а поднимают: raise.",
               "Исключение — HTTPException(status_code=…, detail=…).",
               "FastAPI сам превратит detail в JSON {\"detail\": …}.",
               "if user_id not in USERS:\n    raise HTTPException(status_code=404, detail=\"Пользователь не найден\")\nreturn {\"id\": user_id, \"name\": USERS[user_id]}"),
         t5, S5, "raise HTTPException прерывает обработчик и отдаёт клиенту код 404 с текстом detail.",
         ["Найденный → 200.", "Не найденный → 404 с нужным detail."],
         [(IMP5 + '\n\n@app.get("/users/{user_id}")\ndef get_user(user_id: int):\n    return {"id": user_id, "name": USERS[user_id]}\n',
           "Нет проверки: для неизвестного номера KeyError и код 500."),
          (IMP5 + '\n\n@app.get("/users/{user_id}")\ndef get_user(user_id: int):\n    if user_id not in USERS:\n'
           '        return {"detail": "Пользователь не найден"}\n    return {"id": user_id, "name": USERS[user_id]}\n',
           "Возвращён словарь с кодом 200, а нужен код 404 — поднимите HTTPException."),
          (IMP5 + '\n\n@app.get("/users/{user_id}")\ndef get_user(user_id: int):\n    if user_id not in USERS:\n'
           '        raise HTTPException(status_code=400, detail="Пользователь не найден")\n    return {"id": user_id, "name": USERS[user_id]}\n',
           "400 — «неверный запрос»; для отсутствующего ресурса — 404.")],
         starter=IMP5 + "\n# ваш обработчик\n")

skills = {"api.http": "HTTP: методы, пути, коды ответа", "api.routes": "Обработчики FastAPI", "api.params": "Параметры пути и запроса",
          "api.models": "Тело запроса: модели pydantic", "api.errors": "Ошибки API: 404 и 422"}
write_pack("api-basics", 10, "Веб-API на FastAPI",
           "Свой сервер на Python: обработчики, параметры, модели данных и коды ответа. Запросы — тестовым клиентом без сети. Пилот этапа 10.",
           "python", ["api-01-fastapi"], skills)
write_lesson("api-01-fastapi", "FastAPI: первый веб-API",
             "Писать обработчики FastAPI с параметрами пути и запроса, принимать JSON через модели и возвращать коды 404 и 422.",
             list(skills), [], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Нет аннотации типа у параметра", "fix": "Без типа параметр — строка. Пишите n: int.", "errorType": "TypeError"},
              {"mistake": "Имя в пути не совпадает с параметром функции", "fix": "\"/square/{n}\" → def square(n: int)."},
              {"mistake": "print вместо return", "fix": "Ответ API — то, что функция возвращает."},
              {"mistake": "Ошибка возвращена словарём", "fix": "Код ошибки задаёт raise HTTPException(status_code=404, …)."},
              {"mistake": "Обращение к словарю без проверки", "fix": "Неизвестный ключ → KeyError и код 500. Проверяйте in."}],
             min_pass=3, pack="api-basics", runner="A")

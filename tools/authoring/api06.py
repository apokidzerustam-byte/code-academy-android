"""Урок FastAPI 6: тестирование API — TestClient, проверка кодов и тела ответа, ошибочные случаи, заголовки, изоляция тестов, подмена зависимостей.
Локально настоящего FastAPI нет: ожидаемый вывод сцен и ответы заданий получены на упрощённой эмуляции (/home/claude/fakefa) и сверены с рассуждением;
настоящий FastAPI проверяет валидатор в CI."""
import contextlib
import io
import sys

sys.path.insert(0, "/home/claude/fakefa")
from lib import *  # noqa: E402,F403


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


def go(code):
    """Вывод кода на эмуляции FastAPI."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "scene", "exec"), {"__name__": "__main__"})
    return buf.getvalue()


# ---------- сцены ----------
HEAD = "from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\n\n\n"
PING = '@app.get("/ping")\ndef ping():\n    return {"status": "ok"}\n\n\n'
C2A = HEAD + PING
C2B = 'client = TestClient(app)\nresponse = client.get("/ping")\nprint(response.status_code)\nprint(response.json())\n'
C2 = C2A + C2B
O2 = "200\n{'status': 'ok'}\n"
assert go(C2) == O2

C3A = HEAD + PING + "client = TestClient(app)\n\n\n"
C3B = ('def test_ping():\n    response = client.get("/ping")\n    assert response.status_code == 200\n    assert response.json() == {"status": "ok"}\n\n\n'
       'def test_unknown_path():\n    assert client.get("/nope").status_code == 404\n\n\n')
C3C = 'test_ping()\ntest_unknown_path()\nprint("тесты пройдены")\n'
C3 = C3A + C3B + C3C
O3 = "тесты пройдены\n"
assert go(C3) == O3

C4A = ("from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\nfrom pydantic import BaseModel\n\napp = FastAPI()\nITEMS = []\n\n\n"
       "class Item(BaseModel):\n    name: str\n    price: float\n\n\n"
       '@app.post("/items", status_code=201)\ndef create(item: Item):\n    ITEMS.append(item.dict())\n    return {"id": len(ITEMS), **item.dict()}\n\n\n')
C4B = ('client = TestClient(app)\nresponse = client.post("/items", json={"name": "Чай", "price": 5})\nprint(response.status_code, response.json())\n')
C4C = ('response = client.post("/items", json={"name": "Кофе"})\nprint(response.status_code)\n')
C4 = C4A + C4B + C4C
O4 = "201 {'id': 1, 'name': 'Чай', 'price': 5.0}\n422\n"
assert go(C4) == O4, go(C4)

C5A = ('from fastapi import FastAPI, Header, HTTPException\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\n\n\n'
       '@app.get("/secret")\ndef secret(x_api_key: str = Header(None)):\n    if x_api_key != "academy-key":\n        raise HTTPException(status_code=401, detail="Нужен ключ")\n    return {"data": 42}\n\n\n')
C5B = ('client = TestClient(app)\nprint(client.get("/secret").status_code)\nprint(client.get("/secret", headers={"X-API-Key": "wrong"}).status_code)\n')
C5C = 'print(client.get("/secret", headers={"X-API-Key": "academy-key"}).json())\n'
C5 = C5A + C5B + C5C
O5 = "401\n401\n{'data': 42}\n"
assert go(C5) == O5

C6A = ('from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\n\n'
       'def make_app():\n    app = FastAPI()\n    counter = {"n": 0}\n\n    @app.post("/count")\n    def count():\n        counter["n"] += 1\n        return {"n": counter["n"]}\n\n    return app\n\n\n'
       'def hit(client):\n    return client.post("/count").json()["n"]\n\n\n')
C6B = 'shared = TestClient(make_app())\nprint("общий клиент:", hit(shared), hit(shared))\n'
C6C = 'print("свежий клиент:", hit(TestClient(make_app())), hit(TestClient(make_app())))\n'
C6 = C6A + C6B + C6C
O6 = "общий клиент: 1 2\nсвежий клиент: 1 1\n"
assert go(C6) == O6

C7A = ('from fastapi import Depends, FastAPI\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\n\n\n'
       'def get_rate():\n    return 4.3          # в жизни здесь запрос к банку\n\n\n'
       '@app.get("/convert/{eur}")\ndef convert(eur: float, rate: float = Depends(get_rate)):\n    return {"pln": round(eur * rate, 2)}\n\n\n')
C7B = 'client = TestClient(app)\nprint(client.get("/convert/10").json())\n'
C7C = 'app.dependency_overrides[get_rate] = lambda: 5.0\nprint(client.get("/convert/10").json())\n'
C7D = 'app.dependency_overrides.clear()\nprint(client.get("/convert/10").json())\n'
C7 = C7A + C7B + C7C + C7D
O7 = "{'pln': 43.0}\n{'pln': 50.0}\n{'pln': 43.0}\n"
assert go(C7) == O7

scenes = [
    scene("intro", "Зачем тестировать API", """
      Когда вы пишете API, у вас есть обещание другим программам: на такой запрос вы ответите так. Это называется контрактом. Приложение на телефоне или
      сайт рассчитывают на этот контракт, и если вы случайно поменяете код ответа или название поля, у них всё сломается, а вы не заметите. Проверять
      контракт вручную, отправляя запросы по одному, долго и ненадёжно. Лучше записать проверки в виде тестов и запускать их после каждой
      правки. Для этого не нужен ни настоящий сервер, ни сеть. В FastAPI есть тестовый клиент, который вызывает приложение прямо внутри программы.
      Он быстрый, не занимает порт и работает без интернета. Сегодня мы научимся проверять коды ответов и тело, ошибочные запросы, заголовки,
      а ещё писать тесты, которые не мешают друг другу.""",
          [NOTE("**Контракт API** — на какой запрос какой код и какое тело вернёт сервер", at="у вас есть обещание"),
           NOTE("`TestClient` вызывает приложение **внутри программы**: без сервера, порта и сети", at="Для этого не нужен ни")]),
    scene("client", "TestClient: первый запрос", """
      Сначала создаём приложение с одним маршрутом ping. Он отвечает словарём со статусом ok. Затем клиент: класс TestClient принимает наше
      приложение. Метод get отправляет запрос по адресу. В ответе нас интересуют два свойства. Свойство status code хранит код ответа, а метод json
      возвращает тело ответа как обычный словарь. Запустим. Код двести, значит, всё в порядке, а тело в точности такое, как мы вернули из функции.
      Обратите внимание, что мы ничего не запускали и не открывали порт: клиент обратился к приложению напрямую.""",
          [CLEAR(), T(C2A, at="Сначала создаём"), T("client = TestClient(app)\n", at="Затем клиент"), HL(L(C2, "client = TestClient"), at="Затем клиент"),
           T(C2B.split("\n", 1)[1], at="Метод get"), HL(L(C2, "response ="), at="Метод get"),
           HL(L(C2, "print(response.status_code)"), at="Свойство status code"), HL(L(C2, "print(response.json())"), at="а метод json"),
           RUN(at="Запустим"), OUT(O2, at="Запустим")]),
    scene("asserts", "Проверки через assert", """
      Смотреть на вывод глазами неудобно. Лучше записать ожидания как проверки. Тест, это функция, где мы делаем запрос и сверяем результат командой
      assert. Первый тест проверяет, что адрес ping отвечает кодом двести и нужным словарём. Второй проверяет, что несуществующий адрес даёт
      четыреста четыре. Ошибочные случаи тоже нужно тестировать, потому что это часть контракта: клиент должен получить понятный отказ, а
      не странный ответ. Дальше вызываем оба теста. Если хоть один assert не сойдётся, программа остановится с ошибкой и покажет, какой.
      Если всё хорошо, увидим сообщение. В настоящих проектах такие функции запускает pytest, но принцип тот же.""",
          [CLEAR(), T(C3A, at="Смотреть на вывод"), T(C3B.split("def test_unknown_path")[0], at="Тест, это функция"), HL(L(C3, "def test_ping", 4), at="Первый тест"),
           T("def test_unknown_path" + C3B.split("def test_unknown_path")[1], at="Второй проверяет"), HL(L(C3, "def test_unknown_path", 2), at="Второй проверяет"),
           T(C3C, at="Дальше вызываем"), RUN(at="Если всё хорошо"), OUT(O3, at="Если всё хорошо")]),
    scene("post", "POST и ошибочные данные", """
      Теперь запрос с данными. Метод post принимает параметр json: словарь превращается в тело запроса. Маршрут создаёт товар и отвечает кодом
      двести один, то есть «создано». Модель Item описывает обязательные поля: название и цену. Отправим правильный товар и посмотрим на ответ. Код двести один,
      и в теле номер и поля товара. А теперь отправим товар без цены. Сервер не должен падать или молча принимать мусор: он отвечает
      кодом четыреста двадцать два. Это одна из главных проверок API: плохие данные получают понятный отказ. Заметьте и ещё одно: цена
      пять превратилась в пять целых ноль десятых, потому что поле объявлено числом с плавающей точкой.""",
          [CLEAR(), T(C4A, at="Теперь запрос"), HL(L(C4, "class Item", 3), at="Модель Item"), HL(L(C4, "@app.post"), at="Метод post принимает"),
           T(C4B, at="Отправим правильный"), HL(L(C4, 'client.post("/items", json={"name": "Чай"'), at="Отправим правильный"),
           T(C4C, at="А теперь отправим"), RUN(at="он отвечает кодом"), OUT(O4, at="он отвечает кодом")]),
    scene("headers", "Заголовки и авторизация", """
      Теперь защищённый маршрут. Он читает заголовок X API Key и пускает только с верным значением. В тесте заголовки передают параметром headers.
      Нужны три проверки: без заголовка, с неверным ключом и с верным. Если проверять только успешный случай, можно не заметить, что маршрут
      пускает вообще всех. Первые две проверки дают четыреста один, а третья возвращает данные. Помните: тест на отказ так же важен, как
      тест на успех. Ключ в примере записан в коде ради урока, а в настоящем проекте его берут из настроек окружения.""",
          [CLEAR(), T(C5A, at="Теперь защищённый"), HL(L(C5, "def secret"), at="Он читает заголовок"), T(C5B, at="Нужны три проверки"),
           HL(L(C5, 'print(client.get("/secret").status_code)'), at="без заголовка"), HL(L(C5, '"wrong"'), at="с неверным ключом"),
           T(C5C, at="а третья возвращает"), HL(L(C5, 'academy-key"}).json'), at="а третья возвращает"), RUN(at="Первые две проверки"), OUT(O5, at="Первые две проверки")]),
    scene("isolation", "Тесты не должны мешать друг другу", """
      Ещё одна ловушка: тесты, которые влияют друг на друга. Приложение хранит счётчик в памяти. Если все тесты пользуются одним клиентом, то результат
      второго зависит от первого: он увидит двойку вместо единицы. Стоит поменять порядок запуска, и всё ломается. Чтобы этого не было,
      приложение создают функцией make app, и каждый тест получает своё свежее приложение. Сравним. Общий клиент отвечает один и два, то
      есть второй вызов зависит от первого. Свежие клиенты оба раза отвечают единицей. Тест, который проходит только в определённом порядке,
      это плохой тест: когда он упадёт, вы не поймёте, виноват код или порядок.""",
          [CLEAR(), T(C6A, at="Приложение хранит"), HL(L(C6, "def make_app"), at="приложение создают функцией"), T(C6B, at="Сравним"),
           HL(L(C6, "shared ="), at="Общий клиент"), T(C6C, at="Свежие клиенты"), HL(L(C6, "свежий клиент"), at="Свежие клиенты"), RUN(at="Тест, который проходит"), OUT(O6, at="Тест, который проходит")]),
    scene("override", "Подмена зависимостей", """
      Если маршрут зависит от внешней службы, например от курса валют, настоящий запрос в тесте не нужен: он медленный и каждый раз отвечает
      по-разному. В FastAPI внешние зависимости подключают через Depends, и в тестах их можно заменить. Для этого есть словарь dependency
      overrides. Функция get rate в жизни спрашивает банк, а у нас пока возвращает число. Маршрут convert умножает сумму на курс. Сначала запрос
      даёт сорок три злотых. Затем мы заменяем get rate функцией, которая всегда возвращает пять, и получаем пятьдесят. В конце подмену очищаем, чтобы
      она не повлияла на другие тесты, и ответ снова сорок три. Это тот же приём, что мок из прошлого урока, только встроенный в FastAPI.""",
          [CLEAR(), T(C7A, at="Если маршрут зависит"), HL(L(C7, "def get_rate"), at="Функция get rate"), HL(L(C7, "def convert"), at="Маршрут convert"),
           T(C7B, at="Сначала запрос"), T(C7C, at="Затем мы заменяем"), HL(L(C7, "dependency_overrides[get_rate]"), at="Затем мы заменяем"),
           T(C7D, at="В конце подмену"), RUN(at="Это тот же приём"), OUT(O7, at="Это тот же приём")]),
    scene("checklist", "Что проверять в каждом маршруте", """
      Что же проверять в каждом маршруте? Первое: счастливый путь, когда правильный запрос даёт правильный ответ. Второе: плохие данные, то есть
      пропущенное поле, неверный тип, значение вне границ. Третье: отсутствие или подделка авторизации. Четвёртое: несуществующие объекты,
      то есть код четыреста четыре. Пятое: граничные значения, например нулевая цена или пустая строка. И проверяйте не только код, но и
      тело ответа: правильный код с неверным телом это тоже ошибка. Если вы покрыли эти пять случаев, то контракт вашего API защищён от
      большинства поломок.""",
          [NOTE("1. Счастливый путь · 2. Плохие данные (422) · 3. Нет или подделка авторизации (401/403) · 4. Нет объекта (404) · 5. Границы", at="Что же проверять"),
           NOTE("Проверяйте **и код, и тело** ответа", at="И проверяйте")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: проверять только успешный запрос. Баги прячутся в ошибочных ветках. Вторая: проверять только код и не смотреть
      на тело, тогда сервер может вернуть двести с пустым ответом. Третья: тесты, зависящие друг от друга через общее состояние: они проходят
      сегодня и падают завтра. Четвёртая: настоящая сеть в тесте, из-за которой тест то зелёный, то красный. Подменяйте внешние службы.""",
          [NOTE("Ошибка 1: проверен только успешный запрос.", at="Первая"), NOTE("Ошибка 2: проверен код, но не тело.", at="Вторая"),
           NOTE("Ошибка 3: общее состояние между тестами.", at="Третья"), NOTE("Ошибка 4: настоящая сеть в тесте.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. Тестовый клиент вызывает приложение внутри программы, без сервера и сети. Тест отправляет запрос и сверяет код ответа и тело
      командой assert. Нужно проверять не только успех, но и плохие данные, отсутствие авторизации и несуществующие объекты. Тесты должны быть независимы: для
      этого приложение создают заново. Внешние зависимости подменяют через dependency overrides. В заданиях вы напишете API по описанию тестов, найдёте ошибку,
      которую пропускает тест, предскажете работу счётчика, подмените зависимость и напишете проверку, ловящую три ошибки сразу.""",
          [NOTE("`TestClient` · `assert` на код и тело · ошибки, авторизация, 404 · свежее приложение на тест · `dependency_overrides`", at="Подведём итог")]),
]

notes = """
# Тестирование API на FastAPI

Тестовый клиент вызывает приложение **внутри программы**: не нужны сервер, порт и сеть.

```py
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


@app.get("/ping")
def ping():
    return {"status": "ok"}


client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

## Что передавать в запросе

| Что | Как |
|---|---|
| тело JSON | `client.post("/items", json={...})` |
| параметры строки запроса | `client.get("/items", params={"limit": 5})` |
| заголовки | `client.get("/secret", headers={"X-API-Key": "..."})` |

## Что проверять в каждом маршруте

1. Счастливый путь: верный запрос — верный ответ.
2. Плохие данные: нет поля, неверный тип, значение вне границ — **422**.
3. Нет или подделка авторизации — **401** / **403**.
4. Несуществующий объект — **404**.
5. Граничные значения: ноль, пустая строка, максимум.

Проверяйте и код ответа, и тело.

## Независимость тестов

Не пользуйтесь общим состоянием: создавайте приложение функцией (`make_app()`) для каждого теста.

## Подмена зависимостей

```py
app.dependency_overrides[get_rate] = lambda: 5.0   # на время теста
app.dependency_overrides.clear()                    # очистить после теста
```

В настоящем проекте тесты запускает `pytest`; принцип проверок тот же.
"""

# ---------- a1: товары по описанию тестов ----------
SOL1 = ('from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel, Field\n\napp = FastAPI()\nPRODUCTS = {}\n\n\n'
        'class Product(BaseModel):\n    name: str\n    price: float = Field(..., gt=0)\n\n\n'
        '@app.post("/products", status_code=201)\ndef create_product(product: Product):\n    new_id = len(PRODUCTS) + 1\n    PRODUCTS[new_id] = product.dict()\n    return {"id": new_id, **product.dict()}\n\n\n'
        '@app.get("/products/{product_id}")\ndef read_product(product_id: int):\n    if product_id not in PRODUCTS:\n        raise HTTPException(status_code=404, detail="Товар не найден")\n    return {"id": product_id, **PRODUCTS[product_id]}\n')
START1 = ('from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel, Field\n\napp = FastAPI()\nPRODUCTS = {}\n\n\n'
          '# Здесь опишите модель Product и два маршрута: POST /products и GET /products/{product_id}\n')
t1 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "POST", "path": "/products", "json": {"name": "Чай", "price": 5}, "expected_status": 201, "expected_json": {"id": 1, "name": "Чай", "price": 5.0},
     "hint": "Создание отвечает кодом 201 и возвращает товар с номером"},
    {"id": "v2", "path": "/products/1", "expected_json": {"id": 1, "name": "Чай", "price": 5.0}},
    {"id": "h1", "hidden": True, "path": "/products/99", "expected_status": 404, "expected_json": {"detail": "Товар не найден"}, "hint": "Несуществующий товар — ошибка 404 с текстом «Товар не найден»"},
    {"id": "h2", "hidden": True, "method": "POST", "path": "/products", "json": {"name": "Яд", "price": -1}, "expected_status": 422, "hint": "Цена должна быть больше нуля"},
    {"id": "h3", "hidden": True, "method": "POST", "path": "/products", "json": {"name": "Кофе"}, "expected_status": 422, "hint": "Цена обязательна"},
    {"id": "h4", "hidden": True, "method": "POST", "path": "/products", "json": {"name": "Кофе", "price": 8}, "expected_status": 201, "expected_json": {"id": 2, "name": "Кофе", "price": 8.0},
     "hint": "Номер растёт: второй товар получает id 2"},
    {"id": "h5", "hidden": True, "path": "/products/2", "expected_json": {"id": 2, "name": "Кофе", "price": 8.0}},
]}
a1 = asg("a1-products", "write", "API по описанию тестов",
         "Тест-план: `POST /products` с телом `{\"name\": \"Чай\", \"price\": 5}` отвечает **201** и возвращает `{\"id\": 1, \"name\": \"Чай\", \"price\": 5.0}`; `GET /products/1` возвращает тот же товар; "
         "`GET /products/99` — **404** и `{\"detail\": \"Товар не найден\"}`; товар без цены или с ценой не больше нуля — **422**. Номера выдаются по порядку, начиная с 1. Напишите приложение `app`, которое проходит этот тест-план.",
         "Написать API по описанию тестов.", "Запросы из тест-плана.", "Коды и тело ответов, как в тест-плане.",
         ["Хранилище — словарь PRODUCTS: он уже создан."],
         hints("Сначала опишите модель товара: название — строка, цена — число больше нуля.", "Ограничение для числа задают так: price: float = Field(..., gt=0).",
               "Создание — POST с параметром status_code=201 в декораторе; номер на единицу больше количества товаров.", "Несуществующий номер — raise HTTPException(status_code=404, detail=…).",
               "Верните словарь с id и полями товара: {\"id\": new_id, **product.dict()}."),
         t1, SOL1, "Тест-план задаёт контракт: коды 201, 404 и 422 и форму тела. Сначала записывают ожидания, потом пишут код, который их выполняет.",
         ["POST отвечает 201.", "GET возвращает товар или 404.", "Плохая цена даёт 422.", "Номера растут."],
         [(SOL1.replace('status_code=201', 'status_code=200'), "Создание должно отвечать кодом 201, а не 200."),
          (SOL1.replace('        raise HTTPException(status_code=404, detail="Товар не найден")', '        return {"detail": "Товар не найден"}'), "Для несуществующего товара нужна ошибка 404, а не код 200 с текстом."),
          (SOL1.replace('Field(..., gt=0)', 'Field(...)'), "Цена не ограничена: товар с отрицательной ценой принимается, а должен давать 422."),
          (SOL1.replace('len(PRODUCTS) + 1', '1'), "Номер всегда 1: второй товар затирает первый.")],
         starter=START1)

# ---------- a2: логин, который пускает всех ----------
BAD2 = ('from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel\n\napp = FastAPI()\nUSERS = {"anna": "secret1", "boris": "qwerty"}\n\n\n'
        'class Login(BaseModel):\n    user: str\n    password: str\n\n\n@app.post("/login")\ndef login(data: Login):\n    return {"token": "t-" + data.user}\n')
SOL2 = BAD2.replace('    return {"token": "t-" + data.user}\n', '    if USERS.get(data.user) != data.password:\n        raise HTTPException(status_code=401, detail="Неверный логин или пароль")\n    return {"token": "t-" + data.user}\n')
t2 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "POST", "path": "/login", "json": {"user": "anna", "password": "secret1"}, "expected_json": {"token": "t-anna"}},
    {"id": "v2", "method": "POST", "path": "/login", "json": {"user": "anna", "password": "wrong"}, "expected_status": 401, "expected_json": {"detail": "Неверный логин или пароль"},
     "hint": "Тест на неверный пароль падает: сервер пускает любого"},
    {"id": "h1", "hidden": True, "method": "POST", "path": "/login", "json": {"user": "nobody", "password": "x"}, "expected_status": 401, "expected_json": {"detail": "Неверный логин или пароль"},
     "hint": "Неизвестный пользователь тоже должен получать 401"},
    {"id": "h2", "hidden": True, "method": "POST", "path": "/login", "json": {"user": "boris", "password": "qwerty"}, "expected_json": {"token": "t-boris"}},
    {"id": "h3", "hidden": True, "method": "POST", "path": "/login", "json": {"user": "anna", "password": ""}, "expected_status": 401, "hint": "Пустой пароль не подходит"},
    {"id": "h4", "hidden": True, "method": "POST", "path": "/login", "json": {"user": "boris", "password": "secret1"}, "expected_status": 401, "hint": "Пароль другого пользователя не подходит"},
]}
a2 = asg("a2-login", "fix", "Тест на неверный пароль",
         "Тесты счастливого пути проходят, но тест «неверный пароль» падает: `POST /login` выдаёт токен **любому**, кто назвал существующее имя. Исправьте маршрут: если пара «имя — пароль» не совпадает с `USERS` (или имени нет), "
         "ответьте **401** и `{\"detail\": \"Неверный логин или пароль\"}`.",
         "Исправить маршрут по падающему тесту на отказ.", "POST-запросы с разными логинами и паролями.", "401 при неверной паре, токен при верной.",
         ["Не меняйте словарь USERS и модель Login."],
         hints("Сначала запустите тесты: какой из них падает?", "Тест счастливого пути проходит, потому что токен выдаётся всегда.", "Нужно сравнить пароль из запроса с паролем из USERS.",
               "Для неизвестного имени USERS.get вернёт None, а None не равно строке.", "Если не совпало — raise HTTPException(status_code=401, detail=…), иначе верните токен."),
         t2, SOL2, "Тесты только счастливого пути не заметили бы ошибку: она видна лишь на тесте с неверным паролем. Поэтому ошибочные случаи тоже нужно проверять.",
         ["Верная пара даёт токен.", "Неверный пароль даёт 401.", "Неизвестный пользователь даёт 401."],
         [(BAD2.replace('    return {"token": "t-" + data.user}\n', '    if data.user not in USERS:\n        raise HTTPException(status_code=401, detail="Неверный логин или пароль")\n    return {"token": "t-" + data.user}\n'),
           "Проверяется только имя: любой пароль всё ещё подходит."),
          (SOL2.replace("status_code=401", "status_code=403"), "Неверный пароль — это 401 («не удалось подтвердить личность»), а не 403."),
          (SOL2.replace('USERS.get(data.user) != data.password', 'data.password not in USERS.values()'), "Пароль ищется среди всех паролей: пароль другого пользователя тоже подходит.")],
         starter=BAD2)

# ---------- a3: счётчик (предсказание) ----------
CODE3 = ('from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\n\n'
         'def make_app():\n    app = FastAPI()\n    visits = {"n": 0}\n\n    @app.get("/visit")\n    def visit():\n        visits["n"] += 1\n        return {"n": visits["n"]}\n\n    return app\n\n\n'
         'a = TestClient(make_app())\nb = TestClient(make_app())\n\nprint(a.get("/visit").json()["n"])\nprint(a.get("/visit").json()["n"])\nprint(b.get("/visit").json()["n"])\nprint(a.get("/visit").json()["n"])\n')
E3 = go(CODE3).rstrip("\n")
assert E3 == "1\n2\n1\n3", E3
a3 = asg("a3-visits", "predict", "Счётчик и свежие приложения",
         "Что выведет программа? Запишите вывод построчно, не запуская код.", "Предсказать работу независимых приложений.", "Нет.", "Вывод программы.", ["Ответьте без запуска."],
         hints("Функция make_app создаёт новое приложение со своим счётчиком при каждом вызове.", "Клиенты a и b работают с разными приложениями.", "Счётчик клиента a растёт: первые два запроса дают 1 и 2.",
               "Клиент b считает с нуля: его первый запрос даёт 1.", "Четвёртый запрос снова идёт к приложению a, где уже было два запроса, и даёт 3."),
         {"kind": "answer", "expected_answer": E3}, E3, "Каждый вызов make_app() создаёт отдельное приложение с отдельным счётчиком. Приложение a посчитало 1, 2, затем 3, а b считало отдельно и ответило 1.",
         ["Все строки вывода верны."],
         [("1\n2\n3\n4", "Приложения независимы: у клиента b свой счётчик, он начинает с единицы."), ("1\n1\n1\n1", "Счётчик внутри одного приложения растёт между запросами.")],
         code=CODE3)

# ---------- a4: подмена зависимости ----------
START4 = ('from fastapi import Depends, FastAPI\n\napp = FastAPI()\n\n\ndef get_rate():\n    return 4.3  # в жизни — запрос к банку\n\n\n'
          '@app.get("/convert/{eur}")\ndef convert(eur: float, rate: float = Depends(get_rate)):\n    return {"pln": round(eur * rate, 2)}\n\n\n'
          '# Подмените get_rate так, чтобы курс всегда равнялся 5.0\n')
SOL4 = START4.replace("# Подмените get_rate так, чтобы курс всегда равнялся 5.0\n", "app.dependency_overrides[get_rate] = lambda: 5.0\n")
t4 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/convert/10", "expected_json": {"pln": 50.0}, "hint": "Курс в этом тесте должен быть 5.0"},
    {"id": "v2", "path": "/convert/0", "expected_json": {"pln": 0.0}},
    {"id": "h1", "hidden": True, "path": "/convert/2.5", "expected_json": {"pln": 12.5}},
    {"id": "h2", "hidden": True, "path": "/convert/100", "expected_json": {"pln": 500.0}},
    {"id": "h3", "hidden": True, "path": "/convert/abc", "expected_status": 422, "hint": "Не число — 422"},
]}
a4 = asg("a4-override", "complete", "Подмена курса",
         "Маршрут `/convert/{eur}` умножает сумму на курс из зависимости `get_rate` (в жизни — запрос к банку). В тесте курс должен быть **фиксированным**: 5.0. "
         "Допишите одну строку, которая подменяет зависимость `get_rate` через `dependency_overrides`.",
         "Подменить внешнюю зависимость на время теста.", "Запросы к /convert с разными суммами.", "Результат умножения на курс 5.0.",
         ["Сам маршрут и функцию get_rate менять не нужно."],
         hints("Подмены зависимостей хранит словарь app.dependency_overrides.", "Ключ в нём — сама функция-зависимость, а не её имя в кавычках.", "Значение — функция без параметров, которая вернёт нужное число.",
               "Короткую функцию удобно записать через lambda.", "app.dependency_overrides[get_rate] = lambda: 5.0"),
         t4, SOL4, "dependency_overrides заменяет зависимость целиком: ключ — оригинальная функция, значение — подставная. Так внешние службы убирают из тестов.",
         ["Подмена задана через dependency_overrides.", "Ключ — функция get_rate.", "Курс равен 5.0."],
         [(START4.replace("# Подмените get_rate так, чтобы курс всегда равнялся 5.0\n", 'app.dependency_overrides["get_rate"] = lambda: 5.0\n'), "Ключ — сама функция, а не строка с её именем: подмена не срабатывает."),
          (SOL4.replace("lambda: 5.0", "lambda: 4.0"), "Подставной курс должен быть 5.0.")],
         starter=START4)

# ---------- a5: тест, который ловит три ошибки ----------
# Валидатор здесь не имеет настоящего FastAPI: сверяем функцию в этом же процессе на эмуляции (в CI то же сделает настоящий).
import copy  # noqa: E402
import lib as _lib  # noqa: E402


def _passes_fake(code, tests):
    ns = {}
    try:
        exec(compile(code, "task", "exec"), ns)
        fn = ns[tests["function"]]
        return all(fn(*copy.deepcopy(c["args"])) == c["expected"] for c in tests["cases"])
    except Exception:  # noqa: BLE001
        return False


_orig_passes = _lib._passes
_lib._passes = _passes_fake

PRE5 = ('from fastapi import FastAPI, HTTPException\nfrom fastapi.testclient import TestClient\nfrom pydantic import BaseModel, Field\n\n\n'
        'class Product(BaseModel):\n    name: str\n    price: float = Field(..., gt=0)\n\n\nclass LooseProduct(BaseModel):\n    name: str\n    price: float\n\n\n'
        'def make_shop_app(variant):\n    """Магазин; в вариантах no404, no422, wrong_code спрятана одна ошибка, в варианте ok её нет."""\n    app = FastAPI()\n    items = {}\n'
        '    model = LooseProduct if variant == "no422" else Product\n    created = 200 if variant == "wrong_code" else 201\n\n'
        '    @app.post("/products", status_code=created)\n    def create(product: model):\n        items[len(items) + 1] = product.dict()\n        return {"id": len(items), **product.dict()}\n\n'
        '    @app.get("/products/{product_id}")\n    def read(product_id: int):\n        if product_id not in items:\n            if variant == "no404":\n                return {"detail": "нет такого"}\n'
        '            raise HTTPException(status_code=404, detail="Товар не найден")\n        return {"id": product_id, **items[product_id]}\n\n    return app\n\n\n')
BODY5 = ('def check(variant):\n    client = TestClient(make_shop_app(variant))\n    try:\n'
         '        assert client.post("/products", json={"name": "Чай", "price": 5}).status_code == 201\n'
         '        assert client.get("/products/1").status_code == 200\n'
         '        assert client.get("/products/99").status_code == 404\n'
         '        assert client.post("/products", json={"name": "Яд", "price": -1}).status_code == 422\n'
         '    except AssertionError:\n        return False\n    return True\n')
SOL5 = PRE5 + BODY5
START5 = PRE5 + 'def check(variant):\n    # Создайте клиент для make_shop_app(variant), выполните проверки и верните True, если все прошли, иначе False\n    return True\n'
a5 = fn_task("a5-check", "Тест, который ловит три ошибки",
             "Функция `make_shop_app(variant)` строит магазин: вариант `\"ok\"` работает верно, а в вариантах `\"no404\"`, `\"no422\"`, `\"wrong_code\"` спрятана по одной ошибке. "
             "Допишите `check(variant)`: создайте `TestClient` для `make_shop_app(variant)`, проверьте создание товара (код **201**), чтение (**200**), отсутствующий товар (**404**) и товар с ценой `-1` (**422**). "
             "Верните `True`, если все проверки прошли, и `False`, если хоть одна не сошлась. Хороший тест вернёт `True` только для `\"ok\"`.",
             "check", SOL5, [["ok"], ["no404"], ["no422"], ["wrong_code"]],
             [(PRE5 + 'def check(variant):\n    client = TestClient(make_shop_app(variant))\n    try:\n        assert client.post("/products", json={"name": "Чай", "price": 5}).status_code in (200, 201)\n'
               '        assert client.get("/products/1").status_code == 200\n        assert client.get("/products/99").status_code == 404\n        assert client.post("/products", json={"name": "Яд", "price": -1}).status_code == 422\n'
               '    except AssertionError:\n        return False\n    return True\n', "Код создания принимается любой: ошибка wrong_code не поймана."),
              (SOL5.replace('        assert client.post("/products", json={"name": "Яд", "price": -1}).status_code == 422\n', ''), "Нет проверки плохой цены: вариант no422 проходит."),
              (SOL5.replace('        assert client.get("/products/99").status_code == 404\n', ''), "Нет проверки отсутствующего товара: вариант no404 проходит."),
              (SOL5.replace('def check(variant):\n    client', 'def check(variant):\n    return True\n    client'), "Функция всегда возвращает True: ошибки не ловятся.")],
             hints("Клиент создаётся так: TestClient(make_shop_app(variant)).", "Каждая проверка — assert на код ответа; все assert оборачивают в try … except AssertionError.", "Нужны четыре запроса: создание, чтение, несуществующий номер, плохая цена.",
                   "Ожидаемые коды: создание 201, чтение 200, несуществующий товар 404, цена -1 — 422.", "except AssertionError: return False; в конце функции — return True."),
             "Каждая ошибка ломает свою проверку: no404 — чтение отсутствующего товара, no422 — плохую цену, wrong_code — код создания. Поэтому нужны все четыре проверки; пропущенная пропускает и свою ошибку.",
             type="write", starter=START5, goal="Написать тест, различающий верный и три ошибочных варианта.",
             criteria=["Для «ok» возвращается True.", "Для каждого из трёх ошибочных вариантов — False."])

_lib._passes = _orig_passes

skills = {"api.test-client": "TestClient: запросы и проверки", "api.test-errors": "Тесты ошибочных случаев и авторизации", "api.test-isolation": "Независимые тесты и подмена зависимостей"}
write_lesson("api-06-testing", "FastAPI: тестирование API",
             "Проверять API тестовым клиентом: коды и тело ответов, ошибочные запросы, заголовки, независимость тестов и подмена зависимостей.",
             list(skills), ["api-05-auth"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Проверен только успешный запрос", "fix": "Тестируйте плохие данные, отсутствие авторизации и несуществующие объекты."},
              {"mistake": "Проверен код, но не тело ответа", "fix": "Сверяйте и код, и тело: код 200 с неверным телом тоже ошибка."},
              {"mistake": "Тесты зависят друг от друга через общее состояние", "fix": "Создавайте приложение заново для каждого теста (make_app())."},
              {"mistake": "В тесте настоящая сеть или внешняя служба", "fix": "Подменяйте зависимости через dependency_overrides или моки."}],
             min_pass=4, pack="api-basics", runner="A")
f = ROOT / "content/packs/api-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "api-06-testing" not in data["lessons"]:
    data["lessons"].append("api-06-testing")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

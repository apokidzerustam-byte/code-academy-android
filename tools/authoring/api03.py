"""Урок FastAPI 3: проверка данных (Field, 422), свои ошибки (409), постраничный вывод (limit/offset).
Поведение сверяет валидатор в CI настоящим FastAPI; локально — только эмуляция."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


IMP = ("from fastapi import FastAPI, HTTPException\nfrom fastapi.testclient import TestClient\nfrom pydantic import BaseModel, Field\n\n"
       "app = FastAPI()\nITEMS = []\n\n\n")
MODEL = ("class ItemIn(BaseModel):\n    name: str = Field(..., min_length=2)\n    price: float = Field(..., gt=0)\n    qty: int = Field(1, ge=1)\n")
HEAD = IMP + MODEL
POST_A = ('\n\n@app.post("/items", status_code=201)\ndef add_item(item: ItemIn):\n'
          '    ITEMS.append({"name": item.name, "price": item.price, "qty": item.qty})\n    return ITEMS[-1]\n')
POST_B = ('\n\n@app.post("/items", status_code=201)\ndef add_item(item: ItemIn):\n    for it in ITEMS:\n        if it["name"] == item.name:\n'
          '            raise HTTPException(status_code=409, detail="Такой товар уже есть")\n'
          '    ITEMS.append({"name": item.name, "price": item.price, "qty": item.qty})\n    return ITEMS[-1]\n')
GET_ALL = '\n\n@app.get("/items")\ndef list_items():\n    return ITEMS\n'
GET_PAGE = '\n\n@app.get("/items")\ndef list_items(limit: int = 10, offset: int = 0):\n    return ITEMS[offset:offset + limit]\n'

C2 = HEAD + POST_A
R2 = ('\n\nclient = TestClient(app)\nr = client.post("/items", json={"name": "Чай", "price": 3.5})\nprint(r.status_code, r.json())\n'
      'print(client.post("/items", json={"name": "Я", "price": 3.5}).status_code)\n'
      'print(client.post("/items", json={"name": "Сыр", "price": 0}).status_code)\n'
      'print(client.post("/items", json={"name": "Сыр", "price": 5, "qty": 0}).status_code)\n')
O2 = "201 {'name': 'Чай', 'price': 3.5, 'qty': 1}\n422\n422\n422\n"
C3 = HEAD + POST_B
R3 = ('\n\nclient = TestClient(app)\nclient.post("/items", json={"name": "Чай", "price": 3.5})\n'
      'r = client.post("/items", json={"name": "Чай", "price": 4})\nprint(r.status_code, r.json())\n')
O3 = "409 {'detail': 'Такой товар уже есть'}\n"
C4 = HEAD + POST_B + GET_PAGE
R4 = ('\n\nclient = TestClient(app)\nfor n in range(1, 6):\n    client.post("/items", json={"name": f"Т{n}", "price": 1.5})\n'
      'for offset in (0, 2, 4, 10):\n    r = client.get("/items", params={"limit": 2, "offset": offset})\n    print([i["name"] for i in r.json()])\n'
      'print(client.get("/items", params={"limit": "много"}).status_code)\n')
O4 = "['Т1', 'Т2']\n['Т3', 'Т4']\n['Т5']\n[]\n422\n"

scenes = [
    scene("intro", "Клиенту нельзя доверять", """
      Клиенту нельзя доверять. Он может прислать пустое название, отрицательную цену или ноль штук. Если принять это молча, в списке
      окажется мусор. Хороший сервер проверяет данные на входе и честно отвечает: ошибка на стороне клиента. Для таких ошибок есть
      коды четырёхсотой серии. Четыреста двадцать два значит «данные неверные», а четыреста девять — «конфликт с тем, что уже есть».""",
          [NOTE("422 — данные не прошли проверку · 409 — конфликт с уже существующим · 404 — не найдено", at="Для таких ошибок")]),
    scene("validate", "Ограничения в модели", """
      Ограничения задают прямо в модели с помощью Field. Многоточие значит, что поле обязательное. Параметр min_length задаёт
      минимальную длину названия. Параметр gt — строго больше нуля для цены. Параметр ge — не меньше единицы для количества, а по
      умолчанию одна штука. Отправим нормальный товар и три плохих: короткое название, нулевую цену и нулевое количество.
      FastAPI вернёт четыреста двадцать два сам, наш обработчик даже не запустится.""",
          [CLEAR(), T(C2 + R2, at="Ограничения задают"), HL(L(C2, "name: str"), at="min_length"), HL(L(C2, "price: float"), at="gt —"),
           HL(L(C2, "qty: int"), at="ge —"), RUN(at="Отправим"), OUT(O2, at="Отправим")]),
    scene("conflict", "Свои ошибки: 409", """
      А некоторые ошибки знает только наш код. Например, товар с таким названием уже есть. Для этого подходит код четыреста девять,
      конфликт. Перед добавлением проходим по списку, и если название совпало, поднимаем исключение. Отправим «Чай» дважды: второй
      раз получим конфликт и понятное сообщение.""",
          [CLEAR(), T(C3 + R3, at="А некоторые"), HL(L(C3, "for it in ITEMS", 3), at="Перед добавлением"), RUN(at="Отправим"), OUT(O3, at="Отправим")]),
    scene("paging", "Постраничный вывод", """
      Когда записей много, отдавать их все сразу нельзя. Клиент присылает параметры запроса: limit — сколько взять, offset — сколько
      пропустить. Если их нет, берутся значения по умолчанию. Достаём срез от offset до offset плюс limit. Добавим пять товаров и
      запросим по два с разных позиций. За пределами списка срез просто пуст, а вместо числа в limit получим четыреста двадцать два.""",
          [CLEAR(), T(C4 + R4, at="Когда записей"), HL(L(C4, "def list_items"), at="limit — сколько"), HL(L(C4, "return ITEMS["), at="Достаём срез"),
           RUN(at="Добавим"), OUT(O4, at="Добавим")]),
    scene("summary", "Итог", """
      Итак. Ограничения в модели через Field дают код четыреста двадцать два без единой строчки проверки. Свои ошибки поднимаем через
      HTTPException: четыреста девять для конфликта. Параметры limit и offset превращают длинный список в страницы. И запомните: значение
      по умолчанию в модели не проверяется, поэтому оно само должно подходить под ограничение.""",
          [NOTE("Field(…, gt=0) → 422 · HTTPException(409) → конфликт · limit/offset → страницы · значение по умолчанию не проверяется", at="Итак")]),
]

notes = """
# FastAPI: проверка данных и страницы

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()
ITEMS = []

class ItemIn(BaseModel):
    name: str = Field(..., min_length=2)   # обязательное, не короче 2 символов
    price: float = Field(..., gt=0)        # обязательное, строго больше 0
    qty: int = Field(1, ge=1)              # по умолчанию 1, не меньше 1

@app.post("/items", status_code=201)
def add_item(item: ItemIn):
    for it in ITEMS:
        if it["name"] == item.name:
            raise HTTPException(status_code=409, detail="Такой товар уже есть")
    ITEMS.append({"name": item.name, "price": item.price, "qty": item.qty})
    return ITEMS[-1]

@app.get("/items")
def list_items(limit: int = 10, offset: int = 0):
    return ITEMS[offset:offset + limit]
```

| Ограничение | Смысл |
|---|---|
| `min_length`, `max_length` | длина строки |
| `gt`, `ge` | больше / не меньше |
| `lt`, `le` | меньше / не больше |

| Код | Когда |
|---|---|
| 422 | данные не прошли проверку модели (FastAPI отвечает сам) |
| 409 | конфликт: такая запись уже есть |
| 404 | записи нет |

- `...` в `Field(...)` — поле обязательное.
- Значение по умолчанию **не проверяется**: `Field(0, ge=1)` — ошибка автора.
- Параметры запроса `limit` и `offset` — просто аргументы функции со значениями по умолчанию.
"""

# --- a1: complete — добавить ограничения ---
PLAIN = IMP + "class ItemIn(BaseModel):\n    name: str\n    price: float\n    qty: int = 1\n"
S1 = HEAD + POST_A
t1 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "POST", "path": "/items", "json": {"name": "Чай", "price": 3.5}, "expected_status": 201, "expected_json": {"name": "Чай", "price": 3.5, "qty": 1}},
    {"id": "v2", "method": "POST", "path": "/items", "json": {"name": "Я", "price": 3.5}, "expected_status": 422, "hint": "Название короче двух символов не принимается"},
    {"id": "h1", "hidden": True, "method": "POST", "path": "/items", "json": {"name": "Сыр", "price": 0}, "expected_status": 422, "hint": "Цена ноль — это не «больше нуля»"},
    {"id": "h2", "hidden": True, "method": "POST", "path": "/items", "json": {"name": "Сыр", "price": -1}, "expected_status": 422},
    {"id": "h3", "hidden": True, "method": "POST", "path": "/items", "json": {"name": "Сыр", "price": 5, "qty": 0}, "expected_status": 422, "hint": "Количество не меньше единицы"},
    {"id": "h4", "hidden": True, "method": "POST", "path": "/items", "json": {"name": "Сыр", "price": 5, "qty": 3}, "expected_status": 201, "expected_json": {"name": "Сыр", "price": 5.0, "qty": 3}},
]}
a1 = asg("a1-constraints", "complete", "Ограничения модели",
         "В модели `ItemIn` пока нет ограничений. Добавьте через `Field`: название — **не короче 2 символов**, цена — **строго больше 0**, количество — **не меньше 1** (по умолчанию 1). Обработчик менять не нужно.",
         "Ставить ограничения Field в модели.", "Модель без ограничений.", "Плохие данные → 422.",
         ["Обработчик POST не меняйте."],
         hints("Импортировано: Field. Ограничение пишут как значение поля: name: str = Field(...).", "Многоточие первым аргументом делает поле обязательным.", "Название: Field(..., min_length=2). Цена: gt=0 — строго больше.", "Количество: по умолчанию 1, поэтому Field(1, ge=1).", "price: float = Field(..., gt=0), qty: int = Field(1, ge=1)"),
         t1, S1, "Field(...) обязательное поле с ограничениями; при нарушении FastAPI сам отвечает 422.",
         ["Корректный товар принимается.", "Нарушения каждого из трёх ограничений дают 422."],
         [(IMP + MODEL.replace("price: float = Field(..., gt=0)", "price: float").replace("qty: int = Field(1, ge=1)", "qty: int = 1") + POST_A, "Ограничена только длина названия: цена 0 и количество 0 проходят."),
          (S1.replace("gt=0", "ge=0"), "Цена ноль допустима: нужно строго больше нуля (gt)."),
          (S1.replace("min_length=2", "min_length=1"), "Название из одного символа проходит: нужно не короче двух."),
          (S1.replace("ge=1", "ge=0"), "Количество ноль допустимо: нужно не меньше единицы.")],
         starter=PLAIN + POST_A)

# --- a2: write — 409 ---
S2 = HEAD + POST_B + GET_ALL
t2 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "POST", "path": "/items", "json": {"name": "Чай", "price": 3.5}, "expected_status": 201, "expected_json": {"name": "Чай", "price": 3.5, "qty": 1}},
    {"id": "v2", "method": "POST", "path": "/items", "json": {"name": "Чай", "price": 4}, "expected_status": 409, "expected_json": {"detail": "Такой товар уже есть"}},
    {"id": "h1", "hidden": True, "method": "POST", "path": "/items", "json": {"name": "Сыр", "price": 7}, "expected_status": 201, "hint": "Другое название — это другой товар"},
    {"id": "h2", "hidden": True, "path": "/items", "expected_json": [{"name": "Чай", "price": 3.5, "qty": 1}, {"name": "Сыр", "price": 7.0, "qty": 1}],
     "hint": "Повторный товар в список попадать не должен"},
]}
a2 = asg("a2-conflict", "write", "Конфликт: товар уже есть",
         "Напишите **POST** `/items` (код **201**). Если товар с таким названием уже в списке — код **409** и `{\"detail\": \"Такой товар уже есть\"}`, а в список ничего не добавляется. Иначе добавьте `{\"name\", \"price\", \"qty\"}` и верните его.",
         "Проверять конфликт перед записью.", "Модель с ограничениями; список ITEMS.", "201 или 409.",
         ["Модель и GET не меняйте."],
         hints("Сначала проверка, потом запись.", "Пройдите по ITEMS циклом: for it in ITEMS.", "Название совпало — raise HTTPException(status_code=409, detail=\"Такой товар уже есть\").", "Если цикл закончился без исключения — ITEMS.append({...}).", "return ITEMS[-1] — вернуть добавленный товар."),
         t2, S2, "Проверка идёт до записи: исключение прерывает функцию раньше, чем товар попадёт в список.",
         ["Новый товар добавляется (201).", "Повтор даёт 409 и список не меняет."],
         [(S2.replace("status_code=409", "status_code=400"), "Для конфликта нужен код 409, а не 400."),
          (S2.replace(POST_B, '\n\n@app.post("/items", status_code=201)\ndef add_item(item: ItemIn):\n    ITEMS.append({"name": item.name, "price": item.price, "qty": item.qty})\n    return ITEMS[-1]\n'), "Проверки нет: повторный товар добавляется со статусом 201."),
          (S2.replace(POST_B, '\n\n@app.post("/items", status_code=201)\ndef add_item(item: ItemIn):\n    ITEMS.append({"name": item.name, "price": item.price, "qty": item.qty})\n    if sum(1 for it in ITEMS if it["name"] == item.name) > 1:\n        raise HTTPException(status_code=409, detail="Такой товар уже есть")\n    return ITEMS[-1]\n'), "Проверка после записи: дубликат уже попал в список.")],
         starter=HEAD + GET_ALL + "\n# POST /items с проверкой конфликта\n")

# --- a3: write — страницы ---
S3 = ('from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\nNUMS = list(range(1, 21))\n\n\n'
      '@app.get("/numbers")\ndef numbers(limit: int = 5, offset: int = 0):\n    return {"total": len(NUMS), "items": NUMS[offset:offset + limit]}\n')
t3 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/numbers", "expected_json": {"total": 20, "items": [1, 2, 3, 4, 5]}},
    {"id": "v2", "path": "/numbers", "params": {"limit": 3, "offset": 3}, "expected_json": {"total": 20, "items": [4, 5, 6]}, "hint": "offset — сколько пропустить, limit — сколько взять"},
    {"id": "h1", "hidden": True, "path": "/numbers", "params": {"limit": 5, "offset": 18}, "expected_json": {"total": 20, "items": [19, 20]}, "hint": "У конца списка страница короче"},
    {"id": "h2", "hidden": True, "path": "/numbers", "params": {"offset": 50}, "expected_json": {"total": 20, "items": []}, "hint": "total — всегда размер всего списка"},
    {"id": "h3", "hidden": True, "path": "/numbers", "params": {"limit": "abc"}, "expected_status": 422},
    {"id": "h4", "hidden": True, "path": "/numbers", "params": {"limit": 2}, "expected_json": {"total": 20, "items": [1, 2]}},
]}
a3 = asg("a3-paging", "write", "Страницы чисел",
         "В списке `NUMS` числа от 1 до 20. Напишите **GET** `/numbers` с параметрами запроса `limit` (по умолчанию **5**) и `offset` (по умолчанию **0**). Ответ: `{\"total\": <размер всего NUMS>, \"items\": <срез>}`.",
         "Использовать параметры запроса для страниц.", "limit и offset в запросе.", "total и срез items.",
         ["NUMS не меняйте."],
         hints("Параметры запроса — обычные аргументы функции: def numbers(limit: int = 5, offset: int = 0).", "Срез начинается с offset.", "Заканчивается на offset + limit (не на limit!).", "total — это len(NUMS), а не длина среза.", "return {\"total\": len(NUMS), \"items\": NUMS[offset:offset + limit]}"),
         t3, S3, "Срез от offset до offset + limit; total считают по всему списку, а не по странице.",
         ["Значения по умолчанию работают.", "Страница считается от offset."],
         [(S3.replace("NUMS[offset:offset + limit]", "NUMS[offset:limit]"), "Конец среза — limit, а не offset + limit."),
          (S3.replace("limit: int = 5", "limit: int = 10"), "По умолчанию должно быть 5 элементов."),
          (S3.replace('len(NUMS)', 'len(NUMS[offset:offset + limit])'), "total — размер всего списка, а не страницы.")],
         starter=S3.split("@app.get")[0] + "# GET /numbers с limit и offset\n")

# --- a4: fix — значение по умолчанию ---
BASE4 = ("from fastapi import FastAPI\nfrom pydantic import BaseModel, Field\n\napp = FastAPI()\nITEMS = []\n\n\n"
         "class ItemIn(BaseModel):\n    name: str = Field(..., min_length=2)\n    price: float = Field(..., gt=0)\n    qty: int = Field({D}, ge={G})\n")
POST4 = ('\n\n@app.post("/items", status_code=201)\ndef add_item(item: ItemIn):\n    ITEMS.append({"name": item.name, "price": item.price, "qty": item.qty})\n    return ITEMS[-1]\n')
S4 = BASE4.format(D=1, G=1) + POST4
BAD4 = BASE4.format(D=0, G=1) + POST4
t4 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "POST", "path": "/items", "json": {"name": "Чай", "price": 3.5}, "expected_status": 201, "expected_json": {"name": "Чай", "price": 3.5, "qty": 1},
     "hint": "Если количество не прислали, должна быть одна штука"},
    {"id": "v2", "method": "POST", "path": "/items", "json": {"name": "Сыр", "price": 5, "qty": 0}, "expected_status": 422},
    {"id": "h1", "hidden": True, "method": "POST", "path": "/items", "json": {"name": "Сыр", "price": 5, "qty": 4}, "expected_status": 201, "expected_json": {"name": "Сыр", "price": 5.0, "qty": 4}},
    {"id": "h2", "hidden": True, "method": "POST", "path": "/items", "json": {"name": "Х", "price": 5}, "expected_status": 422},
]}
a4 = asg("a4-default", "fix", "Количество по умолчанию",
         "Товар без поля `qty` должен получать **1 штуку**, а `qty: 0` — отклоняться (422). Сейчас товар без `qty` создаётся с нулём штук. Найдите ошибку.",
         "Помнить: значение по умолчанию не проверяется.", "Модель с Field.", "Товар без qty получает 1.",
         ["Ограничение ge=1 должно остаться."],
         hints("Отправьте товар без qty и посмотрите, что в ответе.", "В ответе qty равно 0 — откуда оно?", "Из значения по умолчанию в Field(0, …).", "Ограничение ge=1 значение по умолчанию не проверяет.", "Поставьте по умолчанию 1: qty: int = Field(1, ge=1)"),
         t4, S4, "Значение по умолчанию подставляется без проверки. Ограничение ge=1 отклоняет присланный ноль, но не замечает ноль по умолчанию — его нужно выбрать верным.",
         ["Без qty — одна штука.", "qty=0 отклоняется."],
         [(BAD4, "Ошибка осталась: по умолчанию ноль штук."),
          (BASE4.format(D=1, G=0) + POST4, "Ограничение ослаблено: qty=0 теперь принимается.")],
         starter=BAD4)

# --- a5: predict ---
CODE5 = ('from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\nfrom pydantic import BaseModel, Field\n\napp = FastAPI()\n\n\n'
         'class Q(BaseModel):\n    n: int = Field(..., ge=1, le=3)\n\n\n@app.post("/q")\ndef q(item: Q):\n    return {"n": item.n * 2}\n\n\n'
         '@app.get("/page")\ndef page(size: int = 2):\n    return list(range(size))\n\n\nclient = TestClient(app)\n'
         'print(client.post("/q", json={"n": 3}).json())\nprint(client.post("/q", json={"n": 4}).status_code)\nprint(client.post("/q", json={}).status_code)\n'
         'print(client.get("/page").json())\nprint(client.get("/page", params={"size": 3}).json())\nprint(client.get("/page", params={"size": "x"}).status_code)\n')
ans5 = "{'n': 6}\n422\n422\n[0, 1]\n[0, 1, 2]\n422"
a5 = asg("a5-predict", "predict", "Что напечатает клиент?",
         "Что напечатает программа? Каждая строка вывода — с новой строки.",
         "Предсказывать коды ответа и тела.", "—", "Шесть строк.", [],
         hints("Идём сверху вниз, каждый print — одна строка.", "n=3 укладывается в от 1 до 3 — обработчик выполняется и удваивает.", "n=4 больше le=3, а пустое тело не содержит обязательного n — в обоих случаях 422.", "GET /page без параметра берёт size=2: range(2) даёт [0, 1].", "size=3 — [0, 1, 2]; текст вместо числа — снова 422."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "n=3 проходит проверку (6), n=4 нарушает le, пустое тело нарушает обязательность — оба 422. size по умолчанию 2, с параметром 3; нечисловой size — 422.",
         ["Все шесть строк верны."],
         [("{'n': 6}\n400\n422\n[0, 1]\n[0, 1, 2]\n422", "Нарушение проверки модели — это 422, а не 400."),
          ("{'n': 6}\n422\n422\n[0, 1, 2]\n[0, 1, 2]\n422", "Без параметра берётся значение по умолчанию size=2, а не 3.")],
         code=CODE5)

skills = {"api.validation": "Проверка данных: Field и код 422", "api.errors": "Свои ошибки: 400, 404, 409", "api.paging": "Постраничный вывод: limit и offset"}
write_lesson("api-03-validation", "FastAPI: проверка данных и страницы",
             "Ограничивать данные в модели, возвращать понятные ошибки и отдавать длинные списки постранично.",
             list(skills), ["api-02-crud"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Значение по умолчанию не подходит под ограничение", "fix": "По умолчанию не проверяется: Field(0, ge=1) — ошибка автора."},
              {"mistake": "Срез items[offset:limit]", "fix": "Конец среза — offset + limit."},
              {"mistake": "Проверка конфликта после записи", "fix": "Сначала проверьте, потом записывайте — иначе дубликат уже в списке."},
              {"mistake": "400 вместо 409 или 422", "fix": "422 — данные не прошли модель; 409 — конфликт с существующим."}],
             min_pass=3, pack="api-basics", runner="A")
f = ROOT / "content/packs/api-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "api-03-validation" not in data["lessons"]:
    data["lessons"].append("api-03-validation")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

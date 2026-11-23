"""Урок FastAPI 4: middleware — слой вокруг каждого запроса: журнал, проверка ключа, порядок слоёв.
Поведение сверяет валидатор в CI настоящим FastAPI; локально настоящего FastAPI нет, ожидаемый вывод сцен получен рассуждением и проверяется там."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


HEAD1 = ("from fastapi import FastAPI, Request\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\nLOG = []\n\n\n")
MW1 = ('@app.middleware("http")\nasync def log_requests(request: Request, call_next):\n    response = await call_next(request)\n'
       '    LOG.append(f"{request.method} {request.url.path} -> {response.status_code}")\n    return response\n')
ROUTES1 = '\n\n@app.get("/hello")\ndef hello():\n    return {"msg": "привет"}\n'
RUN1 = '\n\nclient = TestClient(app)\nclient.get("/hello")\nclient.get("/missing")\nprint(LOG)\n'
C1 = HEAD1 + MW1 + ROUTES1 + RUN1
O1 = "['GET /hello -> 200', 'GET /missing -> 404']\n"

HEAD2 = ("from fastapi import FastAPI, Request\nfrom fastapi.responses import JSONResponse\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\n\n\n")
MW2 = ('@app.middleware("http")\nasync def require_key(request: Request, call_next):\n    if request.url.path != "/public" and request.headers.get("x-api-key") != "secret":\n'
       '        return JSONResponse({"detail": "Нужен ключ"}, status_code=401)\n    return await call_next(request)\n')
ROUTES2 = '\n\n@app.get("/public")\ndef public():\n    return {"open": True}\n\n\n@app.get("/private")\ndef private():\n    return {"open": False}\n'
RUN2 = ('\n\nclient = TestClient(app)\nprint(client.get("/public").status_code)\nprint(client.get("/private").status_code)\n'
        'print(client.get("/private", headers={"X-API-Key": "secret"}).json())\n')
C2 = HEAD2 + MW2 + ROUTES2 + RUN2
O2 = "200\n401\n{'open': False}\n"

C3 = ('from fastapi import FastAPI, Request\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\nORDER = []\n\n\n'
      '@app.middleware("http")\nasync def first(request: Request, call_next):\n    ORDER.append("first-in")\n    response = await call_next(request)\n    ORDER.append("first-out")\n    return response\n\n\n'
      '@app.middleware("http")\nasync def second(request: Request, call_next):\n    ORDER.append("second-in")\n    response = await call_next(request)\n    ORDER.append("second-out")\n    return response\n\n\n'
      '@app.get("/")\ndef root():\n    ORDER.append("handler")\n    return {}\n\n\nclient = TestClient(app)\nclient.get("/")\nprint(ORDER)\n')
O3 = "['second-in', 'first-in', 'handler', 'first-out', 'second-out']\n"

scenes = [
    scene("intro", "Что такое middleware", """
      Представьте охранника на входе в здание. Каждый посетитель проходит мимо него. Охранник смотрит на пропуск, записывает время и
      пропускает дальше, а на выходе иногда ещё и провожает. В веб-сервере такую роль играет middleware, по-русски промежуточный слой. Это
      функция, через которую проходит каждый запрос ещё до того, как он попадёт в обработчик, а ответ проходит через неё на обратном пути.
      Благодаря этому общие правила пишут один раз, а не в каждом обработчике: добавить новый маршрут, не забыв про проверки, становится проще. Типичные задачи слоя: вести журнал запросов, измерять время,
      проверять ключ доступа, добавлять заголовки безопасности. Сегодня мы напишем журнал и проверку ключа, а ещё узнаем, в каком порядке
      слои выполняются.""",
          [NOTE("**Middleware** — функция вокруг каждого запроса: до обработчика и после него.", at="В веб-сервере"),
           NOTE("Журнал · время · проверка ключа · заголовки безопасности · лимиты", at="Типичные задачи")]),
    scene("log", "Журнал запросов", """
      Вот самый простой слой. Его объявляют декоратором app middleware с аргументом http. Функция получает два параметра: request, это
      входящий запрос, и call_next, это обработчик, который стоит дальше по цепочке. Слово await перед вызовом call_next обязательно:
      вызов асинхронный. Всё, что написано до него, выполняется до обработчика, а всё, что после, уже после ответа. Здесь после ответа
      мы дописываем в журнал строку: метод, путь и код ответа. Слой обязан вернуть response, иначе клиент ничего не получит. Сделаем два
      запроса: к существующему адресу и к несуществующему. В журнале окажутся две записи, с кодами двести и четыреста четыре.""",
          [CLEAR(), T(C1, at="Вот самый простой"), HL(L(C1, "@app.middleware"), at="Его объявляют"), HL(L(C1, "async def"), at="Функция получает"),
           HL(L(C1, "await call_next"), at="Слово await"), HL(L(C1, "LOG.append"), at="мы дописываем в журнал"), HL(L(C1, "return response"), at="Слой обязан вернуть"),
           RUN(at="Сделаем два"), OUT(O1, at="Сделаем два")]),
    scene("guard", "Проверка ключа: ответ без обработчика", """
      Слой не обязан пропускать запрос дальше. Это похоже на охранника, который не пускает посетителя без пропуска: до кабинета тот просто не доходит. Слой может вернуть ответ сам, не вызывая call_next, и тогда до обработчика запрос просто не
      дойдёт. На этом строится защита. Проверяем заголовок X API Key: для всех путей, кроме публичного, он должен совпадать с ключом. Если
      не совпал, возвращаем JSONResponse с кодом четыреста один, то есть не авторизован. Иначе пропускаем запрос дальше. Попробуем:
      публичный адрес открыт, закрытый без ключа даёт четыреста один, а с верным ключом отвечает. Ключ в этом примере записан прямо в
      коде только для урока. В настоящем проекте его читают из переменной окружения и не публикуют в репозитории.""",
          [CLEAR(), T(C2, at="Слой не обязан"), HL(L(C2, "if request.url.path", 2), at="Проверяем заголовок"), HL(L(C2, "return JSONResponse"), at="возвращаем JSONResponse"),
           HL(L(C2, "return await call_next"), at="Иначе пропускаем"), RUN(at="Попробуем"), OUT(O2, at="Попробуем")]),
    scene("order", "Порядок слоёв", """
      Если слоёв несколько, они складываются как матрёшка. Запрос идёт снаружи внутрь, ответ изнутри наружу. Важная тонкость: слой,
      объявленный последним, оказывается самым внешним. Поэтому в нашем примере сначала сработает второй слой, потом первый, потом
      обработчик, а на обратном пути первый и затем второй. Запустим и посмотрим на порядок записей. Это важно для безопасности:
      проверку доступа ставят так, чтобы она выполнялась раньше остальных, а журнал стараются сделать самым внешним слоем, чтобы он
      видел и ответы, которые вернули другие слои.""",
          [CLEAR(), T(C3, at="Если слоёв"), HL(L(C3, "async def first"), at="слой, объявленный последним"), HL(L(C3, "async def second"), at="самым внешним"),
           RUN(at="Запустим и посмотрим"), OUT(O3, at="Запустим и посмотрим")]),
    scene("headers", "Заголовки безопасности и CORS", """
      Ещё одна работа для слоя: добавлять к каждому ответу заголовки, которые защищают браузер пользователя. Например, заголовок
      X Content Type Options со значением nosniff запрещает браузеру угадывать тип файла. Заголовок Strict Transport Security требует
      открывать сайт только по защищённому соединению HTTPS. Отдельная тема, CORS: по умолчанию браузер не разрешает странице с одного
      сайта обращаться к API на другом. Сервер сам перечисляет, каким сайтам можно. Здесь важно правило: разрешайте только свои адреса,
      а не звёздочку для всех, особенно если запросы несут права пользователя. В FastAPI для этого есть готовый слой CORSMiddleware,
      писать его вручную не нужно.""",
          [CLEAR(), NOTE("`X-Content-Type-Options: nosniff` — браузер не угадывает тип файла", at="X Content Type Options"),
           NOTE("`Strict-Transport-Security` — только HTTPS", at="Strict Transport Security"),
           NOTE("**CORS**: перечисляйте свои адреса, а не `*`; готовый слой — `CORSMiddleware`", at="Отдельная тема")]),
    scene("logging", "Что писать в журнал", """
      Журнал нужен, чтобы разбирать сбои и замечать атаки. В запись обычно кладут время, метод, путь, код ответа и время выполнения. А вот
      чего в журнале быть не должно: паролей, токенов, ключей доступа, номеров карт и других персональных данных. Журнал читают
      многие, а хранится он долго, и утечка из него так же опасна, как утечка из базы. Если нужно связать запись с пользователем, пишите
      его номер, а не токен. Для настоящих проектов вместо print используют модуль logging: у него есть уровни от отладки до критических
      ошибок, и их можно включать и выключать, не меняя код.""",
          [CLEAR(), NOTE("В журнал: время · метод · путь · код ответа · длительность · номер пользователя", at="В запись обычно"),
           NOTE("**Не** в журнал: пароли, токены, ключи, номера карт, персональные данные", at="А вот"),
           NOTE("Модуль `logging`: уровни `DEBUG` · `INFO` · `WARNING` · `ERROR`", at="Для настоящих проектов")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: забыли await перед call_next. Тогда слой вернёт не ответ, а незавершённую задачу, и сервер упадёт.
      Вторая: забыли вернуть response. Клиент ничего не получит. Третья: проверка доступа стоит после вызова call_next. Обработчик уже
      выполнился, и запрет бесполезен: запись в базу произошла. Проверять нужно до вызова. Четвёртая: записать в журнал пароль или
      токен целиком. Пишите только то, что безопасно показать любому, кто откроет журнал.""",
          [NOTE("Ошибка 1: нет `await` перед `call_next(request)`.", at="Первая"),
           NOTE("Ошибка 2: нет `return response` → клиент без ответа.", at="Вторая"),
           NOTE("Ошибка 3: проверка доступа **после** `call_next` → обработчик уже выполнился.", at="Третья"),
           NOTE("Ошибка 4: пароль или токен в журнале.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. Middleware оборачивает каждый запрос: код до call_next работает до обработчика, код после — после. Слой может записать
      журнал, а может сам вернуть ответ и остановить запрос, например при неверном ключе. Слои складываются матрёшкой, последний объявленный
      оказывается снаружи. В журнал не пишут секреты. В заданиях вы напишете слой журнала и слой проверки ключа, исправите слой без
      await и предскажете порядок выполнения. Критерий прохождения: решить не меньше трёх заданий из четырёх. Запросы проверяются
      тестовым клиентом без сети.""",
          [NOTE("`@app.middleware(\"http\")` · `response = await call_next(request)` · `return response` · ответ без `call_next` останавливает запрос", at="Подведём итог")]),
]

notes = """
# FastAPI: middleware

Middleware — функция, через которую проходит каждый запрос: код до `call_next` выполняется до обработчика, код после — после.

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()
LOG = []

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)          # дальше по цепочке — обработчик
    LOG.append(f"{request.method} {request.url.path} -> {response.status_code}")
    return response                               # ответ нужно вернуть

@app.middleware("http")
async def require_key(request: Request, call_next):
    if request.headers.get("x-api-key") != API_KEY:
        return JSONResponse({"detail": "Нужен ключ"}, status_code=401)   # запрос дальше не идёт
    return await call_next(request)
```

- Слой может вернуть ответ **сам**, не вызывая `call_next`: так работает защита.
- Слои вкладываются как матрёшка: **последний объявленный — самый внешний** (срабатывает первым).
- Проверку доступа делают **до** `call_next`.
- Не пишите в журнал пароли, токены, ключи, номера карт. Пишите номер пользователя, а не токен.
- Ключ в учебном коде записан в тексте только ради урока; в проекте его читают из переменной окружения, не из репозитория, а сравнивают через `hmac.compare_digest`.
- Для настоящего журнала используют модуль `logging` с уровнями `DEBUG`, `INFO`, `WARNING`, `ERROR`.
"""

START = ("from fastapi import FastAPI, Request\n\napp = FastAPI()\nLOG = []\n\n\n# Здесь напишите middleware\n\n\n"
         '@app.get("/hello")\ndef hello():\n    return {"msg": "привет"}\n\n\n@app.get("/log")\ndef show_log():\n    return LOG\n')
SOL1 = ("from fastapi import FastAPI, Request\n\napp = FastAPI()\nLOG = []\n\n\n" + MW1 +
        '\n\n@app.get("/hello")\ndef hello():\n    return {"msg": "привет"}\n\n\n@app.get("/log")\ndef show_log():\n    return LOG\n')
t1 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/hello", "expected_json": {"msg": "привет"}},
    {"id": "v2", "path": "/missing", "expected_status": 404},
    {"id": "v3", "path": "/log", "expected_json": ["GET /hello -> 200", "GET /missing -> 404"], "hint": "Запись делают после ответа: в ней метод, путь и код ответа"},
    {"id": "h1", "hidden": True, "path": "/log", "expected_json": ["GET /hello -> 200", "GET /missing -> 404", "GET /log -> 200"]},
]}
a1 = asg("a1-log", "write", "Журнал запросов",
         "Напишите middleware: после каждого ответа добавляйте в список `LOG` строку вида `GET /hello -> 200` (метод, путь, код ответа). Маршруты `/hello` и `/log` уже есть. "
         "Слой должен вернуть ответ обработчика без изменений.",
         "Написать middleware с call_next.", "Запросы к /hello, /missing, /log.", "LOG с записями по порядку запросов.",
         ["Используйте @app.middleware(\"http\")."],
         hints("Слой объявляется декоратором @app.middleware(\"http\") над async-функцией.", "Функция получает request и call_next.",
               "Ответ получают так: response = await call_next(request).", "Строку для журнала собирайте после получения ответа: нужен response.status_code.",
               "В конце верните response; запись: LOG.append(f\"{request.method} {request.url.path} -> {response.status_code}\")."),
         t1, SOL1, "call_next вызывает обработчик и возвращает ответ; после этого код слоя знает код ответа и может записать его в журнал.",
         ["Есть слой с @app.middleware.", "Запись после ответа.", "Ответ возвращается."],
         [(START.replace("# Здесь напишите middleware", '@app.middleware("http")\nasync def log_requests(request: Request, call_next):\n    LOG.append(f"{request.method} {request.url.path}")\n    return await call_next(request)'),
           "В записи нет кода ответа: он известен только после call_next."),
          (START.replace("# Здесь напишите middleware", '@app.middleware("http")\nasync def log_requests(request: Request, call_next):\n    response = await call_next(request)\n    LOG.append(f"{request.method} {request.url.path} -> 200")\n    return response'),
           "Код ответа записан числом 200 вместо response.status_code."),
          (START.replace("# Здесь напишите middleware", '@app.middleware("http")\nasync def log_requests(request: Request, call_next):\n    response = await call_next(request)\n    LOG.append(f"{request.method} {request.url.path} -> {response.status_code}")'),
           "Слой не вернул response: клиент не получит ответ.")],
         starter=START)

# --- a2: API key ---
START2 = ("from fastapi import FastAPI, Request\nfrom fastapi.responses import JSONResponse\n\napp = FastAPI()\nAPI_KEY = \"academy-key\"\n\n\n# Здесь напишите middleware\n\n\n"
          '@app.get("/health")\ndef health():\n    return {"status": "ok"}\n\n\n@app.get("/secret")\ndef secret():\n    return {"data": 42}\n')
MWK = ('@app.middleware("http")\nasync def require_key(request: Request, call_next):\n    if request.url.path != "/health" and request.headers.get("x-api-key") != API_KEY:\n'
       '        return JSONResponse({"detail": "Нужен ключ API"}, status_code=401)\n    return await call_next(request)')
SOL2 = START2.replace("# Здесь напишите middleware", MWK)
t2 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/health", "expected_json": {"status": "ok"}},
    {"id": "v2", "path": "/secret", "expected_status": 401, "expected_json": {"detail": "Нужен ключ API"}, "hint": "Без заголовка X-API-Key закрытые пути недоступны"},
    {"id": "h1", "hidden": True, "path": "/secret", "headers": {"X-API-Key": "wrong"}, "expected_status": 401, "hint": "Нужно сравнивать значение ключа, а не только наличие заголовка"},
    {"id": "h2", "hidden": True, "path": "/secret", "headers": {"X-API-Key": "academy-key"}, "expected_json": {"data": 42}},
]}
a2 = asg("a2-key", "write", "Проверка ключа",
         "Напишите middleware: все пути, кроме `/health`, требуют заголовок `X-API-Key` со значением из `API_KEY`. Если ключа нет или он неверный, ответьте кодом **401** и `{\"detail\": \"Нужен ключ API\"}` "
         "(класс `JSONResponse` импортирован), не вызывая обработчик. Иначе пропустите запрос дальше.",
         "Остановить запрос в слое, не вызывая call_next.", "Запросы с ключом и без.", "401 без верного ключа, ответ обработчика — с верным.",
         ["Ключ в коде — только учебный; в проекте его читают из переменной окружения."],
         hints("Слой — это @app.middleware(\"http\") async def …(request, call_next).", "Значение заголовка: request.headers.get(\"x-api-key\").",
               "Если путь не /health и ключ не равен API_KEY — верните JSONResponse(…, status_code=401), call_next не вызывайте.", "Для остальных запросов: return await call_next(request).",
               "Условие: request.url.path != \"/health\" and request.headers.get(\"x-api-key\") != API_KEY."),
         t2, SOL2, "Слой возвращает ответ сам и не вызывает call_next, поэтому обработчик защищённых путей не выполняется. Публичный /health пропускается дальше.",
         ["Закрытые пути требуют верный ключ.", "/health открыт.", "Запрос без ключа не доходит до обработчика."],
         [(START2.replace("# Здесь напишите middleware", MWK.replace(' request.url.path != "/health" and', "")), "Проверка идёт и для /health: публичный путь тоже закрыт."),
          (START2.replace("# Здесь напишите middleware", MWK.replace('request.headers.get("x-api-key") != API_KEY', '"x-api-key" not in request.headers')), "Проверяется только наличие заголовка, а не значение ключа."),
          (START2.replace("# Здесь напишите middleware", MWK.replace("status_code=401", "status_code=403")), "Нет ключа — это 401 (не авторизован), а не 403.")],
         starter=START2)

# --- a3: fix — await ---
BAD3 = ("from fastapi import FastAPI, Request\n\napp = FastAPI()\nCOUNT = {\"requests\": 0}\n\n\n@app.middleware(\"http\")\nasync def count_requests(request: Request, call_next):\n"
        "    COUNT[\"requests\"] += 1\n    response = call_next(request)\n    return response\n\n\n"
        '@app.get("/ping")\ndef ping():\n    return {"pong": True}\n\n\n@app.get("/stats")\ndef stats():\n    return COUNT\n')
S3 = BAD3.replace("response = call_next(request)", "response = await call_next(request)")
t3 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/ping", "expected_json": {"pong": True}, "hint": "Слой должен вернуть ответ обработчика, а не незавершённую задачу"},
    {"id": "v2", "path": "/ping", "expected_json": {"pong": True}},
    {"id": "h1", "hidden": True, "path": "/stats", "expected_json": {"requests": 3}, "hint": "Счётчик увеличивается до обработчика: /stats видит и свой запрос"},
]}
a3 = asg("a3-await", "fix", "Слой без await",
         "Сервер падает на любом запросе: middleware считает запросы, но не получает ответ обработчика как нужно. Исправьте слой, чтобы `/ping` отвечал, а `/stats` показывал число запросов, включая собственный.",
         "Находить пропущенный await.", "—", "После двух /ping и одного /stats: {\"requests\": 3}.",
         ["Счёт увеличивается до вызова обработчика — так и оставьте."],
         hints("Исключение говорит об объекте coroutine: функция вернула не ответ.", "call_next — асинхронная функция.", "Результат асинхронного вызова нужно дождаться.",
               "Перед вызовом поставьте await.", "response = await call_next(request)."),
         t3, S3, "call_next асинхронная: без await в response лежит незавершённая задача, а не ответ. После await слой получает настоящий ответ.",
         ["Перед call_next стоит await.", "Счётчик считает запросы."],
         [(BAD3, "Ошибка осталась: нет await."),
          (S3.replace('    COUNT["requests"] += 1\n    response = await call_next(request)\n    return response', '    response = await call_next(request)\n    COUNT["requests"] += 1\n    return response'),
           "Счёт увеличивается после обработчика: /stats не видит собственный запрос."),
          (S3.replace("    return response\n\n\n@app.get(\"/ping\")", "\n\n@app.get(\"/ping\")"), "Слой не возвращает response.")],
         starter=BAD3)

# --- a4: predict ---
ans4 = "['second-in', 'first-in', 'handler', 'first-out', 'second-out']"
a4 = asg("a4-predict", "predict", "Порядок слоёв",
         "Два слоя записывают в список `ORDER` до и после обработчика. Что напечатает программа? Запишите вывод одной строкой.",
         "Понимать вложенность слоёв.", "—", "Одна строка со списком.", [],
         hints("Слои вкладываются как матрёшка.", "Слой, объявленный последним, самый внешний.", "Сначала срабатывает самый внешний слой, потом более внутренний, потом обработчик.",
               "На обратном пути порядок обратный: сначала внутренний, потом внешний.", "Внешний — second, внутренний — first."),
         {"kind": "answer", "expected_answer": ans4}, ans4,
         "Последний объявленный слой second самый внешний: second-in, first-in, handler, затем на обратном пути first-out и second-out.",
         ["Порядок верный."],
         [("['first-in', 'second-in', 'handler', 'second-out', 'first-out']", "Последний объявленный слой — самый внешний, поэтому первым срабатывает second."),
          ("['second-in', 'first-in', 'handler', 'second-out', 'first-out']", "На обратном пути сначала выходит внутренний слой first.")],
         code=C3)

skills = {"api.middleware": "Middleware: слой вокруг запроса", "api.logging": "Журнал запросов", "api.apikey": "Проверка ключа API"}
write_lesson("api-04-middleware", "FastAPI: middleware и журнал",
             "Писать middleware: журнал запросов и проверка ключа, понимать порядок слоёв и не писать секреты в журнал.",
             list(skills), ["api-03-validation"], scenes, notes, [a1, a2, a3, a4],
             [{"mistake": "Нет await перед call_next", "fix": "call_next асинхронная: response = await call_next(request)."},
              {"mistake": "Слой не возвращает response", "fix": "Всегда возвращайте ответ: return response."},
              {"mistake": "Проверка доступа после call_next", "fix": "Проверяйте до call_next: иначе обработчик уже выполнится."},
              {"mistake": "Секреты в журнале", "fix": "Не пишите пароли, токены и ключи; пишите номер пользователя."}],
             min_pass=3, pack="api-basics", runner="A")
f = ROOT / "content/packs/api-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "api-04-middleware" not in data["lessons"]:
    data["lessons"].append("api-04-middleware")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

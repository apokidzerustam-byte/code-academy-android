"""Урок FastAPI 5: пароли и токены — хеш пароля (PBKDF2), токен HS256 по формату JWT, защита маршрутов через Depends, коды 401 и 403.
Хеш и токен — на стандартной библиотеке: так видно, как это устроено. В настоящем проекте берут проверенные библиотеки (argon2/bcrypt, PyJWT).
Токен HS256 сверен с общеизвестным примером jwt.io. Поведение FastAPI сверяет валидатор в CI."""
from lib import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


# ---------- общие куски кода ----------
HELP = '''import base64
import hashlib
import hmac
import json


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign(text: str, secret: str) -> str:
    return b64(hmac.new(secret.encode(), text.encode(), hashlib.sha256).digest())


def make_token(payload: dict, secret: str) -> str:
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = b64(json.dumps(payload, separators=(",", ":")).encode())
    return header + "." + body + "." + sign(header + "." + body, secret)


def read_token(token: str, secret: str, now: int):
    parts = token.split(".")
    if len(parts) != 3:
        return None
    if not hmac.compare_digest(parts[2].encode(), sign(parts[0] + "." + parts[1], secret).encode()):
        return None
    payload = json.loads(unb64(parts[1]))
    if payload.get("exp", 0) < now:
        return None
    return payload
'''
ns = {}
exec(HELP, ns)
mk_tok, b64f = ns["make_token"], ns["b64"]
SECRET = "lesson-secret"
T_OK = mk_tok({"sub": "anna", "exp": 9999999999}, SECRET)
T_OLD = mk_tok({"sub": "anna", "exp": 1}, SECRET)
T_OTHER = mk_tok({"sub": "anna", "exp": 9999999999}, "attacker-secret")
T_FORGED = mk_tok({"sub": "boss", "exp": 9999999999}, "attacker-secret")
_h, _b, _s = T_OK.split(".")
T_TAMPER = _h + "." + b64f(b'{"sub":"boss","exp":9999999999}') + "." + _s   # чужая «полезная нагрузка» с подписью Анны
T_ADMIN = mk_tok({"sub": "boss", "role": "admin", "exp": 9999999999}, SECRET)

# ---------- коды сцен ----------
D1 = ('import hashlib\n\n\ndef hash_password(password: str, salt: str) -> str:\n    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 1000).hex()\n\n\n'
      'stored = hash_password("qwerty", "s1")\nprint(len(stored))\nprint(stored == hash_password("qwerty", "s1"))\nprint(stored == hash_password("qwerty", "s2"))\n'
      'print(stored == hash_password("Qwerty", "s1"))\n')
O1 = run_out(D1)

D2 = HELP + ('\n\nSECRET = "lesson-secret"\ntoken = make_token({"sub": "anna", "exp": 100}, SECRET)\nprint(token.count("."))\nprint(read_token(token, SECRET, 50))\n'
             'print(read_token(token, SECRET, 150))\nprint(read_token(token + "x", SECRET, 50))\nprint(read_token(token, "other", 50))\n')
O2 = run_out(D2)

D3 = ("import base64\nimport hashlib\nimport hmac\nimport json\nimport time\n\nfrom fastapi import Depends, FastAPI, Header, HTTPException\nfrom fastapi.testclient import TestClient\n\n"
      "SECRET = \"lesson-secret\"\n\n\n" + HELP.split("import json\n\n\n", 1)[1] +
      '\n\napp = FastAPI()\n\n\ndef current_user(authorization: str = Header(None)) -> dict:\n    if not authorization or not authorization.startswith("Bearer "):\n'
      '        raise HTTPException(status_code=401, detail="Нужен токен")\n    payload = read_token(authorization[7:], SECRET, int(time.time()))\n    if payload is None:\n'
      '        raise HTTPException(status_code=401, detail="Неверный токен")\n    return payload\n\n\n@app.get("/me")\ndef me(user: dict = Depends(current_user)):\n    return {"user": user["sub"]}\n\n\n'
      'client = TestClient(app)\ntoken = make_token({"sub": "anna", "exp": 9999999999}, SECRET)\nprint(client.get("/me").status_code)\n'
      'print(client.get("/me", headers={"Authorization": "Bearer " + token}).json())\nprint(client.get("/me", headers={"Authorization": "Bearer abc"}).json())\n')
O3 = "401\n{'user': 'anna'}\n{'detail': 'Неверный токен'}\n"
D3B = ('\n\ndef require_admin(user: dict = Depends(current_user)) -> dict:\n    if user.get("role") != "admin":\n        raise HTTPException(status_code=403, detail="Недостаточно прав")\n    return user\n\n\n'
       '@app.get("/admin")\ndef admin_panel(user: dict = Depends(require_admin)):\n    return {"hello": user["sub"]}\n\n\n'
       'admin_token = make_token({"sub": "boss", "role": "admin", "exp": 9999999999}, SECRET)\nprint(client.get("/admin", headers={"Authorization": "Bearer " + token}).status_code)\n'
       'print(client.get("/admin", headers={"Authorization": "Bearer " + admin_token}).json())\n')
O3B = O3 + "403\n{'hello': 'boss'}\n"

scenes = [
    scene("intro", "Кто вы и что вам можно", """
      Два похожих слова, которые нельзя путать. Аутентификация отвечает на вопрос «кто вы»: сервер проверяет, что вы действительно Анна. Авторизация
      отвечает на вопрос «что вам можно»: может ли Анна открыть панель администратора. Типичная схема такая. Пользователь присылает логин и
      пароль. Сервер проверяет пароль и выдаёт токен: короткую строку, подписанную сервером. С этого момента клиент прикладывает токен к каждому
      запросу в заголовке Authorization, а сервер проверяет подпись и срок действия. Пароль больше нигде не путешествует. Сегодня мы разберём
      каждый шаг: как хранить пароли, как устроен токен и как защитить маршрут.""",
          [NOTE("**Аутентификация** — кто вы · **авторизация** — что вам можно", at="Два похожих"),
           NOTE("логин + пароль → токен → `Authorization: Bearer <токен>` → проверка подписи и срока", at="Типичная схема")]),
    scene("hash", "Хранение паролей", """
      Первое правило: пароль нельзя хранить как есть. Если базу украдут, все пароли окажутся у злоумышленника. Вместо пароля хранят хеш,
      результат необратимого преобразования. Но обычный быстрый хеш не годится: перебрать миллионы паролей получится за секунды. Поэтому нужны
      две вещи. Первая: соль, это случайная строка у каждого пользователя, чтобы одинаковые пароли давали разные хеши. Вторая: медленная функция,
      например PBKDF2, которая повторяет вычисление много раз. Вот функция: пароль, соль, алгоритм SHA256 и число повторений. В учебном примере
      их тысяча, чтобы код работал быстро, а в настоящих проектах счёт идёт на сотни тысяч, а то и берут готовые библиотеки argon2 или bcrypt.
      Проверим: хеш всегда одной длины, одинаковые входные данные дают одинаковый результат, а соль или регистр меняют его полностью.""",
          [CLEAR(), T(D1, at="Первое правило"), HL(L(D1, "def hash_password"), at="Вот функция"), HL(L(D1, "pbkdf2_hmac"), at="Вот функция"),
           HL(L(D1, "stored ="), at="Проверим"), RUN(at="Проверим"), OUT(O1, at="Проверим")]),
    scene("token", "Токен: подписанная строка", """
      Теперь токен. Его формат называется JWT, и устроен он просто: три части через точку. Заголовок говорит, каким алгоритмом подписано. Содержимое
      хранит данные, например имя пользователя и срок действия под именем exp. Подпись вычисляется из первых двух частей и секретного ключа сервера.
      Заметьте: содержимое не зашифровано, его может прочитать любой, поэтому секретные данные туда класть нельзя. Защита другая: подделать
      содержимое не получится, подпись перестанет сходиться. Функция make token собирает три части. Функция read token делает обратное: сверяет
      подпись, причём через compare digest, чтобы время сравнения не выдавало информацию, а потом проверяет срок. Любая проблема даёт None.
      Запустим: токен с двумя точками читается, просроченный нет, с подпорченной подписью нет, с другим ключом тоже нет.""",
          [CLEAR(), T(D2, at="Теперь токен"), HL(L(D2, "def sign"), at="Подпись вычисляется"), HL(L(D2, "def make_token", 4), at="Функция make token"),
           HL(L(D2, "def read_token", 10), at="Функция read token"), RUN(at="Запустим"), OUT(O2, at="Запустим")]),
    scene("depends", "Защита маршрута через Depends", """
      Как проверять токен в каждом защищённом маршруте, не копируя код? В FastAPI для этого есть зависимости. Это обычная функция, которую маршрут
      подключает через Depends. Наша функция current user читает заголовок Authorization. Если заголовка нет или он не начинается со слова
      Bearer, отвечаем четыреста один с понятным сообщением. Иначе проверяем токен. Подпись или срок не сошлись, снова четыреста один. Если всё
      хорошо, возвращаем данные токена. Маршрут me просто просит зависимость в параметре и получает уже проверенного пользователя. Проверим три
      случая: без токена, с верным токеном и с мусором вместо токена.""",
          [CLEAR(), T(D3, at="Как проверять"), HL(L(D3, "def current_user"), at="Наша функция current user"), HL(L(D3, "raise HTTPException(status_code=401, detail=\"Нужен токен\")"), at="отвечаем четыреста один"),
           HL(L(D3, "payload = read_token"), at="Иначе проверяем токен"), HL(L(D3, "user: dict = Depends"), at="Маршрут me"), RUN(at="Проверим три"), OUT(O3, at="Проверим три")]),
    scene("roles", "Авторизация: роли и код 403", """
      Теперь авторизация. Допустим, панель управления доступна только администраторам. Добавим вторую зависимость. Она опирается на первую:
      сначала current user проверит токен, а затем require admin посмотрит на поле role. Если роли нет, это уже не четыреста один, а четыреста
      три: вы известны серверу, но вам нельзя. Запомните различие. Четыреста один значит «я не знаю, кто вы», четыреста три значит «знаю, но
      нельзя». Проверим: обычный пользователь Анна получает отказ, а администратор попадает в панель.""",
          [T(D3B, at="Допустим, панель"), HL(L(D3 + D3B, "def require_admin", 4), at="Добавим вторую зависимость"), HL(L(D3 + D3B, "status_code=403"), at="четыреста три"),
           RUN(at="Проверим: обычный"), OUT(O3B, at="Проверим: обычный")]),
    scene("practice", "Правила безопасной работы", """
      Несколько правил, которые важнее любого кода. Секретный ключ подписи читают из переменной окружения, а не пишут в коде и не кладут в
      репозиторий: тот, кто знает ключ, может выпускать токены от чужого имени. Токены живут недолго, обычно минуты или часы. Сайт работает
      только по HTTPS, иначе токен можно подсмотреть по дороге. При неверном входе пишите одно и то же сообщение, не уточняя, что неверно, логин
      или пароль, иначе злоумышленник узнает, какие логины существуют. Ограничивайте число попыток входа. Не пишите токены и пароли в журнал.
      И последнее: в настоящих проектах не изобретают защиту сами, а берут проверенные библиотеки. Мы разбирали устройство, чтобы понимать,
      что они делают.""",
          [CLEAR(), NOTE("Ключ подписи — из переменной окружения, не из кода и не из репозитория", at="Секретный ключ"),
           NOTE("Токены живут недолго · только HTTPS · одно сообщение об ошибке входа · лимит попыток", at="Токены живут"),
           NOTE("Не пишите токены и пароли в журнал; в настоящем проекте — проверенные библиотеки (argon2/bcrypt, PyJWT)", at="Не пишите токены")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: хранить пароль как есть или обычным быстрым хешем без соли. Вторая: читать содержимое токена, не проверив
      подпись. Тогда любой сам напишет себе роль администратора. Третья: не проверять срок действия, и украденный токен работает вечно.
      Четвёртая: путать коды. Нет токена или он плохой, это четыреста один. Токен хороший, но прав мало, это четыреста три. Ещё одна
      частая ошибка: сравнивать подписи обычным равенством. Правильнее compare digest.""",
          [NOTE("Ошибка 1: пароль открытым текстом или быстрый хеш без соли.", at="Первая"),
           NOTE("Ошибка 2: токен прочитан без проверки подписи.", at="Вторая"),
           NOTE("Ошибка 3: не проверен срок `exp`.", at="Третья"),
           NOTE("Ошибка 4: путаница 401 и 403.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. Пароль хранят только в виде хеша с солью, который считает медленная функция вроде PBKDF2. Токен состоит из трёх частей, и его
      подпись защищает содержимое от подделки. Зависимость current user проверяет подпись и срок, а require admin добавляет проверку роли. Нет или
      плох токен, это четыреста один, нет прав, это четыреста три. В заданиях вы напишете функцию хеширования и функцию выпуска токена, зависимость
      для защиты маршрута, исправите зависимость, которая не проверяет подпись, и предскажете результат проверки токена. Критерий прохождения:
      решить не меньше трёх заданий из пяти. Всё проверяется тестовым клиентом без сети.""",
          [NOTE("`pbkdf2_hmac` + соль · токен `заголовок.содержимое.подпись` · `Depends(current_user)` · 401 — кто вы? · 403 — нельзя", at="Подведём итог")]),
]

notes = """
# FastAPI: пароли, токены и защита маршрутов

**Аутентификация** — кто вы; **авторизация** — что вам можно.

## Пароль — только хеш с солью

```python
import hashlib

def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 1000).hex()
```

Соль — случайная строка у каждого пользователя. В учебном коде 1000 повторений, чтобы работало быстро; в проектах берут сотни тысяч повторений или готовые argon2 / bcrypt.

## Токен (формат JWT, алгоритм HS256)

`заголовок.содержимое.подпись`, каждая часть — base64url. Подпись = HMAC-SHA256 от «заголовок.содержимое» с секретным ключом.

```py
token = make_token({"sub": "anna", "exp": 1735689600}, SECRET)
read_token(token, SECRET, now)   # данные или None (подпись неверна / срок вышел)
```

Содержимое **не зашифровано** — секретов в нём быть не должно. Подпись защищает от подделки, а сравнивать её нужно через `hmac.compare_digest`.

## Защита маршрута

```py
def current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Нужен токен")
    payload = read_token(authorization[7:], SECRET, int(time.time()))
    if payload is None:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return payload

@app.get("/me")
def me(user: dict = Depends(current_user)):
    return {"user": user["sub"]}
```

| Код | Смысл |
|---|---|
| 401 | не знаю, кто вы: нет токена, он плохой или просрочен |
| 403 | знаю, кто вы, но прав недостаточно |

- Ключ подписи читают из переменной окружения; в учебных примерах он записан в тексте только ради урока.
- Токены короткоживущие; только HTTPS; не пишите токены и пароли в журнал; одно сообщение об ошибке входа; ограничивайте число попыток.
- Учебная реализация показывает устройство. В настоящем проекте берите проверенные библиотеки (argon2 или bcrypt для паролей, PyJWT для токенов).
"""

# ---------- a1: hash_password (function) ----------
SOL1 = 'import hashlib\n\n\ndef hash_password(password: str, salt: str) -> str:\n    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 1000).hex()\n'
STR1 = "import hashlib\n\n# Напишите функцию hash_password(password, salt)\n"
a1 = fn_task("a1-hash", "Хеш пароля",
             "Напишите функцию `hash_password(password: str, salt: str) -> str`: хеш **PBKDF2-HMAC-SHA256** (`hashlib.pbkdf2_hmac`) от пароля с данной солью, **1000** повторений, результат — строка в шестнадцатеричном виде (`.hex()`). "
             "Пароль и соль нужно перевести в байты методом `encode()`.",
             "hash_password", SOL1,
             [("qwerty", "s1"), ("qwerty", "s2"), ("Qwerty", "s1"), ("пароль", "соль"), ("", "x")],
             [(SOL1.replace('hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 1000).hex()', 'hashlib.sha256((salt + password).encode()).hexdigest()'), "Одиночный быстрый хеш: пароли перебираются слишком быстро — нужна медленная функция PBKDF2."),
              (SOL1.replace("1000", "1"), "Одно повторение: функция почти не замедляет подбор. Нужно 1000."),
              (SOL1.replace('salt.encode()', 'b"fixed"'), "Соль игнорируется: одинаковые пароли получают одинаковые хеши у всех пользователей."),
              (SOL1.replace('.hex()', ''), "Возвращаются байты, а нужна строка: добавьте .hex().")],
             hints("Нужна готовая функция из hashlib: pbkdf2_hmac.", "Её аргументы: имя алгоритма, пароль в байтах, соль в байтах, число повторений.",
                   "Строку переводят в байты методом encode().", "Результат — байты; в строку из шестнадцатеричных цифр их превращает метод hex().",
                   "return hashlib.pbkdf2_hmac(\"sha256\", password.encode(), salt.encode(), 1000).hex()"),
             "PBKDF2 повторяет HMAC-SHA256 много раз, поэтому подбор паролей замедляется; соль делает хеши разными у разных пользователей. hex() превращает байты в строку.",
             type="write", starter=STR1, goal="Хешировать пароль с солью медленной функцией.",
             criteria=["Используется pbkdf2_hmac.", "1000 повторений.", "Соль участвует в хеше.", "Результат — строка hex."])

# ---------- a2: make_token (function) ----------
SOL2 = ('import base64\nimport hashlib\nimport hmac\nimport json\n\n\ndef b64(data: bytes) -> str:\n    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()\n\n\n'
        'def sign(text: str, secret: str) -> str:\n    return b64(hmac.new(secret.encode(), text.encode(), hashlib.sha256).digest())\n\n\n'
        'def make_token(payload: dict, secret: str) -> str:\n    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())\n'
        '    body = b64(json.dumps(payload, separators=(",", ":")).encode())\n    return header + "." + body + "." + sign(header + "." + body, secret)\n')
STR2 = SOL2.split("def make_token")[0] + "# Напишите функцию make_token(payload, secret)\n"
JWT_IO = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
assert mk_tok(JWT_IO, "your-256-bit-secret") == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
a2 = fn_task("a2-token", "Выпуск токена",
             "Функции `b64` (base64url без `=`) и `sign` (подпись HMAC-SHA256) уже написаны. Допишите `make_token(payload: dict, secret: str) -> str`: "
             "заголовок — JSON `{\"alg\": \"HS256\", \"typ\": \"JWT\"}`, содержимое — JSON из `payload` (в обоих `json.dumps(..., separators=(\",\", \":\"))`, порядок ключей как в словаре), "
             "обе части кодируются через `b64`. Результат — `заголовок.содержимое.подпись`, подпись — `sign(заголовок + \".\" + содержимое, secret)`.",
             "make_token", SOL2,
             [({"sub": "1234567890", "name": "John Doe", "iat": 1516239022}, "your-256-bit-secret"), ({"sub": "anna", "exp": 100}, "k"),
              ({"role": "admin", "sub": "boss"}, "k2"), ({"sub": "Аня"}, "k"), ({}, "k")],
             [(SOL2.replace('separators=(",", ":")', 'separators=(",", ":"), sort_keys=True'), "Ключи отсортированы: порядок должен остаться как в словаре."),
              (SOL2.replace('"HS256"', '"none"'), "В заголовке должен быть алгоритм HS256."),
              (SOL2.replace('sign(header + "." + body, secret)', 'sign(body, secret)'), "Подписывается только содержимое: нужно «заголовок.содержимое»."),
              (SOL2.replace('header + "." + body + "." + sign', 'header + "." + body + sign'), "Между частями токена должны быть точки.")],
             hints("Токен — три строки через точку: заголовок, содержимое, подпись.", "Заголовок и содержимое — JSON, превращённый в байты и закодированный функцией b64.",
                   "json.dumps(...) возвращает строку, у неё есть метод encode(); аргумент separators=(\",\", \":\") убирает пробелы.", "Подпись считает готовая sign от строки «заголовок.содержимое».",
                   "header = b64(json.dumps({...}, separators=...).encode()); body = b64(json.dumps(payload, separators=...).encode()); return header + \".\" + body + \".\" + sign(header + \".\" + body, secret)"),
             "Токен HS256: base64url от заголовка и содержимого и подпись HMAC-SHA256 от их склейки через точку. Первый тест совпадает с общеизвестным примером jwt.io.",
             type="write", starter=STR2, goal="Собрать токен формата JWT.",
             criteria=["Заголовок HS256/JWT.", "Содержимое в компактном JSON.", "Подпись от заголовок.содержимое."])

# ---------- a3: current_user (fastapi) ----------
READ = HELP.split("import json\n\n\n", 1)[1]
PRE3 = ("import base64\nimport hashlib\nimport hmac\nimport json\nimport time\n\nfrom fastapi import Depends, FastAPI, Header, HTTPException\n\n"
        "SECRET = \"lesson-secret\"\n\n\n" + READ + "\n\napp = FastAPI()\n\n\n")
ROUTE3 = '\n\n@app.get("/me")\ndef me(user: dict = Depends(current_user)):\n    return {"user": user["sub"]}\n'
DEP3 = ('def current_user(authorization: str = Header(None)) -> dict:\n    if not authorization or not authorization.startswith("Bearer "):\n        raise HTTPException(status_code=401, detail="Нужен токен")\n'
        '    payload = read_token(authorization[7:], SECRET, int(time.time()))\n    if payload is None:\n        raise HTTPException(status_code=401, detail="Неверный токен")\n    return payload\n')
S3 = PRE3 + DEP3 + ROUTE3
START3 = PRE3 + "# Напишите зависимость current_user(authorization)\n" + ROUTE3


def bearer(t): return {"Authorization": "Bearer " + t}


t3 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/me", "expected_status": 401, "expected_json": {"detail": "Нужен токен"}, "hint": "Без заголовка Authorization — 401 и «Нужен токен»"},
    {"id": "v2", "path": "/me", "headers": bearer(T_OK), "expected_json": {"user": "anna"}},
    {"id": "h1", "hidden": True, "path": "/me", "headers": bearer("broken"), "expected_status": 401, "expected_json": {"detail": "Неверный токен"}},
    {"id": "h2", "hidden": True, "path": "/me", "headers": bearer(T_OLD), "expected_status": 401, "expected_json": {"detail": "Неверный токен"}, "hint": "Срок действия токена вышел"},
    {"id": "h3", "hidden": True, "path": "/me", "headers": {"Authorization": "Token " + T_OK}, "expected_status": 401, "expected_json": {"detail": "Нужен токен"}, "hint": "Заголовок должен начинаться со слова Bearer"},
    {"id": "h4", "hidden": True, "path": "/me", "headers": bearer(T_OTHER), "expected_status": 401, "expected_json": {"detail": "Неверный токен"}, "hint": "Токен подписан чужим ключом"},
]}
a3 = asg("a3-depends", "write", "Зависимость current_user",
         "Функция `read_token(token, secret, now)` уже есть: она возвращает данные токена или `None` (подпись неверна, токен просрочен). Напишите зависимость `current_user(authorization: str = Header(None))`: "
         "если заголовка нет или он не начинается с `Bearer ` — **401** и `{\"detail\": \"Нужен токен\"}`; иначе проверьте токен (`now` — `int(time.time())`); если `read_token` вернула `None` — **401** и `{\"detail\": \"Неверный токен\"}`; иначе верните данные токена. "
         "Маршрут `/me` уже использует её через `Depends`.",
         "Защищать маршрут зависимостью.", "Запросы с разными заголовками Authorization.", "401 без верного токена, имя пользователя — с верным.",
         ["Секретный ключ в учебном коде записан в тексте; в проекте — из переменной окружения."],
         hints("Зависимость — обычная функция; заголовок получают параметром authorization: str = Header(None).", "Сначала проверьте, что заголовок есть и начинается с «Bearer ».",
               "Токен — часть строки после «Bearer »: authorization[7:].", "Вызовите read_token(токен, SECRET, int(time.time())); None означает «токен плохой».",
               "Оба отказа — raise HTTPException(status_code=401, detail=…); при успехе верните payload."),
         t3, S3, "Зависимость собирает проверки в одном месте: любой маршрут с Depends(current_user) защищён одинаково. Нет заголовка и плохой токен — 401, но с разными сообщениями.",
         ["Нет заголовка → 401.", "Плохой/просроченный/чужой токен → 401.", "Верный токен → данные."],
         [(PRE3 + DEP3.replace('        raise HTTPException(status_code=401, detail="Неверный токен")\n    return payload', '        raise HTTPException(status_code=403, detail="Неверный токен")\n    return payload') + ROUTE3, "Плохой токен — это 401, а не 403."),
          (PRE3 + DEP3.replace("int(time.time())", "0") + ROUTE3, "Срок не проверяется: просроченный токен принимается (now = 0)."),
          (PRE3 + DEP3.replace('not authorization or not authorization.startswith("Bearer ")', 'not authorization') + ROUTE3, "Слово Bearer не проверяется: заголовок «Token …» не должен приниматься как «Bearer …».")],
         starter=START3)

# ---------- a4: fix — токен без проверки подписи ----------
BAD4 = (PRE3 + 'def current_user(authorization: str = Header(None)) -> dict:\n    if not authorization or not authorization.startswith("Bearer "):\n        raise HTTPException(status_code=401, detail="Нужен токен")\n'
        '    token = authorization[7:]\n    try:\n        payload = json.loads(unb64(token.split(".")[1]))\n    except Exception:\n        raise HTTPException(status_code=401, detail="Неверный токен")\n    return payload\n' + ROUTE3)
t4 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/me", "headers": bearer(T_OK), "expected_json": {"user": "anna"}},
    {"id": "v2", "path": "/me", "headers": bearer(T_FORGED), "expected_status": 401, "expected_json": {"detail": "Неверный токен"}, "hint": "Токен подписан чужим ключом, но содержимое читается: подпись не проверяется"},
    {"id": "h1", "hidden": True, "path": "/me", "headers": bearer(T_TAMPER), "expected_status": 401, "expected_json": {"detail": "Неверный токен"}, "hint": "Содержимое подменили, а подпись осталась старой"},
    {"id": "h2", "hidden": True, "path": "/me", "headers": bearer(T_OLD), "expected_status": 401, "expected_json": {"detail": "Неверный токен"}, "hint": "Срок действия вышел"},
    {"id": "h3", "hidden": True, "path": "/me", "headers": bearer("abc"), "expected_status": 401, "expected_json": {"detail": "Неверный токен"}},
    {"id": "h4", "hidden": True, "path": "/me", "expected_status": 401, "expected_json": {"detail": "Нужен токен"}},
]}
a4 = asg("a4-forged", "fix", "Подделанный токен",
         "Любой может выпустить себе токен администратора: зависимость `current_user` **читает** содержимое токена, но не проверяет подпись и срок. Исправьте её: проверяйте токен функцией `read_token(token, SECRET, int(time.time()))`; "
         "если она вернула `None` — **401** и `{\"detail\": \"Неверный токен\"}`.",
         "Не доверять непроверенному токену.", "Токены: верный, поддельный, с подменённым содержимым, просроченный.", "401 для всего, кроме верного токена.",
         ["Сообщения об ошибках не меняйте."],
         hints("Сейчас содержимое читается как есть: любой токен, похожий по форме, принимается.", "Подпись защищает содержимое только тогда, когда её проверяют.",
               "Проверку подписи и срока уже делает read_token.", "Если read_token вернула None — токен плохой.",
               "payload = read_token(token, SECRET, int(time.time())); if payload is None: raise HTTPException(401, …)."),
         t4, S3, "Содержимое токена читает кто угодно, и поэтому верить ему можно только после проверки подписи и срока. read_token возвращает данные лишь для верного и не просроченного токена.",
         ["Подпись проверяется.", "Срок проверяется.", "Поддельные токены → 401."],
         [(BAD4, "Ошибка осталась: подпись не проверяется."),
          (PRE3 + DEP3.replace("int(time.time())", "0") + ROUTE3, "Подпись проверяется, но срок нет (now = 0): просроченный токен проходит."),
          (PRE3 + DEP3.replace('status_code=401, detail="Неверный токен"', 'status_code=403, detail="Неверный токен"') + ROUTE3, "Плохой токен — 401, а не 403.")],
         starter=BAD4)

# ---------- a5: predict ----------
CODE5 = HELP + ('\n\nSECRET = "k1"\nt = make_token({"sub": "a", "exp": 10}, SECRET)\nprint(read_token(t, SECRET, 10) is not None)\nprint(read_token(t, SECRET, 11) is not None)\n'
                'parts = t.split(".")\nforged = parts[0] + "." + b64(b\'{"sub":"b","exp":10}\') + "." + parts[2]\nprint(read_token(forged, SECRET, 5))\nprint(hmac.compare_digest(b"abc", b"abc"))\n')
a5 = predict_task("a5-predict", "Проверка токена", CODE5,
                  [("True\nTrue\nNone\nTrue", "Срок: условие exp < now; при now = 11 токен с exp = 10 уже просрочен."),
                   ("True\nFalse\n{'sub': 'b', 'exp': 10}\nTrue", "Подпись остаётся старой, а содержимое подменено: подпись не сойдётся и read_token вернёт None.")],
                  hints("Начните с чтения сроков: токен просрочен, если exp меньше now.", "При now = 10 и exp = 10 условие exp < now ложно: токен ещё действует.",
                        "При now = 11: 10 < 11, токен просрочен — read_token вернёт None, а выражение is not None даст False.", "У подделанного токена подпись от другого содержимого.",
                        "Подпись не сойдётся: read_token вернёт None. Последняя строка — равные байты: True."),
                  "exp = 10 действует при now = 10 и просрочен при now = 11. У подделанного токена подмена содержимого ломает подпись, поэтому результат None.",
                  goal="Предсказать проверку подписи и срока.")

skills = {"api.password": "Хеш пароля с солью", "api.token": "Токен JWT (HS256)", "api.auth": "Защита маршрутов: Depends, 401 и 403"}
write_lesson("api-05-auth", "FastAPI: пароли, токены и защита маршрутов",
             "Хранить пароли хешем с солью, выпускать и проверять подписанный токен и защищать маршруты зависимостью, различая 401 и 403.",
             list(skills), ["api-04-middleware"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Пароль открытым текстом или быстрый хеш без соли", "fix": "Хешируйте медленной функцией (PBKDF2, argon2, bcrypt) с солью."},
              {"mistake": "Токен прочитан без проверки подписи", "fix": "Содержимое токена доверенно только после проверки подписи и срока: используйте read_token."},
              {"mistake": "Не проверен срок exp", "fix": "Сравнивайте exp с текущим временем: украденный токен не должен жить вечно."},
              {"mistake": "401 и 403 перепутаны", "fix": "401 — токена нет или он плохой; 403 — токен хороший, но прав недостаточно."}],
             min_pass=3, pack="api-basics", runner="A")
f = ROOT / "content/packs/api-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "api-05-auth" not in data["lessons"]:
    data["lessons"].append("api-05-auth")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

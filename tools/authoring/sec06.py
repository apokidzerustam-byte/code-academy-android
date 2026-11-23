from lib import *

URLS = '''from urllib.parse import urlsplit

for url in [
    "https://bank.example/login",
    "http://bank.example/login",
    "https://bank.example.evil.test/login",
]:
    parts = urlsplit(url)
    print(parts.scheme, parts.hostname)
'''

REDIR = '''from urllib.parse import urlsplit, urlunsplit


def https_redirect(url):
    parts = urlsplit(url)
    if parts.scheme == "https":
        return 200, None
    return 301, urlunsplit(parts._replace(scheme="https"))


print(https_redirect("http://shop.example/cart?id=5"))
print(https_redirect("https://shop.example/cart?id=5"))
'''

COOKIE = '''def make_cookie(name, value, max_age=3600, secure=True, http_only=True, same_site="Lax"):
    parts = [f"{name}={value}", "Path=/"]
    if max_age is not None:
        parts.append(f"Max-Age={max_age}")
    if secure:
        parts.append("Secure")
    if http_only:
        parts.append("HttpOnly")
    if same_site:
        parts.append(f"SameSite={same_site}")
    return "; ".join(parts)


'''
COOKIE_MAIN = '''print(make_cookie("sid", "abc123"))
print(make_cookie("theme", "dark", max_age=86400, http_only=False))
'''

HEADERS = '''REQUIRED = {
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "content-security-policy": "default-src 'self'",
    "referrer-policy": "no-referrer",
}


def missing_headers(headers):
    present = {name.lower() for name in headers}
    return [name for name in REQUIRED if name not in present]


'''
HEADERS_MAIN = '''response = {"Content-Type": "text/html", "X-Frame-Options": "DENY"}
print(missing_headers(response))
'''

MIXED = '''import re


def insecure_links(html):
    return re.findall(r'(?:src|href)="(http://[^"]+)"', html)


page = (
    '<img src="http://cdn.example/logo.png">'
    '<a href="https://ok.example/">ok</a>'
    '<script src="http://cdn.example/app.js"></script>'
)
print(insecure_links(page))
'''

begin()
scenes = [
 S("intro", "Что даёт HTTPS", """
  Обычный протокол HTTP передаёт всё открытым текстом. Пароль, который вы отправили в кафе по общему вайфаю, может прочитать любой, кто сидит в той же сети.
  HTTPS это тот же HTTP, но внутри защищённого соединения TLS. Оно даёт три гарантии. Первая: тайна, то есть посторонний видит только набор
  бессмысленных байтов. Вторая: целостность, то есть данные нельзя незаметно подменить по дороге. Третья: подлинность. Сертификат доказывает, что вы
  разговариваете именно с этим сайтом, а не с подделкой. Значок замка в браузере означает, что все три гарантии выполняются для адреса,
  который вы видите. Но он не означает, что сам сайт честный: мошенник тоже может получить сертификат на своё название. Поэтому защита сайта всегда состоит из нескольких слоёв:
  шифрованное соединение, правильные куки, заголовки безопасности и внимательность самого пользователя. Сегодня мы разберём каждый слой и
  научимся проверять его кодом.""",
  nt("**HTTPS** = HTTP + TLS: тайна · целостность · подлинность", at="HTTPS это тот же HTTP"),
  nt("Замок = соединение защищено. Он **не** значит «сайт честный»", at="Значок замка")),
 S("url", "Схема и настоящее имя сайта", """
  Первое, что нужно уметь, это правильно читать адрес. У адреса есть схема, то есть начало до двоеточия: http или https. Затем идёт имя сайта.
  Давайте разберём три адреса стандартной функцией. Первый защищён и принадлежит банку. Второй тот же сайт, но по незащищённой схеме,
  и в нём нельзя вводить пароль. А в третьем есть обман: слово bank example стоит в начале, но имя сайта заканчивается на evil test, значит, это совсем другой
  сайт. Смотреть нужно на имя перед первой косой чертой, а не на красивое начало. Этот приём пригодится и вам как разработчику: когда вы проверяете, куда ведёт
  адрес, например при перенаправлении после входа, всегда сверяйте полное имя сайта, а не только его начало. Иначе мошенник подставит свой сайт.""",
  clr(), t(URLS, at="Давайте разберём"), hl([4], at="Первый защищён"), hl([5], at="Второй тот же сайт"), hl([6], at="А в третьем"), run("Смотреть нужно")),
 S("redirect", "Переход на HTTPS и HSTS", """
  Сервер не должен отвечать на пароли по HTTP. Поэтому для незащищённых запросов он возвращает перенаправление: код триста один и новый адрес с
  защищённой схемой. Функция https redirect делает именно это: если схема уже https, всё хорошо, иначе заменяет её и сохраняет остальную часть
  адреса. Запустим на двух адресах. Но первый запрос всё равно уходит открытым, и этим может воспользоваться перехватчик. Поэтому сайт добавляет
  заголовок Strict Transport Security, сокращённо HSTS: он велит браузеру на год вперёд ходить на сайт только по HTTPS, даже если пользователь
  наберёт http. Тогда первый открытый запрос остаётся только при самом первом визите на сайт, а дальше
  перехватчику ловить нечего.""",
  clr(), t(REDIR, at="Функция https redirect"), hl([5, 6, 7, 8], at="Функция https redirect"), run("Запустим на двух"),
  nt("`Strict-Transport-Security: max-age=31536000; includeSubDomains` — «год ходи только по HTTPS»", at="заголовок Strict Transport Security")),
 S("cookies", "Куки: флаги безопасности", """
  Сервер запоминает вошедшего пользователя в куки, и эта кука стоит дороже пароля: кто её украл, тот и вошёл. Поэтому у неё есть защитные
  флаги. Secure: кука отправляется только по HTTPS. HttpOnly: скрипты на странице не могут её прочитать, а значит, украсть её через внедрённый код
  будет сложнее. SameSite: кука не отправляется со сторонних сайтов, и это защита от подделки запросов. И Max-Age: у куки ограниченный срок жизни.
  Функция make cookie собирает заголовок Set Cookie с такими флагами. Для сессии оставляем всё включённым. А безобидной настройке, вроде
  темы оформления, можно разрешить чтение скриптом: флаг HttpOnly отключён. Хорошее правило: давайте куке минимум возможностей. Если скрипту читать её не
  нужно, пусть не читает. Если она нужна только на вашем сайте, пусть не уходит на чужие. Лишние возможности это лишняя поверхность для
  атаки.""",
  clr(), t(COOKIE, at="Поэтому у неё"), hl([5, 6], at="Secure: кука"), hl([7, 8], at="HttpOnly: скрипты"), hl([9, 10], at="SameSite: кука"), hl([3, 4], at="И Max-Age"),
  t(COOKIE_MAIN, at="Для сессии оставляем"), run("А безобидной")),
 S("headers", "Заголовки безопасности", """
  Ещё один слой защиты, заголовки ответа. Они говорят браузеру, как себя вести. X Content Type Options со значением nosniff запрещает
  браузеру угадывать тип файла. X Frame Options запрещает показывать сайт внутри чужой страницы, и это защита от обмана кликами. Политика
  Content Security Policy задаёт, откуда страница может загружать скрипты: значение default src self разрешает только свой сайт. А Referrer Policy
  решает, сколько информации об адресе отправлять другим сайтам. Проверка очень простая: сравниваем нужные заголовки с теми, что вернул сервер. Имена
  заголовков нечувствительны к регистру, поэтому приводим их к нижнему. Здесь не хватает четырёх из пяти. Для начала включите
  хотя бы эти заголовки: они ничего не ломают в обычном сайте, а закрывают целые классы атак. Политику Content Security Policy вводят осторожно:
  сначала в режиме наблюдения, чтобы не заблокировать собственные скрипты.""",
  clr(), t(HEADERS, at="Ещё один слой"), hl([3], at="X Content Type Options"), hl([4], at="X Frame Options"), hl([5], at="Content Security Policy"), hl([6], at="Referrer Policy"),
  t(HEADERS_MAIN, at="Проверка очень простая"), run("Здесь не хватает")),
 S("mixed", "Смешанное содержимое", """
  Последняя ловушка: страница загружена по HTTPS, но подтягивает картинку или скрипт по обычному HTTP. Это называется смешанным содержимым. Скрипт
  по открытому каналу злоумышленник может подменить, и вся защита страницы превращается в видимость. Браузеры такое блокируют, но лучше
  не допускать. Найти такие ссылки можно регулярным выражением: ищем атрибуты src или href, значение которых начинается с http двоеточие две косые черты.
  Ссылка на https пропускается, а картинка и скрипт попадают в список. Такую проверку полезно запускать перед выпуском сайта: найденные
  адреса остаётся заменить на https, и страница станет полностью защищённой.""",
  clr(), t(MIXED, at="Найти такие ссылки"), hl([5], at="ищем атрибуты"), run("Ссылка на https")),
 S("mistakes", "Типичные ошибки", """
  Четыре типичные ошибки. Первая: считать замок гарантией честности сайта. Вторая: сессионная кука без флагов Secure и HttpOnly. Третья: включить HTTPS
  и забыть про перенаправление и HSTS, так что открытый вход остаётся. Четвёртая: подключать скрипты и картинки по HTTP на защищённой странице.""",
  nt("Ошибка 1: замок = «сайт честный».", at="Первая"), nt("Ошибка 2: сессионная кука без `Secure` и `HttpOnly`.", at="Вторая"),
  nt("Ошибка 3: нет перенаправления и HSTS.", at="Третья"), nt("Ошибка 4: ресурсы по HTTP на HTTPS-странице.", at="Четвёртая")),
 S("summary", "Итог", """
  Подведём итог. HTTPS даёт тайну, целостность и подлинность. Читайте адрес целиком: важно имя сайта, а не красивое начало. Сервер перенаправляет на
  HTTPS и включает HSTS. Сессионной куке нужны флаги Secure, HttpOnly и SameSite. Заголовки безопасности запрещают браузеру опасные догадки. Ресурсы
  на защищённой странице тоже загружаются по HTTPS. В заданиях вы предскажете перенаправление, проверите куку, исправите сборку куки, найдёте слабые
  заголовки и найдёте небезопасные ресурсы. Критерий прохождения: решить не меньше четырёх заданий из пяти.""",
  nt("HTTPS · редирект + HSTS · куки `Secure`/`HttpOnly`/`SameSite` · заголовки · без HTTP-ресурсов", at="Подведём итог")),
]

notes = """
# HTTPS, куки и заголовки безопасности

## HTTPS

HTTPS = HTTP + TLS: **тайна** (посторонний не прочитает), **целостность** (не подменит), **подлинность** (сертификат доказывает, что это именно тот сайт). Замок не означает, что сайт честный.

Смотрите на **имя сайта** (до первой `/`), а не на красивое начало: `bank.example.evil.test` — другой сайт.

## Перенаправление и HSTS

Сервер отвечает на HTTP кодом `301` с адресом по HTTPS и добавляет `Strict-Transport-Security: max-age=31536000; includeSubDomains`.

## Куки

| Флаг | Что делает |
|---|---|
| `Secure` | отправляется только по HTTPS |
| `HttpOnly` | недоступна скриптам страницы |
| `SameSite=Lax/Strict` | не отправляется со сторонних сайтов |
| `Max-Age` | ограничивает срок жизни |

```py
"sid=abc123; Path=/; Max-Age=3600; Secure; HttpOnly; SameSite=Lax"
```

## Заголовки безопасности

| Заголовок | Значение |
|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` или `SAMEORIGIN` |
| `Content-Security-Policy` | например `default-src 'self'` |
| `Referrer-Policy` | например `no-referrer` |

Имена заголовков нечувствительны к регистру. В FastAPI такие заголовки добавляют слоем middleware (урок про middleware).

## Смешанное содержимое

Страница по HTTPS не должна загружать скрипты и картинки по `http://`.
"""

A1_CODE = ('from urllib.parse import urlsplit, urlunsplit\n\n\ndef https_redirect(url):\n    parts = urlsplit(url)\n    if parts.scheme == "https":\n        return 200, None\n    return 301, urlunsplit(parts._replace(scheme="https"))\n\n\n'
           'for url in ["http://a.com/x?y=1#top", "https://a.com/x", "HTTP://A.com/x", "ftp://a.com/f"]:\n    print(https_redirect(url))\n')
a1 = predict_task("a1-redirect", "Перенаправление на HTTPS", A1_CODE,
  [("(301, 'https://a.com/x?y=1#top')\n(200, None)\n(301, 'https://a.com/x')\n(200, None)", "Имя сайта сохраняет регистр: A.com не меняется на a.com; а ftp не равно https, поэтому тоже перенаправляется."),
   ("(301, 'https://a.com/x?y=1')\n(200, None)\n(301, 'https://A.com/x')\n(301, 'https://a.com/f')", "Фрагмент после решётки не теряется: urlunsplit возвращает его на место.")],
  hints("Функция меняет только схему: адрес после неё остаётся прежним.", "Запрос после вопросительного знака и фрагмент после решётки сохраняются.", "urlsplit приводит схему к нижнему регистру: HTTP даёт http, но имя сайта остаётся как есть.",
        "Схема https даёт (200, None) без перенаправления.", "Любая другая схема, в том числе ftp, считается небезопасной и тоже заменяется на https."),
  "Функция заменяет схему на https для любой схемы, кроме https, и сохраняет остальные части адреса, в том числе регистр имени сайта, запрос и фрагмент.")

AC_SOL = ('def audit_cookie(header):\n    attrs = [part.strip().lower() for part in header.split(";")[1:]]\n    problems = []\n    if "secure" not in attrs:\n        problems.append("нет Secure")\n'
          '    if "httponly" not in attrs:\n        problems.append("нет HttpOnly")\n    same_site = [a for a in attrs if a.startswith("samesite=")]\n'
          '    if not same_site:\n        problems.append("нет SameSite")\n    elif same_site[0] == "samesite=none" and "secure" not in attrs:\n        problems.append("SameSite=None без Secure")\n    return problems\n')
AC_START = 'def audit_cookie(header):\n    # Верните список проблем: "нет Secure", "нет HttpOnly", "нет SameSite", "SameSite=None без Secure" (в этом порядке)\n    pass\n'
a2 = fn_task("a2-audit-cookie", "Проверка куки",
  "Напишите `audit_cookie(header)`: принимает строку заголовка `Set-Cookie` и возвращает список проблем (в этом порядке): `\"нет Secure\"`, `\"нет HttpOnly\"`, `\"нет SameSite\"`, "
  "`\"SameSite=None без Secure\"` (последняя — когда `SameSite=None`, а `Secure` нет). Имена флагов нечувствительны к регистру. Первая часть заголовка (`имя=значение`) флагом не считается.",
  "audit_cookie", AC_SOL,
  [["sid=abc; Path=/; Secure; HttpOnly; SameSite=Lax"], ["sid=abc; Path=/"], (["sid=abc; secure; httponly; samesite=strict"], True), (["sid=abc; HttpOnly; SameSite=None"], True),
   (["sid=abc; Secure; SameSite=None"], True), (["samesite=1; Secure; HttpOnly"], True), (["sid=abc; Path=/; Max-Age=60; Secure; HttpOnly"], True)],
  [(AC_SOL.replace('.strip().lower()', '.strip()'), "Флаги проверяются с учётом регистра: secure не распознаётся как Secure."),
   (AC_SOL.replace('same_site = [a for a in attrs if a.startswith("samesite=")]', 'same_site = [p.strip().lower() for p in header.split(";") if p.strip().lower().startswith("samesite=")]'), "Первая часть «имя=значение» тоже считается флагом: кука с именем samesite ошибочно проходит проверку."),
   (AC_SOL.replace('    elif same_site[0] == "samesite=none" and "secure" not in attrs:\n        problems.append("SameSite=None без Secure")\n', ''), "Не проверено сочетание SameSite=None без Secure.")],
  hints("Заголовок делят по точке с запятой: первая часть — имя и значение, остальные — флаги.", "Флаги удобно привести к нижнему регистру и убрать пробелы.", "Secure и HttpOnly — флаги без значения: проверьте, есть ли они в списке.",
        "SameSite имеет вид samesite=значение: ищите флаг, который с этого начинается.", "SameSite=None без Secure браузеры отвергают: проверьте это отдельно, когда SameSite есть."),
  "Проверка куки разбирает заголовок на части и ищет нужные флаги. Имя куки не должно путаться с флагами, а сочетание SameSite=None без Secure небезопасно.",
  type="write", starter=AC_START, goal="Найти слабые места куки.", criteria=["Флаги ищутся без учёта регистра.", "Имя куки не считается флагом.", "Проверено SameSite=None."])

MC_START = ('def make_cookie(name, value, max_age=3600, secure=True, http_only=True, same_site="Lax"):\n    parts = [f"{name}={value}", "Path=/", f"Max-Age={max_age}"]\n    if not secure:\n        parts.append("Secure")\n'
            '    if not http_only:\n        parts.append("HttpOnly")\n    if same_site:\n        parts.append(f"SameSite={same_site}")\n    return "; ".join(parts)\n')
MC_SOL = ('def make_cookie(name, value, max_age=3600, secure=True, http_only=True, same_site="Lax"):\n    parts = [f"{name}={value}", "Path=/"]\n    if max_age is not None:\n        parts.append(f"Max-Age={max_age}")\n'
          '    if secure:\n        parts.append("Secure")\n    if http_only:\n        parts.append("HttpOnly")\n    if same_site:\n        parts.append(f"SameSite={same_site}")\n    return "; ".join(parts)\n')
a3 = fn_task("a3-make-cookie", "Куки с флагами наоборот",
  "Функция `make_cookie` собирает заголовок `Set-Cookie`, но флаги работают **наоборот**: `Secure` и `HttpOnly` добавляются, когда их просили отключить. Кроме того, при `max_age=None` (сессионная кука) в заголовке не должно быть `Max-Age`. Исправьте функцию.",
  "make_cookie", MC_SOL,
  [["sid", "abc"], ["theme", "dark", 86400, True, False], (["tmp", "1", None], True), (["a", "b", 60, False, False, None], True), (["s", "x", 0, True, True, "Strict"], True)],
  [(MC_START, "Исходная функция: флаги инвертированы, при None печатается «Max-Age=None»."),
   (MC_START.replace("if not secure", "if secure").replace("if not http_only", "if http_only"), "Флаги исправлены, но при max_age=None в заголовке остаётся «Max-Age=None»."),
   (MC_SOL.replace("    if max_age is not None:\n        parts.append(f\"Max-Age={max_age}\")\n", "    parts.append(f\"Max-Age={max_age}\")\n"), "При max_age=None в заголовке не должно быть Max-Age.")],
  hints("Запустите функцию с разными параметрами и сравните заголовок с ожидаемым.", "Флаг Secure добавляется, когда secure истинно, а не наоборот.", "То же с HttpOnly: он нужен, когда http_only истинно.",
        "Max-Age добавляется только если max_age не None.", "Условие для Max-Age: if max_age is not None."),
  "Флаги безопасности включаются по запросу, а не по обратному условию. Отсутствие max_age означает сессионную куку без Max-Age: добавлять «Max-Age=None» нельзя.",
  type="fix", starter=MC_START, goal="Исправить сборку куки.", criteria=["Secure и HttpOnly по запросу.", "Max-Age только если задан."])

WH_SOL = ('def weak_headers(headers):\n    h = {name.lower(): value.strip().lower() for name, value in headers.items()}\n    weak = []\n    hsts = h.get("strict-transport-security")\n    max_age = 0\n'
          '    if hsts:\n        for part in hsts.split(";"):\n            part = part.strip()\n            if part.startswith("max-age="):\n                value = part[len("max-age="):]\n                max_age = int(value) if value.isdigit() else 0\n'
          '    if max_age < 31536000:\n        weak.append("strict-transport-security")\n    if h.get("x-content-type-options") != "nosniff":\n        weak.append("x-content-type-options")\n'
          '    if h.get("x-frame-options") not in ("deny", "sameorigin"):\n        weak.append("x-frame-options")\n    return weak\n')
WH_START = 'def weak_headers(headers):\n    # Верните список слабых или отсутствующих заголовков (в нижнем регистре, в порядке из условия)\n    pass\n'
GOOD = {"Strict-Transport-Security": "max-age=31536000; includeSubDomains", "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY"}
a4 = fn_task("a4-weak-headers", "Слабые заголовки",
  "Напишите `weak_headers(headers)`: принимает словарь заголовков ответа и возвращает список **слабых или отсутствующих** (в нижнем регистре, в этом порядке): "
  "`strict-transport-security` (нужен `max-age` не меньше 31536000), `x-content-type-options` (должен быть `nosniff`), `x-frame-options` (`DENY` или `SAMEORIGIN`). Имена и значения сравниваются без учёта регистра.",
  "weak_headers", WH_SOL,
  [[GOOD], [{}], ([{**GOOD, "Strict-Transport-Security": "max-age=600"}], True), ([{"x-frame-options": "sameorigin", "X-CONTENT-TYPE-OPTIONS": "NoSniff", "strict-transport-security": "includeSubDomains; max-age=63072000"}], True),
   ([{**GOOD, "X-Frame-Options": "ALLOWALL"}], True), ([{**GOOD, "X-Content-Type-Options": "sniff"}], True), ([{**GOOD, "Strict-Transport-Security": "max-age=abc"}], True), ([{"Strict-Transport-Security": "max-age=31536000"}], True)],
  [(WH_SOL.replace("name.lower(): value.strip().lower()", "name: value.strip().lower()"), "Имена сравниваются с учётом регистра."),
   (WH_SOL.replace("    if max_age < 31536000:", "    if not hsts:"), "Слишком короткий max-age тоже слабая настройка."),
   (WH_SOL.replace('not in ("deny", "sameorigin")', 'not in ("deny",)'), "SAMEORIGIN допустим."),
   (WH_SOL.replace('h.get("x-content-type-options") != "nosniff"', '"x-content-type-options" not in h'), "Значение должно быть именно nosniff.")],
  hints("Сначала приведите имена и значения к нижнему регистру: так проще сравнивать.", "Для nosniff достаточно сравнить значение со строкой.", "X-Frame-Options допускает два значения: deny и sameorigin.",
        "В HSTS нужно найти часть max-age=число: разделите значение по точке с запятой.", "Число переведите в int; если max-age нет или он меньше 31536000, заголовок слабый."),
  "Мало просто иметь заголовок: значение должно быть защитным. Имена нечувствительны к регистру, а у HSTS важен срок max-age.",
  type="write", starter=WH_START, goal="Найти слабые заголовки безопасности.", criteria=["Имена без учёта регистра.", "Проверены значения.", "Срок HSTS не меньше года."])

IR_PAT = r"""src\s*=\s*["'](http://[^"']+)["']"""


def ir_code(pat=IR_PAT, flags=", re.IGNORECASE"):
    head = "import re\n\n\ndef insecure_resources(html):\n    return re.findall(r'''"
    return head + pat + "''', html" + flags + ")\n"


IR_SOL = ir_code()
IR_START = 'import re\n\n\ndef insecure_resources(html):\n    # Верните список адресов из src, которые начинаются с http://\n    pass\n'
IR_HTML1 = '<img src="http://a.example/x.png"><script src="https://b.example/app.js"></script><iframe src="http://c.example/f"></iframe>'
IR_HTML2 = "<IMG SRC='http://d.example/y.png'> <a href=\"http://e.example/\">link</a> <img src = \"http://f.example/z.png\">"
a5 = fn_task("a5-insecure-resources", "Небезопасные ресурсы",
  "Напишите `insecure_resources(html)`: верните список адресов из атрибутов **`src`** (картинки, скрипты, фреймы), которые начинаются с `http://`, в порядке появления. "
  "Учтите: кавычки бывают двойные и одинарные, имя атрибута — в любом регистре, вокруг `=` могут быть пробелы. Ссылки `href` на другие страницы смешанным содержимым не считаются.",
  "insecure_resources", IR_SOL,
  [[IR_HTML1], [IR_HTML2], (["<p>без ресурсов</p>"], True), (["<img src=\"https://ok.example/a.png\">"], True), (["<script src='http://x.example/a.js'></script><img src=\"/local.png\">"], True)],
  [(ir_code(r"""src\s*=\s*"(http://[^"]+)\""""), "Одинарные кавычки не учтены."),
   (ir_code(flags=""), "Имя атрибута в верхнем регистре (SRC) не найдено."),
   (ir_code(IR_PAT.replace("src", "(?:src|href)", 1)), "Ссылки href не считаются смешанным содержимым."),
   (ir_code(IR_PAT.replace("\\s*=\\s*", "=")), "Пробелы вокруг знака равенства не учтены.")],
  hints("Подойдёт регулярное выражение: re.findall.", "Ищем слово src, затем знак равенства, возможно с пробелами: \\s*=\\s*.", "Значение в кавычках: двойных или одинарных — [\"'].",
        "Само значение начинается с http:// и тянется до закрывающей кавычки: [^\"']+ .", "Регистр: добавьте флаг re.IGNORECASE; адрес оберните в скобки, чтобы findall вернул только его."),
  "Регулярное выражение должно допускать реальные вариации разметки: регистр, пробелы и оба вида кавычек. Скобки выделяют нужную часть, поэтому findall возвращает адреса.",
  type="write", starter=IR_START, goal="Найти ресурсы, загружаемые по HTTP.", criteria=["Учтены оба вида кавычек.", "Регистр и пробелы не важны.", "href не считается."])

mistakes = [
 {"mistake": "Замок в браузере принимают за гарантию честности сайта", "fix": "Замок защищает канал; читайте имя сайта и проверяйте, тот ли это сайт."},
 {"mistake": "Сессионная кука без Secure и HttpOnly", "fix": "Включайте Secure, HttpOnly и SameSite для сессионных кук."},
 {"mistake": "HTTPS есть, но нет перенаправления и HSTS", "fix": "Перенаправляйте с HTTP и включайте Strict-Transport-Security."},
 {"mistake": "Скрипты и картинки по HTTP на HTTPS-странице", "fix": "Все ресурсы загружайте по HTTPS."}]

finish("sec-06-https-headers", "HTTPS, куки и заголовки безопасности", "Понимать, что даёт HTTPS, и настраивать защитные флаги куки, заголовки ответа и перенаправление на защищённое соединение.",
  {"sec.https": "HTTPS и перенаправление", "sec.cookie-flags": "Флаги безопасности куки", "sec.headers": "Заголовки безопасности"},
  ["sec-05-secrets-csrf"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="security-lab", min_pass=4)

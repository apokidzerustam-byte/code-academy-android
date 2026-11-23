from lib import *

begin()
scenes = [
 S("intro", "Секреты и подделка запросов", """
  В этом уроке две темы. Первая — секреты: ключи доступа к сервисам, пароли от баз данных, токены. Если такой ключ попал в
  открытый репозиторий, им могут воспользоваться посторонние, и счёт за чужие запросы придёт вам. Вторая тема — CSRF,
  подделка межсайтового запроса: когда вредоносная страница заставляет ваш браузер отправить запрос на сайт, где вы уже
  вошли. Обе угрозы закрываются простыми и проверенными приёмами.""",
  nt("Секреты — **вне кода**, в переменных окружения · CSRF — защита токеном", at="Вторая тема")),
 S("env", "Переменные окружения", """
  Секрет не должен жить в исходном коде. Его передают программе снаружи, через переменные окружения операционной системы.
  В Python они доступны через os.environ. Для демонстрации мы запишем значение сами, а программа его прочитает. Метод get
  возвращает значение по умолчанию, если переменной нет, а обращение через квадратные скобки вызовет KeyError. Для
  обязательных секретов лучше упасть сразу при запуске, чем работать без ключа.""",
  clr(), t('import os\n\nos.environ["DEMO_API_KEY"] = "key-12345"\n\n', at="Для демонстрации"),
  t('print(os.environ.get("DEMO_API_KEY"))\nprint(os.environ.get("MISSING_KEY", "по умолчанию"))\ntry:\n    os.environ["MISSING_KEY"]\nexcept KeyError as e:\n    print("нет переменной", e)\n', at="Метод get"), run("Для обязательных")),
 S("repo", "Секреты и репозиторий", """
  Файл с локальными настройками, обычно называемый dot env, добавляют в gitignore, как мы делали в курсе по Git. А в
  репозитории хранят только файл-образец без настоящих значений. Если секрет всё же попал в коммит, удаление файла не
  спасает: он остался в истории. Ключ нужно считать скомпрометированным и немедленно заменить на новый у поставщика
  сервиса. И ещё одно правило: не печатайте секреты в журнал целиком, показывайте только маску.""",
  clr(), t('def mask(secret):\n    if len(secret) <= 4:\n        return "*" * len(secret)\n    return "*" * (len(secret) - 4) + secret[-4:]\n\n\n', at="не печатайте"),
  t('print(mask("key-12345"))\nprint(mask("abc"))\n', at="не печатайте"), run("не печатайте")),
 S("csrf", "Подделка запроса", """
  Представьте, что вы вошли на сайт банка, и браузер хранит сессионную куку. Вы открываете другую страницу, на ней скрытая форма
  отправляет перевод на сайт банка. Браузер сам приложит куку, и банк решит, что запрос ваш. Защита — токен: сервер
  выдаёт форме уникальное значение, которое злоумышленник угадать не может, и требует его в каждом запросе, меняющем данные.
  Токен можно вычислять от идентификатора сессии и серверного секрета с помощью HMAC.""",
  nt("Запрос, меняющий данные, должен содержать **токен**, который чужая страница не знает", at="Защита")),
 S("token", "Токен на HMAC", """
  Реализуем это на нескольких строках. Токен — HMAC-хеш от идентификатора сессии с серверным секретом. Проверка
  пересчитывает токен и сравнивает его функцией compare_digest. Токен из другой сессии или подделанный не пройдёт. Чужая страница
  не знает ни секрета, ни связанного с сессией значения, поэтому не может создать верный токен.""",
  clr(), t('import hashlib\nimport hmac\n\nSECRET = b"server-secret"\n\n\ndef make_token(session_id):\n    return hmac.new(SECRET, session_id.encode(), hashlib.sha256).hexdigest()\n\n\ndef check_token(session_id, token):\n    return hmac.compare_digest(make_token(session_id), token)\n\n\n', at="Реализуем"),
  t('token = make_token("session-1")\nprint(len(token))\nprint(check_token("session-1", token))\nprint(check_token("session-2", token))\nprint(check_token("session-1", "forged"))\n', at="Токен из другой"), run("Чужая страница")),
 S("summary", "Итог", """
  Подведём итог. Секреты хранят вне кода: в переменных окружения, а файлы с ними исключают из репозитория. Утёкший секрет
  заменяют. В журналах показывают только маски. От CSRF защищают токены, привязанные к сессии и проверяемые на каждом
  изменяющем запросе, а также атрибут SameSite у кук. Так мы завершаем знакомство с основами безопасной разработки.""",
  nt("секреты → окружение, не репозиторий · утёк → замени · CSRF → токен + `SameSite`", at="Подведём итог")),
]

notes = """
# Секреты и CSRF

```python
import os

def get_key():
    key = os.environ.get("API_KEY")
    if not key:
        raise KeyError("нужна переменная API_KEY")
    return key
```

## Секреты

1. Вне кода: переменные окружения или файл `.env` (в `.gitignore`).
2. В репозитории — только образец без значений.
3. Утёк — замените ключ, удаление из истории не гарантирует безопасность.
4. В журналах — маски: `*****2345`.

## CSRF-токен

```python
import hashlib, hmac

SECRET = b"server-secret"

def make_token(session_id):
    return hmac.new(SECRET, session_id.encode(), hashlib.sha256).hexdigest()

def check_token(session_id, token):
    return hmac.compare_digest(make_token(session_id), token)
```

Дополнительно: `SameSite` у кук, проверка токена на каждом запросе, меняющем данные.
"""

a1 = predict_task("a1-env", "Читаем окружение",
  'import os\n\nenv = {"PORT": "8080", "DEBUG": ""}\nprint(env.get("PORT", "80"))\nprint(env.get("HOST", "localhost"))\nprint(env.get("DEBUG", "off") or "off")\ntry:\n    env["TOKEN"]\nexcept KeyError as e:\n    print("нет", e)\n',
  [("80\nlocalhost\noff\nнет 'TOKEN'", "PORT задан, поэтому значение по умолчанию не используется."), ("8080\nlocalhost\n\nнет 'TOKEN'", "Пустая строка ложна, и `or` подставит «off».")],
  hints("get возвращает значение по умолчанию только если ключа нет.", "PORT есть: 8080.", "HOST нет: localhost.", "DEBUG есть, но пустой: пустая строка ложна, поэтому `or` даёт «off».", "env[\"TOKEN\"] вызывает KeyError: сообщение — имя ключа в кавычках."),
  "get подставляет умолчание лишь для отсутствующего ключа; пустая строка — значение, но в `or` она ложна.")

a2 = fn_task("a2-require", "Обязательная настройка",
  "Напишите `require(env, name)`: `env` — словарь переменных. Если `name` есть и значение не пустое — верните его. Иначе возбудите `KeyError` с текстом `нужна переменная NAME`.",
  "require", "def require(env, name):\n    value = env.get(name)\n    if not value:\n        raise KeyError(f\"нужна переменная {name}\")\n    return value\n",
  [[{"API_KEY": "abc"}, "API_KEY"], {"args": [{}, "API_KEY"], "expected_error": "KeyError"}, ([{"A": "1", "B": "2"}, "B"], True), {"args": [{"A": ""}, "A"], "expected_error": "KeyError", "hidden": True}],
  [("def require(env, name):\n    return env[name]\n", "Пустое значение принимается."),
   ("def require(env, name):\n    return env.get(name, \"\")\n", "Отсутствие переменной не вызывает ошибку.")],
  hints("Получите значение по имени без исключения.", "Метод get вернёт None, если ключа нет.", "Пустое значение тоже считается отсутствием.", "Проверка: if not value.", "Исключение: raise KeyError с понятным текстом."),
  "Обязательный секрет лучше потребовать при старте: ошибка сразу покажет, чего не хватает.")

a3 = fn_task("a3-mask", "Маска секрета",
  "Напишите `mask(secret)`: верните строку той же длины, где все символы, кроме **последних четырёх**, заменены на `*`. Если длина не больше 4 — все символы `*`.",
  "mask", "def mask(secret):\n    if len(secret) <= 4:\n        return \"*\" * len(secret)\n    return \"*\" * (len(secret) - 4) + secret[-4:]\n",
  [["key-12345"], ["abc"], (["abcd"], True), (["abcde"], True), ([""], True), (["token-secret-0001"], True)],
  [("def mask(secret):\n    return \"*\" * (len(secret) - 4) + secret[-4:]\n", "Короткие секреты показываются целиком."),
   ("def mask(secret):\n    return \"*\" * len(secret)\n", "Последние четыре символа тоже скрыты.")],
  hints("Покажите только хвост строки.", "Хвост: последние четыре символа — срез с отрицательным индексом.", "Остальное — звёздочки: умножение строки на число.", "Для коротких секретов показывать нечего.", "Длина не больше 4 — вернуть звёздочки по длине."),
  "Маска помогает находить нужный ключ в журнале, не раскрывая его. Короткие значения скрываются полностью.")

a4 = fn_task("a4-csrf-make", "Выдать CSRF-токен",
  "Напишите `make_token(session_id, secret)`: верните `hmac.new(secret.encode(), session_id.encode(), hashlib.sha256).hexdigest()`.",
  "make_token", "import hashlib\nimport hmac\n\n\ndef make_token(session_id, secret):\n    return hmac.new(secret.encode(), session_id.encode(), hashlib.sha256).hexdigest()\n",
  [["session-1", "s3cret"], ["session-2", "s3cret"], (["session-1", "other"], True), (["", "k"], True), (["сессия", "секрет"], True)],
  [("import hashlib\n\n\ndef make_token(session_id, secret):\n    return hashlib.sha256((session_id + secret).encode()).hexdigest()\n", "Не HMAC: другая конструкция."),
   ("import hashlib\nimport hmac\n\n\ndef make_token(session_id, secret):\n    return hmac.new(secret.encode(), session_id.encode(), hashlib.md5).hexdigest()\n", "Другой алгоритм хеширования.")],
  hints("Токен получается из идентификатора сессии и секрета.", "Для этого служит модуль hmac.", "hmac.new принимает ключ, сообщение и алгоритм.", "Ключ — секрет, сообщение — идентификатор сессии, оба в байтах.", "Результат — hexdigest()."),
  "HMAC связывает токен с секретом сервера: без секрета подделать токен нельзя.")

a5 = fn_task("a5-csrf-check", "Проверить токен",
  "Напишите `check_token(session_id, secret, token)`: пересчитайте токен как в предыдущем задании (`hmac`, `sha256`, hex) и сравните с `token` через `hmac.compare_digest`. Верните `True` или `False`.",
  "check_token", "import hashlib\nimport hmac\n\n\ndef check_token(session_id, secret, token):\n    expected = hmac.new(secret.encode(), session_id.encode(), hashlib.sha256).hexdigest()\n    return hmac.compare_digest(expected, token)\n",
  [["s1", "k", __import__("hmac").new(b"k", b"s1", "sha256").hexdigest()], ["s1", "k", __import__("hmac").new(b"k", b"s2", "sha256").hexdigest()], (["s1", "other", __import__("hmac").new(b"k", b"s1", "sha256").hexdigest()], True), (["s1", "k", ""], True), (["s1", "k", "x" * 64], True)],
  [("def check_token(session_id, secret, token):\n    return bool(token)\n", "Любой непустой токен принимается."),
   ("def check_token(session_id, secret, token):\n    return len(token) == 64\n", "Проверяется только длина.")],
  hints("Пересчитайте ожидаемый токен.", "Используйте ту же схему, что при выдаче.", "Получите hex-строку.", "Сравните её с полученным токеном.", "Сравнение — hmac.compare_digest."),
  "Проверка не доверяет присланному токену: сервер сам вычисляет ожидаемое значение и сравнивает.")

mistakes = [
 {"mistake": "Записывают ключ прямо в код", "fix": "Берите секреты из окружения и добавьте файл с ними в .gitignore."},
 {"mistake": "Удаляют утёкший ключ из файла и считают проблему решённой", "fix": "Ключ остаётся в истории: замените его у поставщика."},
 {"mistake": "Печатают секреты в журнал", "fix": "Показывайте маску."},
 {"mistake": "Проверяют CSRF-токен только на форме входа", "fix": "Токен нужен на каждом запросе, меняющем данные."}]

finish("sec-05-secrets-csrf", "Секреты и CSRF", "Хранить секреты вне кода и защищать запросы CSRF-токенами.",
  {"sec.secrets": "Секреты и окружение", "sec.csrf": "CSRF", "sec.hmac": "HMAC-токены"},
  ["sec-04-xss"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="security-lab")

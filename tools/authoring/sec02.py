from lib import *

begin()
scenes = [
 S("intro", "Как хранить пароли", """
  Пароли пользователей — самое ценное, что есть в базе. Если хранить их как есть, любая утечка базы выдаёт все пароли сразу,
  а люди часто используют один и тот же пароль на нескольких сайтах. Поэтому правило одно: пароль не хранят. Хранят его
  хеш — результат специальной необратимой функции. При входе хеш считают заново от введённого пароля и сравнивают с
  сохранённым. Исходный пароль при этом никогда не нужен.""",
  nt("Не хранить пароль, а хранить **хеш** · сравнивать хеши, а не пароли", at="Поэтому правило")),
 S("hash", "Что такое хеш", """
  Хеш-функция превращает любые данные в строку фиксированной длины. У неё три важных свойства. Одинаковый вход всегда даёт
  одинаковый результат. Малейшее изменение входа полностью меняет результат. И по результату нельзя восстановить вход. В
  модуле hashlib есть алгоритм sha256: его результат — шестьдесят четыре шестнадцатеричных символа. Посмотрим, как
  меняется хеш от одной буквы.""",
  clr(), t('import hashlib\n\n\ndef sha(text):\n    return hashlib.sha256(text.encode()).hexdigest()\n\n\n', at="В модуле"),
  t('print(len(sha("пароль")))\nprint(sha("пароль") == sha("пароль"))\nprint(sha("пароль") == sha("Пароль"))\n', at="Посмотрим"), run("Посмотрим")),
 S("salt", "Соль", """
  Но у обычного хеша есть слабое место. Если двое выбрали один пароль, их хеши совпадают, и злоумышленник с готовой таблицей
  популярных паролей быстро найдёт совпадения. Помогает соль — случайная строка, уникальная для каждого пользователя,
  которая добавляется к паролю перед хешированием. Соль не секретна, её хранят рядом с хешем. Теперь одинаковые пароли
  дают разные хеши.""",
  clr(), t('import hashlib\n\n\ndef sha(text):\n    return hashlib.sha256(text.encode()).hexdigest()\n\n\n', at="Но у"),
  t('print(sha("qwerty") == sha("qwerty"))\nprint(sha("соль-анны" + "qwerty") == sha("соль-бориса" + "qwerty"))\n', at="Теперь"), run("Теперь")),
 S("pbkdf2", "Медленный хеш", """
  Обычный sha256 слишком быстр: можно перебирать миллиарды паролей в секунду. Для паролей специально создают медленные
  функции. В стандартной библиотеке есть pbkdf2_hmac. Она принимает алгоритм, пароль, соль и число повторений: чем больше
  повторений, тем дороже каждая попытка подбора. В реальных системах берут сотни тысяч повторений. Результат по-прежнему
  детерминирован: те же пароль и соль дают тот же хеш.""",
  clr(), t('import hashlib\n\n\ndef slow_hash(password, salt):\n    raw = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 20000)\n    return raw.hex()\n\n\n', at="В стандартной"),
  t('print(len(slow_hash("qwerty", "s1")))\nprint(slow_hash("qwerty", "s1") == slow_hash("qwerty", "s1"))\nprint(slow_hash("qwerty", "s1") == slow_hash("qwerty", "s2"))\n', at="Результат"), run("Результат")),
 S("verify", "Проверка и случайная соль", """
  Соль нужно генерировать случайно. Для этого есть модуль secrets, предназначенный именно для безопасных случайных значений:
  обычный random для паролей и ключей не подходит. Функция token_hex возвращает случайную строку нужной длины в байтах.
  При проверке пароля сравнивайте хеши функцией compare_digest. Она работает за одно и то же время независимо от места
  первого расхождения, и по времени ответа нельзя угадать, сколько символов совпало.""",
  clr(), t('import hmac\nimport secrets\n\nsalt = secrets.token_hex(16)\nprint(len(salt))\nprint(hmac.compare_digest("abc", "abc"))\nprint(hmac.compare_digest("abc", "abd"))\n', at="Соль нужно"), run("При проверке")),
 S("summary", "Итог", """
  Подведём итог. Пароль не хранят: хранят соль и медленный хеш. Соль случайная и уникальная для каждого пользователя, её
  получают из secrets. Для хеширования используют pbkdf2_hmac или специализированные библиотеки, а при проверке сравнивают
  функцией compare_digest. И самое главное: не изобретайте собственных схем защиты, используйте проверенные средства.""",
  nt("соль (secrets) + медленный хеш (pbkdf2) + `compare_digest`", at="Подведём итог")),
]

notes = """
# Хеширование паролей

```python
import hashlib
import hmac
import secrets

salt = secrets.token_hex(16)
raw = hashlib.pbkdf2_hmac("sha256", "пароль".encode(), salt.encode(), 20000)
stored = raw.hex()

# проверка
check = hashlib.pbkdf2_hmac("sha256", "пароль".encode(), salt.encode(), 20000).hex()
print(hmac.compare_digest(stored, check))
```

## Правила

1. Пароль не хранят — только соль и хеш.
2. Соль — случайная и своя для каждого пользователя (`secrets`).
3. Хеш — медленный (`pbkdf2_hmac`, много повторений).
4. Сравнение — `hmac.compare_digest`.
5. Не изобретайте собственную криптографию.

`random` не подходит для безопасных значений — используйте `secrets`.
"""

HASH_H = 'import hashlib\n\n\ndef sha(text):\n    return hashlib.sha256(text.encode()).hexdigest()\n\n'
a1 = predict_task("a1-hash-props", "Свойства хеша",
  HASH_H + 'print(sha("a") == sha("a"))\nprint(sha("a") == sha("A"))\nprint(len(sha("очень длинная строка " * 100)))\nprint(sha("ab") == sha("a") + sha("b"))\n',
  [("True\nTrue\n64\nFalse", "Регистр меняет хеш полностью."), ("True\nFalse\n64\nTrue", "Хеш склейки не равен склейке хешей."), ("True\nFalse\n2100\nFalse", "Длина хеша не зависит от длины входа.")],
  hints("Одинаковый вход — одинаковый хеш.", "Большая и малая буква — разные входы.", "SHA-256 всегда даёт 64 шестнадцатеричных символа.", "Хеш склейки строк — не склейка хешей.", "Результат: True, False, 64, False."),
  "У хеша фиксированная длина, он детерминирован и сильно меняется от малейшего изменения входа.")

a2 = fn_task("a2-hash-password", "Хеш пароля с солью",
  "Напишите `hash_password(password, salt)`: верните строку — шестнадцатеричное представление результата `hashlib.pbkdf2_hmac(\"sha256\", пароль, соль, 5000)` (пароль и соль перед этим кодируются через `.encode()`).",
  "hash_password", "import hashlib\n\n\ndef hash_password(password, salt):\n    raw = hashlib.pbkdf2_hmac(\"sha256\", password.encode(), salt.encode(), 5000)\n    return raw.hex()\n",
  [["qwerty", "s1"], ["qwerty", "s2"], (["пароль", "соль"], True), (["", "x"], True), (["a" * 50, "salt"], True)],
  [("import hashlib\n\n\ndef hash_password(password, salt):\n    return hashlib.sha256(password.encode()).hexdigest()\n", "Нет соли и нет медленного хеширования."),
   ("import hashlib\n\n\ndef hash_password(password, salt):\n    raw = hashlib.pbkdf2_hmac(\"sha256\", password.encode(), salt.encode(), 1000)\n    return raw.hex()\n", "Неверное число повторений.")],
  hints("Нужна функция из модуля hashlib.", "pbkdf2_hmac принимает: имя алгоритма, байты пароля, байты соли, число повторений.", "Строки в байты переводит метод encode().", "Результат — байты; нужен шестнадцатеричный вид.", "У байтов есть метод hex()."),
  "pbkdf2_hmac возвращает байты. Метод hex() превращает их в строку, которую удобно хранить в базе.")

a3 = fn_task("a3-verify", "Проверка пароля",
  "Напишите `verify_password(password, salt, stored)`: пересчитайте хеш пароля с солью (`pbkdf2_hmac`, `sha256`, 5000 повторений, результат в hex) и сравните с `stored` функцией `hmac.compare_digest`. Верните `True` или `False`.",
  "verify_password", "import hashlib\nimport hmac\n\n\ndef verify_password(password, salt, stored):\n    raw = hashlib.pbkdf2_hmac(\"sha256\", password.encode(), salt.encode(), 5000)\n    return hmac.compare_digest(raw.hex(), stored)\n",
  [["qwerty", "s1", __import__("hashlib").pbkdf2_hmac("sha256", b"qwerty", b"s1", 5000).hex()], ["qwerty", "s1", __import__("hashlib").pbkdf2_hmac("sha256", b"qwerty2", b"s1", 5000).hex()], (["qwerty", "s2", __import__("hashlib").pbkdf2_hmac("sha256", b"qwerty", b"s1", 5000).hex()], True), (["", "s", __import__("hashlib").pbkdf2_hmac("sha256", b"", b"s", 5000).hex()], True), (["x", "s", "00"], True)],
  [("def verify_password(password, salt, stored):\n    return True\n", "Любой пароль подходит."),
   ("import hashlib\n\n\ndef verify_password(password, salt, stored):\n    return hashlib.sha256(password.encode()).hexdigest() == stored\n", "Другая схема хеширования: сравнение никогда не сходится.")],
  hints("Сначала пересчитайте хеш так же, как при регистрации.", "Тот же алгоритм, та же соль, то же число повторений.", "Результат приведите к hex.", "Сравните с сохранённым значением.", "Для сравнения используйте hmac.compare_digest."),
  "Проверка повторяет вычисление хеша и сравнивает результат с сохранённым за постоянное время.")

a4 = predict_task("a4-salt-demo", "Одинаковые пароли",
  'import hashlib\n\n\ndef h(password, salt=""):\n    return hashlib.sha256((salt + password).encode()).hexdigest()\n\n\nanna = h("qwerty")\nboris = h("qwerty")\nprint(anna == boris)\nanna = h("qwerty", "x1")\nboris = h("qwerty", "y2")\nprint(anna == boris)\nprint(h("qwerty", "x1") == anna)\n',
  [("False\nFalse\nTrue", "Без соли хеши одинаковых паролей совпадают."), ("True\nTrue\nTrue", "С разной солью хеши отличаются."), ("True\nFalse\nFalse", "Один и тот же пароль с той же солью даёт тот же хеш.")],
  hints("Без соли h(\"qwerty\") вычисляется одинаково.", "Первое сравнение: True.", "С разными солями хеши разные: False.", "Третье: тот же пароль и та же соль — тот же хеш.", "Результат: True, False, True."),
  "Соль делает хеши одинаковых паролей разными, а повторный расчёт с той же солью — воспроизводимым.")

a5 = fn_task("a5-record", "Не храните пароль в открытом виде",
  "Функция создаёт запись пользователя для базы, но сохраняет пароль как есть. Исправьте: вместо пароля сохраните соль и хеш (`pbkdf2_hmac`, `sha256`, 5000 повторений, hex). Запись: `{\"name\": имя, \"salt\": соль, \"hash\": хеш}`.",
  "make_record", "import hashlib\n\n\ndef make_record(name, password, salt):\n    raw = hashlib.pbkdf2_hmac(\"sha256\", password.encode(), salt.encode(), 5000)\n    return {\"name\": name, \"salt\": salt, \"hash\": raw.hex()}\n",
  [["anna", "qwerty", "s1"], ["boris", "qwerty", "s2"], (["v", "", "z"], True), (["i", "пароль", "соль"], True)],
  [("import hashlib\n\n\ndef make_record(name, password, salt):\n    return {\"name\": name, \"salt\": salt, \"hash\": hashlib.sha256(password.encode()).hexdigest()}\n", "Хеш без соли и без медленной функции.")],
  hints("В записи не должно быть пароля.", "Храните три поля: name, salt, hash.", "Хеш считается через pbkdf2_hmac.", "Пароль и соль переводятся в байты.", "Результат хеширования — hex."),
  "Запись содержит только то, что нужно для проверки: имя, соль и хеш. Сам пароль нигде не сохраняется.",
  type="fix", starter="def make_record(name, password, salt):\n    return {\"name\": name, \"password\": password}\n")

mistakes = [
 {"mistake": "Хранят пароль или его обратимое «шифрование»", "fix": "Храните соль и хеш; пароль восстановить нельзя и не нужно."},
 {"mistake": "Используют быстрый sha256 без соли", "fix": "Берите pbkdf2_hmac (или bcrypt/argon2) и случайную соль для каждого пользователя."},
 {"mistake": "Генерируют соль через random", "fix": "random предсказуем; для безопасных значений — модуль secrets."},
 {"mistake": "Сравнивают хеши через ==", "fix": "Используйте hmac.compare_digest."}]

finish("sec-02-passwords", "Хеширование паролей", "Хранить пароли безопасно: соль, медленный хеш, постоянное по времени сравнение.",
  {"sec.hash": "Хеш-функции", "sec.salt": "Соль", "sec.pbkdf2": "pbkdf2_hmac"},
  ["sec-01-threat-model"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="security-lab")

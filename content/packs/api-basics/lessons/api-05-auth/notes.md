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

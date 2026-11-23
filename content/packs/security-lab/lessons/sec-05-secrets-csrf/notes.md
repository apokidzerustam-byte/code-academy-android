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

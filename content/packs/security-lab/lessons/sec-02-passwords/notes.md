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

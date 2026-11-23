# Выпуск приложения

```python
def parse_version(text):
    return tuple(int(p) for p in text.split("."))

print(parse_version("1.10.0") > parse_version("1.9.0"))

SECRET_PATTERNS = (".jks", ".keystore", ".env")

def is_secret(path):
    return path.endswith(SECRET_PATTERNS)

print(is_secret("app/release.jks"))
```

## Правила

1. Патч — исправления, минор — совместимые новинки, мажор — несовместимые изменения.
2. Ключ подписи и пароли не хранятся в репозитории.
3. Ключ нужно резервировать: без него обновить приложение нельзя.

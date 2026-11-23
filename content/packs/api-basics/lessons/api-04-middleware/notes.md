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

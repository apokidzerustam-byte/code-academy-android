# Тестирование API на FastAPI

Тестовый клиент вызывает приложение **внутри программы**: не нужны сервер, порт и сеть.

```py
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


@app.get("/ping")
def ping():
    return {"status": "ok"}


client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

## Что передавать в запросе

| Что | Как |
|---|---|
| тело JSON | `client.post("/items", json={...})` |
| параметры строки запроса | `client.get("/items", params={"limit": 5})` |
| заголовки | `client.get("/secret", headers={"X-API-Key": "..."})` |

## Что проверять в каждом маршруте

1. Счастливый путь: верный запрос — верный ответ.
2. Плохие данные: нет поля, неверный тип, значение вне границ — **422**.
3. Нет или подделка авторизации — **401** / **403**.
4. Несуществующий объект — **404**.
5. Граничные значения: ноль, пустая строка, максимум.

Проверяйте и код ответа, и тело.

## Независимость тестов

Не пользуйтесь общим состоянием: создавайте приложение функцией (`make_app()`) для каждого теста.

## Подмена зависимостей

```py
app.dependency_overrides[get_rate] = lambda: 5.0   # на время теста
app.dependency_overrides.clear()                    # очистить после теста
```

В настоящем проекте тесты запускает `pytest`; принцип проверок тот же.

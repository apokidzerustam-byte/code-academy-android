# FastAPI: проверка данных и страницы

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()
ITEMS = []

class ItemIn(BaseModel):
    name: str = Field(..., min_length=2)   # обязательное, не короче 2 символов
    price: float = Field(..., gt=0)        # обязательное, строго больше 0
    qty: int = Field(1, ge=1)              # по умолчанию 1, не меньше 1

@app.post("/items", status_code=201)
def add_item(item: ItemIn):
    for it in ITEMS:
        if it["name"] == item.name:
            raise HTTPException(status_code=409, detail="Такой товар уже есть")
    ITEMS.append({"name": item.name, "price": item.price, "qty": item.qty})
    return ITEMS[-1]

@app.get("/items")
def list_items(limit: int = 10, offset: int = 0):
    return ITEMS[offset:offset + limit]
```

| Ограничение | Смысл |
|---|---|
| `min_length`, `max_length` | длина строки |
| `gt`, `ge` | больше / не меньше |
| `lt`, `le` | меньше / не больше |

| Код | Когда |
|---|---|
| 422 | данные не прошли проверку модели (FastAPI отвечает сам) |
| 409 | конфликт: такая запись уже есть |
| 404 | записи нет |

- `...` в `Field(...)` — поле обязательное.
- Значение по умолчанию **не проверяется**: `Field(0, ge=1)` — ошибка автора.
- Параметры запроса `limit` и `offset` — просто аргументы функции со значениями по умолчанию.

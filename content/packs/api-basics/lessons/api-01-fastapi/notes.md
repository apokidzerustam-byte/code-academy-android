# FastAPI: свой веб-API

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/items/{item_id}")          # параметр пути
def get_item(item_id: int, q: str = ""):   # q — параметр запроса ?q=...
    return {"item_id": item_id, "q": q}

class Item(BaseModel):                # тело запроса (JSON)
    name: str
    price: float

@app.post("/items")
def create(item: Item):
    return {"name": item.name}

@app.get("/books/{book_id}")
def book(book_id: int):
    raise HTTPException(status_code=404, detail="Не найдено")
```

## Проверка в приложении — без сети
```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int, q: str = ""):
    return {"item_id": item_id, "q": q}

client = TestClient(app)
r = client.get("/items/5", params={"q": "чай"})
print(r.status_code, r.json())   # 200 {'item_id': 5, 'q': 'чай'}
```

## Коды ответа
| Код | Когда |
|---|---|
| 200 | всё хорошо |
| 404 | не найдено (`HTTPException(404)`) |
| 422 | данные не прошли проверку типов (FastAPI сам) |

## На компьютере
`pip install fastapi uvicorn`, затем `uvicorn main:app --reload` → http://127.0.0.1:8000/docs — автоматическая документация.

## Частые ошибки
- Нет аннотации типа: `def add(a, b)` — параметры придут строками, `a + b` склеит их.
- Имя параметра в пути и в функции не совпадает.
- Функция ничего не возвращает — ответ `null`.
- Забыли `app = FastAPI()` или назвали приложение иначе.

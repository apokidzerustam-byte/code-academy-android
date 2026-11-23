# FastAPI: CRUD — список дел

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
TASKS = {}
NEXT_ID = 1

class TaskIn(BaseModel):
    title: str
    done: bool = False

@app.post("/tasks", status_code=201)          # создать
def create_task(task: TaskIn):
    global NEXT_ID
    TASKS[NEXT_ID] = {"id": NEXT_ID, "title": task.title, "done": task.done}
    NEXT_ID += 1
    return TASKS[NEXT_ID - 1]

@app.get("/tasks")                            # прочитать все
def list_tasks():
    return list(TASKS.values())

@app.get("/tasks/{task_id}")                  # прочитать одну
def get_task(task_id: int):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return TASKS[task_id]
```

| Действие | Метод | Путь | Успех |
|---|---|---|---|
| создать | POST | `/tasks` | 201 |
| прочитать все | GET | `/tasks` | 200 |
| прочитать одну | GET | `/tasks/{id}` | 200 / 404 |
| заменить | PUT | `/tasks/{id}` | 200 / 404 |
| удалить | DELETE | `/tasks/{id}` | 200 / 404 |

- Переменную модуля меняют после слова `global`.
- Данные в словаре живут, пока работает сервер.
- Неверное тело запроса → 422 (FastAPI сам).

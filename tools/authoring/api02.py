"""Урок FastAPI 2: CRUD — список дел в памяти (POST/GET/PUT/DELETE).
Вывод сцен и поведение заданий сверяет валидатор в CI настоящим FastAPI; локально FastAPI недоступен."""
from mk import *

HEAD = ("from fastapi import FastAPI, HTTPException\nfrom fastapi.testclient import TestClient\nfrom pydantic import BaseModel\n\n"
        "app = FastAPI()\nTASKS = {}\nNEXT_ID = 1\n\n\nclass TaskIn(BaseModel):\n    title: str\n    done: bool = False\n")
POST = ('\n\n@app.post("/tasks", status_code=201)\ndef create_task(task: TaskIn):\n    global NEXT_ID\n'
        '    TASKS[NEXT_ID] = {"id": NEXT_ID, "title": task.title, "done": task.done}\n    NEXT_ID += 1\n    return TASKS[NEXT_ID - 1]\n')
GET = ('\n\n@app.get("/tasks")\ndef list_tasks():\n    return list(TASKS.values())\n\n\n'
       '@app.get("/tasks/{task_id}")\ndef get_task(task_id: int):\n    if task_id not in TASKS:\n'
       '        raise HTTPException(status_code=404, detail="Задача не найдена")\n    return TASKS[task_id]\n')
PUT = ('\n\n@app.put("/tasks/{task_id}")\ndef update_task(task_id: int, task: TaskIn):\n    if task_id not in TASKS:\n'
       '        raise HTTPException(status_code=404, detail="Задача не найдена")\n'
       '    TASKS[task_id] = {"id": task_id, "title": task.title, "done": task.done}\n    return TASKS[task_id]\n')
DELETE = ('\n\n@app.delete("/tasks/{task_id}")\ndef delete_task(task_id: int):\n    if task_id not in TASKS:\n'
          '        raise HTTPException(status_code=404, detail="Задача не найдена")\n    del TASKS[task_id]\n    return {"deleted": task_id}\n')
SETUP2 = ('\n\nclient = TestClient(app)\nclient.post("/tasks", json={"title": "Купить молоко"})\n'
          'client.post("/tasks", json={"title": "Написать отчёт", "done": True})\n')

C1, R1 = HEAD + POST, ('\n\nclient = TestClient(app)\nr = client.post("/tasks", json={"title": "Купить молоко"})\nprint(r.status_code, r.json())\n'
                       'r = client.post("/tasks", json={"title": "Написать отчёт", "done": True})\nprint(r.status_code, r.json())\n')
O1 = "201 {'id': 1, 'title': 'Купить молоко', 'done': False}\n201 {'id': 2, 'title': 'Написать отчёт', 'done': True}\n"
C2, R2 = HEAD + POST + GET, SETUP2 + 'print(client.get("/tasks").json())\nprint(client.get("/tasks/2").json())\nprint(client.get("/tasks/9").status_code)\n'
O2 = ("[{'id': 1, 'title': 'Купить молоко', 'done': False}, {'id': 2, 'title': 'Написать отчёт', 'done': True}]\n"
      "{'id': 2, 'title': 'Написать отчёт', 'done': True}\n404\n")
C3, R3 = HEAD + POST + GET + PUT, SETUP2 + ('print(client.put("/tasks/1", json={"title": "Купить молоко", "done": True}).json())\n'
                                              'print(client.put("/tasks/9", json={"title": "X"}).status_code)\nprint(client.get("/tasks/1").json())\n')
O3 = "{'id': 1, 'title': 'Купить молоко', 'done': True}\n404\n{'id': 1, 'title': 'Купить молоко', 'done': True}\n"
C4, R4 = HEAD + POST + GET + PUT + DELETE, SETUP2 + ('print(client.delete("/tasks/2").json())\nprint(client.get("/tasks/2").status_code)\n'
                                                      'print(client.delete("/tasks/2").status_code)\nprint(len(client.get("/tasks").json()))\n')
O4 = "{'deleted': 2}\n404\n404\n1\n"

scenes = [
    scene("intro", "Четыре действия с данными", """
      Почти любое приложение умеет четыре вещи с данными: создать, прочитать, изменить и удалить. По-английски это CRUD. В веб-API
      каждому действию соответствует метод запроса. POST создаёт, GET читает, PUT заменяет, DELETE удаляет. Сегодня на этой основе
      напишем сервер списка дел, который хранит задачи в памяти.""",
          [NOTE("CRUD: **C**reate — POST · **R**ead — GET · **U**pdate — PUT · **D**elete — DELETE", at="В веб-API")]),
    scene("create", "Создаём задачу: POST", """
      Задачи хранятся в словаре, ключ — номер. Счётчик следующего номера лежит в переменной NEXT_ID. Модель TaskIn описывает то,
      что присылает клиент: название и признак выполнения, по умолчанию ложь. Обработчик POST записывает задачу под новым
      номером и увеличивает счётчик. Параметр status_code равно двести один говорит: создано. Отправим две задачи.""",
          [CLEAR(), T(C1 + R1, at="Задачи хранятся"), HL([6, 7], at="Задачи хранятся"), HL([10, 11, 12], at="Модель TaskIn"), HL([15, 16, 17, 18, 19, 20], at="Обработчик POST"),
           HL([15], at="status_code"), RUN(at="Отправим"), OUT(O1, at="Отправим")]),
    scene("read", "Читаем: GET", """
      Теперь чтение. Адрес tasks без номера возвращает все задачи списком. Адрес с номером возвращает одну задачу, а если такого
      номера нет, поднимаем исключение с кодом четыреста четыре. Запрашиваем весь список, вторую задачу и несуществующую девятую.""",
          [CLEAR(), T(C2 + R2, at="Теперь чтение"), HL([23, 24, 25], at="без номера"), HL([28, 29, 30, 31, 32], at="с номером"), RUN(at="Запрашиваем"), OUT(O2, at="Запрашиваем")]),
    scene("update", "Заменяем: PUT", """
      Метод PUT заменяет задачу целиком. Обработчик получает и номер из адреса, и новое тело. Если номера нет, снова четыреста
      четыре. Отметим молоко выполненным. Заметьте: запрос к девятой задаче вернул ошибку, а после обновления чтение первой показывает
      новое значение.""",
          [CLEAR(), T(C3 + R3, at="Метод PUT"), HL([35, 36, 37, 38, 39, 40], at="Обработчик получает"), RUN(at="Отметим"), OUT(O3, at="Отметим")]),
    scene("delete", "Удаляем: DELETE", """
      Удаление — метод DELETE. Если задача есть, убираем её из словаря и сообщаем, какой номер удалён. Удалим вторую задачу.
      Теперь чтение второй даёт четыреста четыре, повторное удаление — тоже, а в списке осталась одна задача.""",
          [CLEAR(), T(C4 + R4, at="Удаление"), HL([43, 44, 45, 46, 47, 48], at="Если задача"), RUN(at="Удалим"), OUT(O4, at="Удалим")]),
    scene("summary", "Итог", """
      Подведём итог. CRUD — это создание, чтение, изменение и удаление, а в API им соответствуют POST, GET, PUT и DELETE. Код двести
      один сообщает о создании, четыреста четыре — о том, что не найдено. Данные в словаре живут, пока работает сервер; чтобы они
      сохранялись, нужна база данных, а о ней — в следующих этапах.""",
          [NOTE("POST → 201 · GET → 200 · PUT → 200 · DELETE → 200 · нет такой записи → 404", at="Подведём")]),
]

notes = """
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
"""

PRE = HEAD + "\n"
SEED = HEAD.replace("TASKS = {}\nNEXT_ID = 1", 'TASKS = {\n    1: {"id": 1, "title": "Хлеб", "done": True},\n    2: {"id": 2, "title": "Чай", "done": False},\n    3: {"id": 3, "title": "Сыр", "done": True},\n}\nNEXT_ID = 4')
GETONE = ('\n\n@app.get("/tasks/{task_id}")\ndef get_task(task_id: int):\n    if task_id not in TASKS:\n'
          '        raise HTTPException(status_code=404, detail="Задача не найдена")\n    return TASKS[task_id]\n')

# --- Задание 1: POST и GET списка ---
S1 = HEAD + POST + '\n\n@app.get("/tasks")\ndef list_tasks():\n    return list(TASKS.values())\n'
t1 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "POST", "path": "/tasks", "json": {"title": "А"}, "expected_status": 201, "expected_json": {"id": 1, "title": "А", "done": False}},
    {"id": "v2", "method": "POST", "path": "/tasks", "json": {"title": "Б", "done": True}, "expected_status": 201, "expected_json": {"id": 2, "title": "Б", "done": True}},
    {"id": "h1", "hidden": True, "path": "/tasks", "expected_json": [{"id": 1, "title": "А", "done": False}, {"id": 2, "title": "Б", "done": True}],
     "hint": "GET /tasks возвращает все задачи списком, в порядке создания"},
    {"id": "h2", "hidden": True, "method": "POST", "path": "/tasks", "json": {"done": True}, "expected_status": 422, "hint": "Без названия задача не создаётся — 422"},
    {"id": "h3", "hidden": True, "method": "POST", "path": "/tasks", "json": {"title": "В"}, "expected_status": 201, "expected_json": {"id": 3, "title": "В", "done": False},
     "hint": "Номера растут на единицу, а неудачный запрос номер не занимает"},
]}
a1 = asg("a1-create", "write", "Создать и показать",
         "Допишите приложение. Сделайте:\n\n- **POST** `/tasks` с кодом **201**: записывает задачу в `TASKS` под номером `NEXT_ID`, увеличивает `NEXT_ID` и возвращает `{\"id\": …, \"title\": …, \"done\": …}`;\n- **GET** `/tasks`: возвращает список всех задач в порядке создания.",
         "Писать POST-обработчик с моделью и счётчиком.", "Модель TaskIn, словарь TASKS и счётчик NEXT_ID уже заданы.", "Задачи создаются и читаются списком.",
         ["Не меняйте TaskIn, TASKS и NEXT_ID.", "Счётчик меняют после слова global."],
         hints("POST-обработчик получает параметр с типом модели: task: TaskIn.", "Код 201 задаёт параметр декоратора: status_code=201.", "Чтобы изменить NEXT_ID, объявите global NEXT_ID.", "Положите в TASKS[NEXT_ID] словарь с id, title и done; затем увеличьте NEXT_ID.", "GET /tasks — return list(TASKS.values())."),
         t1, S1, "Обработчик POST записывает задачу под номером NEXT_ID и сдвигает счётчик; GET отдаёт все значения словаря списком.",
         ["POST создаёт задачу с кодом 201.", "GET показывает все задачи."],
         [(S1.replace('status_code=201', 'status_code=200'), "Создание должно возвращать код 201."),
          (S1.replace("    NEXT_ID += 1\n", ""), "Счётчик не растёт: все задачи получают номер 1."),
          (S1.replace("list(TASKS.values())", "TASKS"), "Возвращён словарь вместо списка."),
          (S1.replace('"done": task.done', '"done": False'), "Признак выполнения из запроса игнорируется.")],
         starter=HEAD + "\n# POST /tasks (код 201) и GET /tasks\n")

# --- Задание 2: GET одной и DELETE ---
S2 = SEED + GETONE + DELETE
t2 = {"kind": "fastapi", "cases": [
    {"id": "v1", "path": "/tasks/2", "expected_json": {"id": 2, "title": "Чай", "done": False}},
    {"id": "v2", "method": "DELETE", "path": "/tasks/2", "expected_json": {"deleted": 2}},
    {"id": "h1", "hidden": True, "path": "/tasks/2", "expected_status": 404, "expected_json": {"detail": "Задача не найдена"}, "hint": "После удаления задача не находится — 404"},
    {"id": "h2", "hidden": True, "method": "DELETE", "path": "/tasks/9", "expected_status": 404, "expected_json": {"detail": "Задача не найдена"}},
    {"id": "h3", "hidden": True, "path": "/tasks/3", "expected_json": {"id": 3, "title": "Сыр", "done": True}, "hint": "Другие задачи не затронуты"},
    {"id": "h4", "hidden": True, "path": "/tasks/abc", "expected_status": 422},
]}
a2 = asg("a2-get-delete", "write", "Одна задача и удаление",
         "В `TASKS` уже три задачи. Сделайте:\n\n- **GET** `/tasks/{task_id}`: возвращает задачу; если нет — код **404** и `{\"detail\": \"Задача не найдена\"}`;\n- **DELETE** `/tasks/{task_id}`: удаляет задачу и возвращает `{\"deleted\": task_id}`; если нет — тот же 404.",
         "Читать и удалять по номеру из пути.", "Номер задачи в пути.", "Задача или 404; удаление.",
         ["Не меняйте TASKS и TaskIn.", "Номер в пути — целое."],
         hints("Номер берётся из пути: \"/tasks/{task_id}\" и параметр task_id: int.", "Сначала проверьте: task_id not in TASKS.", "Ошибку поднимают: raise HTTPException(status_code=404, detail=\"Задача не найдена\").", "Из словаря удаляют так: del TASKS[task_id].", "Ответ удаления: return {\"deleted\": task_id}."),
         t2, S2, "Обе функции сначала проверяют, что номер есть, иначе поднимают 404; DELETE ещё и убирает ключ из словаря.",
         ["GET возвращает задачу или 404.", "DELETE удаляет и сообщает номер."],
         [(S2.replace('    del TASKS[task_id]\n', ''), "Задача не удаляется: после DELETE она по-прежнему находится."),
          (SEED + GETONE.replace("TASKS[task_id]", "TASKS[task_id]['title']") + DELETE, "Возвращено только название, а нужна вся задача."),
          (SEED + GETONE + DELETE.replace("status_code=404, detail=\"Задача не найдена\"", "status_code=400, detail=\"Задача не найдена\""), "Для отсутствующей задачи нужен код 404, а не 400.")],
         starter=SEED + "\n# GET /tasks/{task_id} и DELETE /tasks/{task_id}\n")

# --- Задание 3: PUT ---
S3 = SEED + GETONE + PUT
t3 = {"kind": "fastapi", "cases": [
    {"id": "v1", "method": "PUT", "path": "/tasks/1", "json": {"title": "Хлеб и масло", "done": False}, "expected_json": {"id": 1, "title": "Хлеб и масло", "done": False}},
    {"id": "v2", "path": "/tasks/1", "expected_json": {"id": 1, "title": "Хлеб и масло", "done": False}, "hint": "После PUT чтение показывает новое значение"},
    {"id": "h1", "hidden": True, "method": "PUT", "path": "/tasks/9", "json": {"title": "X"}, "expected_status": 404, "expected_json": {"detail": "Задача не найдена"}},
    {"id": "h2", "hidden": True, "method": "PUT", "path": "/tasks/2", "json": {"done": True}, "expected_status": 422, "hint": "Без названия — 422"},
    {"id": "h3", "hidden": True, "path": "/tasks/2", "expected_json": {"id": 2, "title": "Чай", "done": False}, "hint": "Неудачный PUT ничего не меняет"},
    {"id": "h4", "hidden": True, "method": "PUT", "path": "/tasks/3", "json": {"title": "Сыр"}, "expected_json": {"id": 3, "title": "Сыр", "done": False},
     "hint": "Если done не прислали — берётся значение по умолчанию (ложь)"},
]}
a3 = asg("a3-put", "write", "Заменить задачу",
         "Сделайте **PUT** `/tasks/{task_id}`: принимает тело `TaskIn`, **заменяет** задачу с этим номером на `{\"id\": task_id, \"title\": …, \"done\": …}` и возвращает её. Если номера нет — код **404** и `{\"detail\": \"Задача не найдена\"}`.",
         "Писать PUT с путём и телом.", "Номер в пути и JSON-тело.", "Обновлённая задача или 404.",
         ["id задачи при замене не меняется."],
         hints("У PUT два входа: номер из пути и тело. def update_task(task_id: int, task: TaskIn).", "Сначала проверьте, что номер существует.", "Нет номера — raise HTTPException(status_code=404, …).", "Запишите TASKS[task_id] = {…} с тем же id.", "Верните TASKS[task_id]."),
         t3, S3, "PUT получает номер из пути и тело из JSON; замена выполняется только для существующей задачи.",
         ["PUT заменяет существующую задачу.", "Нет задачи → 404."],
         [(S3.replace('    TASKS[task_id] = {"id": task_id, "title": task.title, "done": task.done}\n    return TASKS[task_id]\n', '    return {"id": task_id, "title": task.title, "done": task.done}\n'), "Ответ верный, но в TASKS ничего не записано."),
          (S3.replace('    if task_id not in TASKS:\n        raise HTTPException(status_code=404, detail="Задача не найдена")\n    TASKS[task_id] =', '    TASKS[task_id] ='), "Нет проверки: PUT к несуществующей задаче создаёт её."),
          (S3.replace('"id": task_id, "title": task.title', '"id": 1, "title": task.title'), "Номер задачи не из пути.")],
         starter=SEED + GETONE + "\n# PUT /tasks/{task_id}\n")

# --- Задание 4: фильтр ---
SEED4 = "from typing import Optional\n" + SEED
FILT_BAD = '\n\n@app.get("/tasks")\ndef list_tasks(done: Optional[bool] = None):\n    if done:\n        return [t for t in TASKS.values() if t["done"]]\n    return list(TASKS.values())\n'
FILT_OK = ('\n\n@app.get("/tasks")\ndef list_tasks(done: Optional[bool] = None):\n    if done is not None:\n'
           '        return [t for t in TASKS.values() if t["done"] == done]\n    return list(TASKS.values())\n')
T1, T2, T3 = {"id": 1, "title": "Хлеб", "done": True}, {"id": 2, "title": "Чай", "done": False}, {"id": 3, "title": "Сыр", "done": True}
t4 = {"kind": "fastapi", "cases": [
    {"id": "all", "path": "/tasks", "expected_json": [T1, T2, T3]},
    {"id": "done", "path": "/tasks", "params": {"done": True}, "expected_json": [T1, T3]},
    {"id": "todo", "path": "/tasks", "params": {"done": False}, "expected_json": [T2], "hint": "done=false — только невыполненные"},
    {"id": "bad", "hidden": True, "path": "/tasks", "params": {"done": "maybe"}, "expected_status": 422},
]}
a4 = asg("a4-filter", "fix", "Фильтр по статусу",
         "Адрес `/tasks?done=true` должен возвращать только выполненные задачи, `/tasks?done=false` — только невыполненные, без параметра — все. Сейчас `done=false` почему-то возвращает **все** задачи. Найдите ошибку.",
         "Отличать False от «параметр не передан».", "Параметр запроса done.", "Три режима фильтра.",
         ["Параметр done необязательный."],
         hints("Запросите /tasks?done=false и посмотрите, что вернулось.", "Условие if done: для значения False не срабатывает.", "Но False — это значение, а не отсутствие параметра.", "Отсутствие параметра — None. Сравнивайте с None.", "if done is not None: и сравнение t[\"done\"] == done"),
         t4, SEED4 + FILT_OK, "if done: считает False «пустым», поэтому ветка фильтрации пропускается. Проверка is not None различает False и «не передано».",
         ["done=true, done=false и без параметра работают."],
         [(SEED4 + FILT_BAD, "Ошибка осталась: для False возвращаются все задачи."),
          (SEED4 + FILT_OK.replace('t["done"] == done', 't["done"]'), "Всегда возвращаются выполненные, даже при done=false.")],
         starter=SEED4 + FILT_BAD)

CODE5 = ('from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\napp = FastAPI()\nitems = []\n\n\n'
         '@app.post("/add/{x}")\ndef add(x: int):\n    items.append(x)\n    return len(items)\n\n\n'
         '@app.get("/sum")\ndef total():\n    return sum(items)\n\n\nclient = TestClient(app)\n'
         'print(client.post("/add/5").json())\nprint(client.post("/add/7").json())\nprint(client.get("/sum").json())\n'
         'print(client.get("/add/1").status_code)\nprint(client.post("/add/x").status_code)\nprint(client.get("/sum").json())\n')
ans5 = "1\n2\n12\n405\n422\n12"
a5 = asg("a5-predict", "predict", "Что напечатает клиент?",
         "Что напечатает программа? Каждая строка вывода — с новой строки.",
         "Предсказывать коды и ответы API.", "—", "Шесть строк.", [],
         hints("Идём сверху вниз: сервер хранит items между запросами.", "Первый POST добавляет 5 и возвращает длину списка — 1.", "Второй добавляет 7: длина 2. Сумма 5 + 7 = 12.", "GET по адресу, где разрешён только POST, — код 405.", "Текст вместо числа в пути — код 422, и items не меняется."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "POST возвращает длину списка (1, затем 2), GET /sum — 12. Метод GET для /add не разрешён — 405, «x» — не число — 422, а сумма осталась 12.",
         ["Все шесть строк верны."],
         [("1\n2\n12\n404\n422\n12", "Адрес /add существует, но только для POST: это 405, а не 404."),
          ("5\n7\n12\n405\n422\n12", "POST возвращает длину списка, а не добавленное число.")],
         code=CODE5)

skills = {"api.crud": "CRUD: создать, прочитать, изменить, удалить", "api.state": "Данные в памяти сервера", "api.filter": "Необязательные параметры запроса"}
merge_pack_f = ROOT / "content/packs/api-basics/pack.json"
write_lesson("api-02-crud", "FastAPI: список дел (CRUD)",
             "Писать обработчики POST, GET, PUT и DELETE, хранить данные в памяти сервера и возвращать верные коды ответа.",
             list(skills), ["api-01-fastapi"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Счётчик меняют без global", "fix": "Переменную модуля внутри функции меняют после слова global.", "errorType": "UnboundLocalError"},
              {"mistake": "if done: вместо if done is not None:", "fix": "False — тоже значение; «не передано» — это None."},
              {"mistake": "Забыли проверить существование номера", "fix": "Без проверки обращение к словарю даёт KeyError и код 500."},
              {"mistake": "Код 200 при создании", "fix": "Создание отвечает 201: status_code=201."}],
             min_pass=3, pack="api-basics", runner="A")
f = merge_pack_f
data = json.loads(f.read_text("utf-8"))
if "api-02-crud" not in data["lessons"]:
    data["lessons"].append("api-02-crud")
data["skills"].update(skills)
data["stage"] = 8
data["description"] = "Свой сервер на Python: обработчики, параметры, модели данных, CRUD и коды ответа. Запросы — тестовым клиентом без сети."
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

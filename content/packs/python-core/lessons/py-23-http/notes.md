# HTTP без сети

```python
from urllib.parse import urlparse, parse_qs, urlencode

url = "https://api.example.com/tasks?status=open&limit=5"
parts = urlparse(url)
print(parts.scheme, parts.netloc, parts.path)   # https api.example.com /tasks
print(parse_qs(parts.query))                    # {'status': ['open'], 'limit': ['5']}
print(urlencode({"q": "учёт", "page": 2}))
```

## Коды состояния

| Код | Смысл |
|---|---|
| 200 | OK |
| 201 | Создано |
| 301 | Перенаправление |
| 404 | Не найдено |
| 500 | Ошибка сервера |

## Сырой ответ

```python
import json

raw = "HTTP/1.1 200 OK\nContent-Type: application/json\n\n{\"id\": 7}"
head, body = raw.split("\n\n", 1)
lines = head.split("\n")
status = int(lines[0].split()[1])
headers = dict(line.split(": ", 1) for line in lines[1:])
print(status, headers["Content-Type"], json.loads(body))
```

## Запомните

1. Адрес разбирайте через `urllib.parse`.
2. Параметры собирайте через `urlencode` — он экранирует символы.
3. Всегда проверяйте код состояния, прежде чем читать тело.

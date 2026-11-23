# Клиент, сервер и HTTP

```python
from urllib.parse import urlparse, parse_qs

parts = urlparse("https://example.com/search?q=python&page=2")
print(parts.netloc)          # example.com
print(parse_qs(parts.query)) # {'q': ['python'], 'page': ['2']}
```

| Метод | Смысл |
|---|---|
| GET | получить данные |
| POST | отправить данные |
| PUT | обновить |
| DELETE | удалить |

| Код | Значение |
|---|---|
| 2xx | успех |
| 3xx | перенаправление |
| 4xx | ошибка клиента |
| 5xx | ошибка сервера |

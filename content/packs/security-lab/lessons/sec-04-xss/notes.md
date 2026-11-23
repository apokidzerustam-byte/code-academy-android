# XSS и экранирование

```python
import html

def render(text):
    return f"<p>{html.escape(text)}</p>"

print(render("<script>alert(1)</script>"))
```

## Правила

1. Весь внешний текст при выводе в HTML — через `html.escape`.
2. В атрибутах экранируйте и кавычки.
3. Адреса: разрешайте только схемы `http` и `https`.
4. Шаблонизаторы с автоэкранированием; в JS — `textContent`, не `innerHTML`.
5. Дополнительно: Content-Security-Policy, cookie с `HttpOnly`.

Экранируйте при выводе, а не при сохранении.

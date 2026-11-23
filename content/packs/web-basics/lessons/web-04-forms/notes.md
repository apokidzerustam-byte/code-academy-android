# Смысловая вёрстка и формы

```html
<header><h1>Мой блог</h1><nav>…</nav></header>
<main>
  <section><h2>Записи</h2><article>…</article></section>
</main>
<footer>© 2026</footer>

<form>
  <label for="email">Почта</label>
  <input id="email" name="email" type="email" required>

  <select id="plan" name="plan">
    <option value="free">Бесплатный</option>
  </select>

  <label><input type="checkbox" name="agree"> Согласен</label>
  <button type="submit">Отправить</button>
</form>
```

| Тег / атрибут | Для чего |
|---|---|
| `header`, `nav`, `main`, `footer` | смысл блоков страницы |
| `label for="id"` | подпись, связанная с полем |
| `type` | text, email, number, checkbox, password |
| `required`, `min`, `max`, `pattern` | проверка в браузере |
| `name` | имя поля при отправке данных |

- `h1` на странице один; дальше `h2`, `h3` по порядку.
- Проверка в браузере (`form.checkValidity()`) — удобство, а **не защита**: сервер проверяет заново.
- Подпись без связи (`for` ≠ `id`) — частая ошибка доступности.

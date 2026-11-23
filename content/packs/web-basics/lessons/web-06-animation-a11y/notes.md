# Анимации и доступность

```css
.btn {
  transition: background 0.3s;         /* в обычном состоянии, а не в :hover */
}
.btn:hover { background: darkcyan; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.loader { animation: spin 1s linear infinite; }

@media (prefers-reduced-motion: reduce) {
  .loader { animation: none; }
}

button:focus-visible { outline: 3px solid orange; }
```

```html
<img src="team.jpg" alt="Фото команды">
<label for="q">Поиск</label> <input id="q">
<button aria-label="Поиск">🔍</button>
```

| Что | Правило |
|---|---|
| быстрая анимация | `transform`, `opacity` |
| уменьшение движения | `@media (prefers-reduced-motion: reduce)` |
| контраст текста | не меньше 4.5 : 1 (крупный — 3 : 1) |
| фокус | не убирайте `outline` без замены |

- Контраст: `(L светлого + 0.05) / (L тёмного + 0.05)`, где L — относительная яркость цвета.
- Кнопка — `button`, ссылка — `a`: фокус и клавиатура работают сами.

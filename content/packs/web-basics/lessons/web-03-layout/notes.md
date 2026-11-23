# CSS: блочная модель и flexbox

```css
.card {
  width: 100px;          /* содержимое */
  padding: 10px;         /* внутренний отступ */
  border: 5px solid teal;
  margin: 20px;          /* внешний отступ */
}
/* ширина с рамкой = 100 + 2·10 + 2·5 = 130 (margin не входит) */

.menu {
  display: flex;         /* дети — в ряд */
  gap: 12px;
  justify-content: space-between;   /* вдоль ряда */
  align-items: center;              /* поперёк */
}
```

| Свойство | Значения |
|---|---|
| `justify-content` | `flex-start`, `center`, `flex-end`, `space-between`, `space-around` |
| `align-items` | `stretch`, `flex-start`, `center`, `flex-end` |
| `flex-direction` | `row` (по умолчанию), `column` |

- `display: flex` пишут **родителю**, а не детям.
- Центр по экрану: `body { display:flex; justify-content:center; align-items:center; min-height:100vh; }`.
- `box-sizing: border-box` — ширина включает padding и рамку.
- Если элементы не встают в ряд, проверьте `display: flex` у родителя.

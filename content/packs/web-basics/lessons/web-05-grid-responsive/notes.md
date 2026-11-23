# CSS Grid и адаптивная вёрстка

```css
.gallery {
  display: grid;                              /* включаем сетку у родителя */
  grid-template-columns: repeat(3, 1fr);      /* три равные колонки */
  gap: 10px;                                  /* промежуток */
}
.top { grid-column: 1 / -1; }                 /* на все колонки */

/* mobile-first: база — для телефона */
@media (min-width: 600px) {
  .gallery { grid-template-columns: repeat(3, 1fr); }
}

/* колонки подбираются сами */
.catalog { grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); }

img { max-width: 100%; height: auto; }
```

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

| Что | Как |
|---|---|
| колонки | `grid-template-columns: 1fr 2fr 1fr` — доли свободного места |
| промежуток | `gap` вычитается из ширины до деления на доли |
| на всю ширину | `grid-column: 1 / -1` |
| от ширины и шире | `@media (min-width: ...)` |

- Начинайте с раскладки для телефона, а широкие экраны добавляйте медиазапросами.
- Без `meta viewport` телефон показывает уменьшенную настольную страницу.
- Картинке нужны `max-width: 100%` **и** `height: auto`, иначе она исказится.

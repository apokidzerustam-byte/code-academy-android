# JavaScript: страница и DOM

```js
const h = document.querySelector("h1");          // первый подходящий
document.querySelectorAll("li");                 // все подходящие
h.textContent = "Новый заголовок";

const li = document.createElement("li");
li.textContent = "Молоко";
document.getElementById("list").appendChild(li);
li.classList.toggle("done");                     // добавить/убрать класс
li.remove();                                     // удалить элемент

button.addEventListener("click", () => { … });   // реакция на событие
```

- Читайте значение поля **внутри** обработчика: `input.value`.
- Пользовательский текст — только через `textContent`. `innerHTML` разбирает разметку: это путь к XSS.
- `list.children.length` — число дочерних элементов.
- События всплывают: один обработчик на `ul` может обслужить все `li` (делегирование): `event.target`.

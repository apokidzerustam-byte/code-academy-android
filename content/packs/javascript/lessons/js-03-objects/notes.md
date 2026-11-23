# JavaScript: объекты и JSON

```js
const user = { name: "Аня", age: 25, skills: ["js", "sql"] };
user.name;  user["age"];  user.city = "Краков";
Object.keys(user);  Object.values(user);  Object.entries(user);
delete user.age;  "age" in user;

const custom = { ...base, size: 16 };      // копия с изменениями (правое побеждает)
const { theme, size } = custom;            // достать поля

for (const [key, value] of Object.entries(obj)) { … }

const text = JSON.stringify(obj);          // объект → текст
const back = JSON.parse(text);             // текст → объект
try { JSON.parse(bad); } catch (e) { … }   // ошибка разбора
```

- Ключ — строка; значение — что угодно (число, массив, другой объект).
- `{ ...a, ...b }` — свойства `b` перекрывают одноимённые из `a`.
- `Object.keys(obj)` — массив имён; `Object.values(obj)` — массив значений.
- `JSON.parse` на неверном тексте бросает `SyntaxError`.

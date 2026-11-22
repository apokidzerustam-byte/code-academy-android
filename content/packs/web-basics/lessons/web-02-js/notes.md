# JavaScript: первые шаги

## Переменные и вывод
```js
let n = 1;          // можно менять
const year = 2026;  // нельзя переназначить
console.log("n =", n, `год ${year}`);
```

## Функции
```js
function square(x) {
  return x * x;      // вернуть, а не напечатать
}
const half = (x) => x / 2;   // стрелочная функция
```

## Условия и циклы
```js
if (s >= 60) { … } else { … }
for (const s of scores) { … }        // по элементам массива
for (let i = 0; i < 5; i++) { … }    // со счётчиком
```
Сравнение — `===` (строго: `"2" === 2` ложно). `"2" + 2` даёт строку `"22"`.

## Страница
```js
const btn = document.getElementById("btn");
btn.addEventListener("click", () => {
  document.getElementById("count").textContent = "…";
});
```

## Частые ошибки
- Опечатка в имени → `ReferenceError: … is not defined`.
- Функция печатает, а нужно `return`.
- Бесконечный цикл: забыли изменить счётчик. Приложение остановит его через 2 секунды.
- `=` вместо `===` в условии.

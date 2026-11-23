# JavaScript: массивы

```js
const nums = [5, 2, 8, 1];
nums.push(10);                       // добавить в конец
nums.length;  nums[0];  nums[nums.length - 1];
nums.includes(8);  nums.indexOf(8);  // true, 2
nums.slice(1, 3);                    // [2, 8] — копия куска

prices.map((p) => p * 2);                    // преобразовать каждый
prices.filter((p) => p < 20);                // оставить подходящие
prices.reduce((sum, p) => sum + p, 0);       // свернуть в одно значение

names.find((n) => n.startsWith("Б"));        // первый подходящий
names.some(f);  names.every(f);              // хотя бы один / все

[...a].sort((x, y) => x - y);                // числа: по возрастанию
```

- `sort()` без аргументов сортирует **как строки**: `[10, 9, 100]` → `[10, 100, 9]`.
- `sort` и `push` меняют массив; `map`, `filter`, `slice` создают новый.
- Копия массива: `[...arr]`.
- `reduce` без начального значения берёт первый элемент — для пустого массива это ошибка.

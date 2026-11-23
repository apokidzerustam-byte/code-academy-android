# Модули и инкапсуляция

```js
const counter = (function () {
  let count = 0;                    // закрытое состояние
  return {
    inc() { count += 1; return count; },
    value() { return count; },
  };
})();

console.log(counter.inc());         // 1
console.log(counter.count);         // undefined — снаружи не видно
```

Фабрика создаёт независимые экземпляры:

```js
function createCounter(start) {
  let count = start;
  return { inc() { count += 1; }, value() { return count; } };
}
```

ES-модули (справочно: в этом приложении `import` не выполняется):

```text
// math.js
export const PI = 3.14159;
export default function perimeter(r) { return 2 * PI * r; }

// main.js
import perimeter, { PI } from "./math.js";
import * as math from "./math.js";
```

- Модуль: **своя область видимости** + **небольшой открытый интерфейс**.
- Один модуль — одна причина измениться; зависимости явные, без круговых.
- Подключённые имена нельзя присваивать заново.
- В HTML модули подключают через `<script type="module" src="main.js">`.

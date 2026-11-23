# JavaScript: значения, строки и числа

```js
const s = "  Анна Сидорова  ".trim();
s.toUpperCase(); s.length; s.slice(0, 4); s.includes("Сидор");
s.split(" ").join("_");                    // разрезать и склеить

typeof 42;            // "number"
typeof null;          // "object" — историческая странность
Number("42") + 1;     // 43
Number("abc");        // NaN
2 === "2";            // false (строгое)
2 == "2";             // true  (нестрогое — избегайте)

`Итого: ${(12.5 * 3).toFixed(2)} zł`;      // "Итого: 37.50 zł"
0.1 + 0.2;                                 // 0.30000000000000004
```

- Сравнивайте через `===` и `!==`.
- `NaN !== NaN`: проверяйте `Number.isNaN(x)`.
- Деньги: округляйте `toFixed(2)`, не сравнивайте дроби на равенство.
- `user.name.length` при отсутствии `name` — `TypeError`.

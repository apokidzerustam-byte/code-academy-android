# Kotlin: коллекции и лямбды

```kotlin
fun main() {
    val nums = listOf(5, 3, 8, 1)
    println(nums.sorted())            // [1, 3, 5, 8]
    println(nums.map { it * 10 })     // [50, 30, 80, 10]
    println(nums.filter { it > 2 })   // [5, 3, 8]
    println(nums.sum())               // 17

    val cart = mutableListOf("хлеб")
    cart.add("молоко")
    cart.remove("хлеб")
    println(cart)                     // [молоко]

    val ages = mutableMapOf("Аня" to 20)
    ages["Борис"] = 25
    println(ages["Вера"])             // null — такого ключа нет
}
```

## Лямбды
```kotlin
fun repeatAction(times: Int, action: (Int) -> Unit) {
    for (i in 1..times) action(i)
}

fun main() {
    val double = { x: Int -> x * 2 }
    println(double(21))
    repeatAction(3) { n -> println("Шаг $n") }
}
```

| Вид | Создать | Менять |
|---|---|---|
| список | `listOf(…)` | `mutableListOf(…)` |
| множество | `setOf(…)` | `mutableSetOf(…)` |
| словарь | `mapOf("a" to 1)` | `mutableMapOf("a" to 1)` |

- `it` — имя единственного параметра лямбды.
- `m[ключ]` для словаря возвращает значение или `null`.
- Лямбду, которая стоит последней среди аргументов, выносят за круглые скобки.
- В Compose действие кнопки — лямбда: `Button(onClick = { … })`.

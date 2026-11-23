# Kotlin: классы и null

```kotlin
class Account(val owner: String, var balance: Int) {
    fun deposit(amount: Int) {
        balance += amount
    }

    fun describe(): String = "$owner: $balance"
}

fun safeLength(text: String?): Int {
    return text?.length ?: 0
}

fun label(x: Int?): String {
    if (x == null) return "пусто"
    return "значение ${x + 1}"     // здесь x уже точно не null
}

fun main() {
    val acc = Account("Аня", 100)
    acc.deposit(50)
    println(acc.describe())
    println(safeLength(null))
    println(label(4))
}
```

| Запись | Смысл |
|---|---|
| `class A(val x: Int, var y: Int)` | свойства в главном конструкторе |
| `String?` | строка или `null` |
| `a?.length` | длина, а если `a` равно `null` — `null` |
| `a ?: "запас"` | `a`, а если `null` — запасное значение |
| `a!!` | «точно не null» — роняет программу, если это не так |

Запускается программа в GitHub Actions (проект Kotlin в разделе «Проекты»); на телефоне проверяются синтаксис
и структура кода.

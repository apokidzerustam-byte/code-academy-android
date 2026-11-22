# Kotlin: первые шаги

```kotlin
fun main() {
    val name = "Аня"     // нельзя изменить
    var age = 20         // можно изменить
    age += 1
    println("$name, $age, ${age * 2}")
}
```

## Функции
```kotlin
fun square(x: Int): Int {
    return x * x
}

fun half(x: Double): Double = x / 2   // функция-выражение

fun main() {
    println(square(3))
    println(half(5.0))
}
```

## when и циклы
```kotlin
fun grade(score: Int): String = when {
    score >= 90 -> "отлично"
    score >= 60 -> "зачёт"
    else -> "незачёт"
}

fun main() {
    for (i in 1..3) println(grade(i * 40))
}
```

## data class и списки
```kotlin
data class Book(val title: String, val year: Int)

fun main() {
    val books = listOf(Book("Онегин", 1833), Book("Мастер", 1967))
    println(books.filter { it.year < 1900 })
}
```

## Типы
`Int` — целое, `Double` — дробное, `String` — строка, `Boolean` — да/нет, `List<Book>` — список книг.

## Как проверяется на телефоне
Компилятора Kotlin в телефоне нет. Задания проверяют синтаксис, имена и типы функций и классов
и нужные конструкции. Запустить программу — проект Kotlin в разделе «Проекты» (файл README.md) и GitHub Actions.

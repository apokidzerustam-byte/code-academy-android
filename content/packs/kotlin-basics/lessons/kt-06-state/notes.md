# Kotlin: состояние и события в Compose

Интерфейс — функция от состояния. Изменили состояние — Compose заново вызывает функции, которые его читают.

```kotlin
@Composable
fun Counter() {
    var count by remember { mutableIntStateOf(0) }   // состояние, переживающее перерисовку
    Column {
        Text("Счёт: $count")
        Button(onClick = { count++ }) { Text("+1") }
    }
}
```

Нужны импорты `getValue`, `setValue`, `remember`, `mutableIntStateOf` из `androidx.compose.runtime`.

## Подъём состояния

```kotlin
@Composable
fun CounterView(count: Int, onIncrement: () -> Unit) {   // без состояния
    Column {
        Text("Счёт: $count")
        Button(onClick = onIncrement) { Text("+1") }
    }
}

@Composable
fun CounterScreen() {                                     // владелец состояния
    var count by remember { mutableIntStateOf(0) }
    CounterView(count = count, onIncrement = { count++ })
}
```

**Состояние течёт вниз, события — вверх.** Функцию без состояния легко повторно использовать и проверять.

## Неизменяемое состояние

```kotlin
data class TaskUi(val title: String, val done: Boolean)
val updated = task.copy(done = true)      // новая копия, старая не меняется
```

- Обычная переменная вместо состояния не обновит экран.
- `mutableStateOf` без `remember` сбрасывается при каждой перерисовке.
- Меняйте объекты копией (`copy`), а не правкой полей на месте.
- **Ограничение проверки:** упрощённая модель Compose в CI не делает перерисовок: проверяется построенное дерево элементов и вызовы `onClick`. Поведение `remember` в проверке не моделируется, его правила закреплены структурными правилами заданий.

# Kotlin: ViewModel и StateFlow

ViewModel хранит состояние экрана и логику его изменения. Она переживает поворот экрана и не знает про кнопки и текст.

```kotlin
class CounterViewModel : ViewModel() {
    private val _count = MutableStateFlow(0)               // изменяемое — приватно
    val count: StateFlow<Int> = _count.asStateFlow()       // наружу — только чтение

    fun increment() {
        _count.value += 1
    }
}
```

Сложное состояние — класс данных; меняют его через `update` и `copy`:

```kotlin
data class TasksUiState(val tasks: List<String> = emptyList(), val loading: Boolean = false)

_state.update { it.copy(tasks = it.tasks + title) }
```

Экран подписывается и посылает события:

```kotlin
@Composable
fun CounterScreen(viewModel: CounterViewModel) {
    val count by viewModel.count.collectAsState()
    Column {
        Text("Счёт: $count")
        Button(onClick = { viewModel.increment() }) { Text("+1") }
    }
}
```

**Поток данных:** состояние → экран → событие → ViewModel → новое состояние.

- Не отдавайте наружу `MutableStateFlow`; не читайте `.value` в функции интерфейса — экран не обновится.
- Не меняйте списки на месте: создавайте копию.
- Не храните во ViewModel ссылки на экран.
- **Ограничение проверки:** заглушки в CI выполняют код последовательно: потоков, подписок и перерисовок нет, `collectAsState` просто читает текущее значение. Правила настоящего Compose закреплены структурными проверками заданий. В приложении на телефоне этот код не запускается.

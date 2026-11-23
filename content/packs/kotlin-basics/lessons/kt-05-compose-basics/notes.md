# Kotlin: основы Jetpack Compose

Интерфейс в Compose — обычные функции Kotlin с аннотацией `@Composable`. Вы описываете, что показать для данных; система перерисует экран при изменении данных.

```kotlin
@Composable
fun Greeting(name: String) {
    Text("Привет, $name!")
}

@Composable
fun ProfileCard(name: String, role: String) {
    Column(modifier = Modifier.padding(16.dp)) {
        Text(name)
        Row {
            Text("Роль: ")
            Text(role)
        }
    }
}
```

| Элемент | Назначение |
|---|---|
| `@Composable` | функция описывает кусок интерфейса; имя с большой буквы |
| `Text(строка)` | показывает текст |
| `Column { … }` / `Row { … }` | дети сверху вниз / слева направо |
| `Modifier.padding(16.dp)` | отступ; `dp` — единица, не зависящая от плотности экрана |
| `Button(onClick = { … }) { Text("…") }` | кнопка с содержимым |
| `LazyColumn { items(список) { … } }` | прокручиваемый список; рисует только видимое |

Состояние, которое меняет картинку:

```kotlin
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue

var count by remember { mutableIntStateOf(0) }
Button(onClick = { count++ }) { Text("Ещё") }
```

- Обычная переменная вместо `remember { mutableStateOf(…) }` не обновит экран.
- Внутри `LazyColumn` нельзя вызывать `Text` напрямую и писать `for`: используйте `items(список) { элемент -> … }`.
- Для `by` нужны импорты `getValue` и `setValue`.
- **Ограничение проверки:** задания проверяются на компьютере по упрощённым заглушкам Compose (они строят текстовое дерево элементов и не знают про перерисовку). Правила настоящего компилятора Compose (например, «`Text` вне `@Composable`») проверяются структурными правилами. На телефоне в приложении этот код не запускается.

package androidx.compose.runtime

import kotlinx.coroutines.flow.StateFlow

/** Заглушка: настоящая функция подписывается на поток и перерисовывает экран; здесь возвращается текущее значение при каждом чтении. */
fun <T> StateFlow<T>.collectAsState(): State<T> {
    val flow = this
    return object : State<T> {
        override val value: T get() = flow.value
    }
}

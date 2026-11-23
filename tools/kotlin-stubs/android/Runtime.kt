package androidx.compose.runtime

import kotlin.reflect.KProperty

/** Заглушка для проверки учебного кода в CI (не настоящий Compose): аннотация без компилятора Compose. */
@Target(AnnotationTarget.FUNCTION, AnnotationTarget.TYPE, AnnotationTarget.PROPERTY_GETTER)
annotation class Composable

interface State<out T> {
    val value: T
}

interface MutableState<T> : State<T> {
    override var value: T
}

private class StateImpl<T>(override var value: T) : MutableState<T>

fun <T> mutableStateOf(value: T): MutableState<T> = StateImpl(value)

fun mutableIntStateOf(value: Int): MutableState<Int> = StateImpl(value)

/** Модель «один проход»: значение не запоминается между вызовами, перекомпозиции нет. */
fun <T> remember(calculation: () -> T): T = calculation()

operator fun <T> State<T>.getValue(thisObj: Any?, property: KProperty<*>): T = value

operator fun <T> MutableState<T>.setValue(thisObj: Any?, property: KProperty<*>, newValue: T) {
    value = newValue
}

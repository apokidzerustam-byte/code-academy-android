package kotlinx.coroutines.flow

interface Flow<out T>

interface StateFlow<out T> : Flow<T> {
    val value: T
}

interface MutableStateFlow<T> : StateFlow<T> {
    override var value: T
}

private class MutableStateFlowImpl<T>(override var value: T) : MutableStateFlow<T>

fun <T> MutableStateFlow(value: T): MutableStateFlow<T> = MutableStateFlowImpl(value)

fun <T> MutableStateFlow<T>.asStateFlow(): StateFlow<T> = this

fun <T> MutableStateFlow<T>.update(function: (T) -> T) {
    value = function(value)
}

package kotlinx.coroutines

import kotlin.coroutines.Continuation
import kotlin.coroutines.CoroutineContext
import kotlin.coroutines.EmptyCoroutineContext
import kotlin.coroutines.startCoroutine

/** Заглушка корутин для проверки в CI: всё выполняется последовательно, delay ничего не ждёт. */
interface CoroutineScope

private object StubScope : CoroutineScope

interface Job {
    suspend fun join()
}

interface Deferred<out T> : Job {
    suspend fun await(): T
}

object Dispatchers {
    val Main: CoroutineContext = EmptyCoroutineContext
    val IO: CoroutineContext = EmptyCoroutineContext
    val Default: CoroutineContext = EmptyCoroutineContext
}

private class DoneJob<T>(private val outcome: Result<T>) : Deferred<T> {
    override suspend fun join() {}
    override suspend fun await(): T = outcome.getOrThrow()
}

private fun <T> execute(block: suspend CoroutineScope.() -> T): Result<T> {
    var outcome: Result<T>? = null
    block.startCoroutine(StubScope, Continuation(EmptyCoroutineContext) { outcome = it })
    return outcome!!
}

fun <T> runBlocking(block: suspend CoroutineScope.() -> T): T = execute(block).getOrThrow()

fun CoroutineScope.launch(context: CoroutineContext = EmptyCoroutineContext, block: suspend CoroutineScope.() -> Unit): Job =
    DoneJob(execute(block))

fun <T> CoroutineScope.async(context: CoroutineContext = EmptyCoroutineContext, block: suspend CoroutineScope.() -> T): Deferred<T> =
    DoneJob(execute(block))

suspend fun delay(timeMillis: Long) {}

suspend fun <T> withContext(context: CoroutineContext, block: suspend CoroutineScope.() -> T): T = StubScope.block()

suspend fun <T> coroutineScope(block: suspend CoroutineScope.() -> T): T = StubScope.block()

package androidx.lifecycle

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.StubScopes

abstract class ViewModel

/** Заглушка: настоящая область отменяется вместе с ViewModel, здесь корутины просто выполняются последовательно. */
val ViewModel.viewModelScope: CoroutineScope
    get() = StubScopes.shared

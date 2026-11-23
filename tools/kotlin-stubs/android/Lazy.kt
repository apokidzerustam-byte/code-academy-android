package androidx.compose.foundation.lazy

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import stubs.ComposeLog

interface LazyListScope
interface LazyItemScope

private object LazyListScopeImpl : LazyListScope
private object LazyItemScopeImpl : LazyItemScope

fun <T> LazyListScope.items(items: List<T>, itemContent: @Composable LazyItemScope.(T) -> Unit) {
    for (item in items) LazyItemScopeImpl.itemContent(item)
}

@Composable
fun LazyColumn(modifier: Modifier = Modifier, content: LazyListScope.() -> Unit) {
    ComposeLog.add("LazyColumn")
    ComposeLog.nested { LazyListScopeImpl.content() }
}

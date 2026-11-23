package androidx.compose.foundation.layout

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.Dp
import stubs.ComposeLog

interface ColumnScope
interface RowScope

private object ColumnScopeImpl : ColumnScope
private object RowScopeImpl : RowScope

fun Modifier.padding(all: Dp): Modifier = this

fun Modifier.fillMaxWidth(): Modifier = this

@Composable
fun Column(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    ComposeLog.add("Column")
    ComposeLog.nested { ColumnScopeImpl.content() }
}

@Composable
fun Row(modifier: Modifier = Modifier, content: @Composable RowScope.() -> Unit) {
    ComposeLog.add("Row")
    ComposeLog.nested { RowScopeImpl.content() }
}

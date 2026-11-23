package androidx.compose.material3

import androidx.compose.foundation.layout.RowScope
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import stubs.ComposeLog

@Composable
fun Text(text: String, modifier: Modifier = Modifier) {
    ComposeLog.add("Text($text)")
}

private object ButtonScope : RowScope

@Composable
fun Button(onClick: () -> Unit, modifier: Modifier = Modifier, content: @Composable RowScope.() -> Unit) {
    ComposeLog.clicks.add(onClick)
    ComposeLog.add("Button")
    ComposeLog.nested { ButtonScope.content() }
}

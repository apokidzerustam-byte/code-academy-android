package androidx.compose.ui.unit

data class Dp(val value: Float)

val Int.dp: Dp
    get() = Dp(this.toFloat())

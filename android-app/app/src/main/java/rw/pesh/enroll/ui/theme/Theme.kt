package rw.pesh.enroll.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColors = lightColorScheme(
    primary = PeshNavy,
    secondary = PeshBlue,
    tertiary = PeshGold,
    background = PeshBackground,
)

private val DarkColors = darkColorScheme(
    primary = PeshBlue,
    secondary = PeshGold,
)

@Composable
fun PeshTheme(content: @Composable () -> Unit) {
    val colors = if (isSystemInDarkTheme()) DarkColors else LightColors
    MaterialTheme(colorScheme = colors, typography = MaterialTheme.typography, content = content)
}

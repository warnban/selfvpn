package site.daddyvpn.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val DarkScheme = darkColorScheme(
    background = DaddyColors.Background,
    onBackground = DaddyColors.Foreground,
    surface = DaddyColors.Card,
    onSurface = DaddyColors.Foreground,
    primary = DaddyColors.Primary,
    onPrimary = DaddyColors.PrimaryForeground,
    secondary = DaddyColors.Secondary,
    onSecondary = DaddyColors.SecondaryForeground,
    error = DaddyColors.Danger,
)

@Composable
fun DaddyVpnTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkScheme,
        content = content,
    )
}

object DaddyTypography {
    val DisplayTimer = TextStyle(
        fontFamily = FontFamily.Monospace,
        fontSize = 42.sp,
        fontWeight = FontWeight.Medium,
        letterSpacing = 3.sp,
        lineHeight = 42.sp,
    )
    val BrandTitle = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontSize = 22.sp,
        fontWeight = FontWeight.Bold,
        letterSpacing = 2.6.sp,
    )
    val LabelCaps = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontSize = 11.sp,
        fontWeight = FontWeight.SemiBold,
        letterSpacing = 1.3.sp,
    )
    val StatValue = TextStyle(
        fontFamily = FontFamily.Monospace,
        fontSize = 26.sp,
        fontWeight = FontWeight.Medium,
        lineHeight = 26.sp,
    )
}

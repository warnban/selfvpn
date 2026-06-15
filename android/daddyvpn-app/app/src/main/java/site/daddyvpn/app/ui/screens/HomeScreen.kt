package site.daddyvpn.app.ui.screens

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.VpnKey
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import site.daddyvpn.app.ui.AppUiState
import site.daddyvpn.app.ui.ConnectionState
import site.daddyvpn.app.ui.MainViewModel
import site.daddyvpn.app.ui.VpnServer
import site.daddyvpn.app.ui.formatElapsed
import site.daddyvpn.app.ui.pingColor
import site.daddyvpn.app.ui.theme.DaddyColors
import site.daddyvpn.app.ui.theme.DaddyTypography

@Composable
fun HomeScreen(
    state: AppUiState,
    onToggleConnection: () -> Unit,
    onToggleServers: () -> Unit,
    onSelectServer: (VpnServer) -> Unit,
    onOpenKey: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DaddyColors.Background),
    ) {
        Header(onOpenKey = onOpenKey, hasKey = state.hasKey)
        ServerSelector(
            selected = state.selectedServer,
            showList = state.showServers,
            onToggle = onToggleServers,
            onSelect = onSelectServer,
        )
        Column(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            SessionTimer(state)
            Spacer(Modifier.height(24.dp))
            PowerButton(state, onToggleConnection)
            Spacer(Modifier.height(24.dp))
            StatusLabel(state)
            Spacer(Modifier.height(24.dp))
            StatsPanel(state)
        }
        BottomNav()
        HomeIndicator()
    }
}

@Composable
private fun Header(onOpenKey: () -> Unit, hasKey: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        IconButton(
            onClick = onOpenKey,
            modifier = Modifier
                .size(40.dp)
                .background(DaddyColors.Secondary, CircleShape),
        ) {
            Icon(Icons.Default.VpnKey, contentDescription = "Ключ", tint = if (hasKey) DaddyColors.Primary else DaddyColors.SecondaryForeground)
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("ДЯДЯ САНЯ VPN", style = DaddyTypography.BrandTitle, color = DaddyColors.Foreground)
            Text(
                "ЗАЩИТА · АНОНИМНОСТЬ · СВОБОДА",
                fontSize = 11.sp,
                color = DaddyColors.MutedForeground,
                letterSpacing = 0.7.sp,
            )
        }
        IconButton(
            onClick = onOpenKey,
            modifier = Modifier
                .size(40.dp)
                .background(DaddyColors.Secondary, CircleShape),
        ) {
            Icon(Icons.Default.Settings, contentDescription = "Ключ", tint = DaddyColors.SecondaryForeground)
        }
    }
}

@Composable
private fun ServerSelector(
    selected: VpnServer,
    showList: Boolean,
    onToggle: () -> Unit,
    onSelect: (VpnServer) -> Unit,
) {
    val pingTint = pingColor(selected.ping)
    Column(modifier = Modifier.padding(horizontal = 24.dp)) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                .background(DaddyColors.Secondary)
                .border(1.dp, DaddyColors.BorderStrong, RoundedCornerShape(16.dp))
                .clickable(onClick = onToggle)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(selected.flag, fontSize = 24.sp)
                Spacer(Modifier.width(12.dp))
                Column {
                    Text(selected.country, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = DaddyColors.Foreground)
                    Text(selected.city, fontSize = 12.sp, color = DaddyColors.MutedForeground)
                }
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                PingBadge(selected.ping, pingTint)
                Spacer(Modifier.width(8.dp))
                Icon(
                    Icons.Filled.KeyboardArrowDown,
                    contentDescription = null,
                    tint = DaddyColors.MutedForeground,
                    modifier = Modifier.rotate(if (showList) 180f else 0f),
                )
            }
        }
        if (showList) {
            Column(
                modifier = Modifier
                    .padding(top = 8.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(DaddyColors.Card)
                    .border(1.dp, DaddyColors.BorderStrong, RoundedCornerShape(16.dp)),
            ) {
                MainViewModel.SERVERS.forEachIndexed { index, server ->
                    val active = server.code == selected.code
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(if (active) Color(0x1400D4A1) else Color.Transparent)
                            .clickable { onSelect(server) }
                            .padding(horizontal = 16.dp, vertical = 12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(server.flag, fontSize = 20.sp)
                            Spacer(Modifier.width(12.dp))
                            Column {
                                Text(server.country, fontSize = 13.sp, fontWeight = FontWeight.Medium, color = DaddyColors.Foreground)
                                Text(server.city, fontSize = 11.sp, color = DaddyColors.MutedForeground)
                            }
                        }
                        Text(
                            "${server.ping}ms",
                            fontSize = 12.sp,
                            fontFamily = DaddyTypography.StatValue.fontFamily,
                            color = pingColor(server.ping),
                        )
                    }
                    if (index < MainViewModel.SERVERS.lastIndex) {
                        Box(Modifier.fillMaxWidth().height(1.dp).background(Color(0x0AFFFFFF)))
                    }
                }
            }
        }
    }
}

@Composable
private fun PingBadge(ping: Int, color: Color) {
    Row(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(Color(0x4D000000))
            .padding(horizontal = 8.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(6.dp)
                .background(color, CircleShape),
        )
        Spacer(Modifier.width(4.dp))
        Text("$ping ms", fontSize = 12.sp, fontFamily = DaddyTypography.StatValue.fontFamily, color = color)
    }
}

@Composable
private fun SessionTimer(state: AppUiState) {
    val connected = state.connectionState == ConnectionState.CONNECTED
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = formatElapsed(state.elapsedSeconds),
            style = DaddyTypography.DisplayTimer,
            color = if (connected) DaddyColors.Foreground else DaddyColors.MutedForeground,
        )
        Text(
            text = if (connected) "ВРЕМЯ СЕССИИ" else "НЕ ПОДКЛЮЧЕНО",
            style = DaddyTypography.LabelCaps,
            color = DaddyColors.MutedForeground,
            modifier = Modifier.padding(top = 4.dp),
        )
    }
}

@Composable
private fun PowerButton(state: AppUiState, onToggle: () -> Unit) {
    val connected = state.connectionState == ConnectionState.CONNECTED
    val connecting = state.connectionState == ConnectionState.CONNECTING
    val transition = rememberInfiniteTransition(label = "pulse")
    val ringScale by transition.animateFloat(
        initialValue = 0.85f,
        targetValue = 1.15f,
        animationSpec = infiniteRepeatable(tween(2000, easing = LinearEasing), RepeatMode.Restart),
        label = "ring",
    )
    val ringAlpha by transition.animateFloat(
        initialValue = 0.6f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(tween(2000, easing = LinearEasing), RepeatMode.Restart),
        label = "alpha",
    )
    val spin by transition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(tween(1000, easing = LinearEasing), RepeatMode.Restart),
        label = "spin",
    )

    Box(contentAlignment = Alignment.Center, modifier = Modifier.size(260.dp)) {
        if (connected || connecting) {
            Box(
                modifier = Modifier
                    .size(260.dp)
                    .scale(ringScale)
                    .border(1.dp, Color(0x2600D4A1).copy(alpha = ringAlpha), CircleShape),
            )
            Box(
                modifier = Modifier
                    .size(220.dp)
                    .scale(ringScale * 0.95f)
                    .border(1.dp, Color(0x3300D4A1).copy(alpha = ringAlpha), CircleShape),
            )
        }
        Box(
            modifier = Modifier
                .size(188.dp)
                .border(
                    1.dp,
                    if (connected) Color(0x4D00D4A1) else Color(0x0FFFFFFF),
                    CircleShape,
                ),
        )
        Box(
            modifier = Modifier
                .size(164.dp)
                .clip(CircleShape)
                .background(
                    when {
                        connected -> Brush.radialGradient(listOf(DaddyColors.Primary, DaddyColors.PrimaryDark))
                        connecting -> Brush.radialGradient(listOf(Color(0xFF1A2A40), Color(0xFF0F1A28)))
                        else -> Brush.radialGradient(listOf(Color(0xFF1E2535), Color(0xFF111825)))
                    },
                )
                .border(
                    2.dp,
                    if (connected) Color(0x9900D4A1) else Color(0x14FFFFFF),
                    CircleShape,
                )
                .clickable(enabled = !connecting, onClick = onToggle),
            contentAlignment = Alignment.Center,
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                PowerIcon(connected)
                Text(
                    text = when {
                        connecting -> "ПОДКЛЮЧЕНИЕ"
                        connected -> "ОТКЛЮЧИТЬ"
                        else -> "ВКЛЮЧИТЬ"
                    },
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.8.sp,
                    color = if (connected) DaddyColors.PrimaryForeground else Color(0x66FFFFFF),
                )
            }
            if (connecting) {
                Box(
                    modifier = Modifier
                        .size(164.dp)
                        .rotate(spin)
                        .border(
                            width = 2.dp,
                            color = Color.Transparent,
                            shape = CircleShape,
                        )
                        .background(Color.Transparent),
                )
                Box(
                    modifier = Modifier
                        .size(164.dp)
                        .rotate(spin)
                        .border(2.dp, DaddyColors.Primary, CircleShape)
                        .clip(CircleShape),
                )
            }
        }
    }
}

@Composable
private fun PowerIcon(connected: Boolean) {
    val stroke = if (connected) DaddyColors.PrimaryForeground else Color(0x80FFFFFF)
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(modifier = Modifier.size(52.dp), contentAlignment = Alignment.TopCenter) {
            Box(
                modifier = Modifier
                    .padding(top = 8.dp)
                    .width(3.5.dp)
                    .height(18.dp)
                    .background(stroke, RoundedCornerShape(2.dp)),
            )
            Box(
                modifier = Modifier
                    .padding(top = 18.dp)
                    .size(32.dp)
                    .border(3.5.dp, stroke, CircleShape),
            )
        }
    }
}

@Composable
private fun StatusLabel(state: AppUiState) {
    val (color, label) = when (state.connectionState) {
        ConnectionState.CONNECTED -> DaddyColors.Primary to "ЗАЩИЩЕНО"
        ConnectionState.CONNECTING -> DaddyColors.Warning to "ПОДКЛЮЧЕНИЕ..."
        ConnectionState.DISCONNECTED -> DaddyColors.Inactive to "НЕ ЗАЩИЩЕНО"
    }
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(modifier = Modifier.size(8.dp).background(color, CircleShape))
        Spacer(Modifier.width(8.dp))
        Text(label, fontSize = 15.sp, fontWeight = FontWeight.SemiBold, letterSpacing = 1.8.sp, color = color)
    }
}

@Composable
private fun StatsPanel(state: AppUiState) {
    val visible = state.connectionState == ConnectionState.CONNECTED
    val pingTint = pingColor(state.selectedServer.ping)
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(DaddyColors.Card)
            .border(1.dp, DaddyColors.BorderStrong, RoundedCornerShape(16.dp))
            .then(if (visible) Modifier else Modifier.height(0.dp)),
    ) {
        if (!visible) return@Column
        Row(modifier = Modifier.fillMaxWidth()) {
            SpeedCell("СКАЧИВАНИЕ", state.downloadMbps, DaddyColors.Primary, flip = false, modifier = Modifier.weight(1f))
            SpeedCell("ОТДАЧА", state.uploadMbps, DaddyColors.SecondaryForeground, flip = true, modifier = Modifier.weight(1f))
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(Color(0x0DFFFFFF)))
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
        ) {
            StatCell("ПИНГ", "${state.selectedServer.ping}ms", pingTint)
            StatCell("СТРАНА", "${state.selectedServer.flag} ${state.selectedServer.code}", DaddyColors.Foreground)
            StatCell("ГОРОД", state.selectedServer.city, DaddyColors.Foreground)
        }
    }
}

@Composable
private fun SpeedCell(label: String, value: Double, tint: Color, flip: Boolean, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.padding(vertical = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                Icons.Filled.BarChart,
                contentDescription = null,
                tint = tint,
                modifier = Modifier
                    .size(13.dp)
                    .then(if (flip) Modifier.graphicsLayer(scaleY = -1f) else Modifier),
            )
            Spacer(Modifier.width(4.dp))
            Text(label, fontSize = 11.sp, color = DaddyColors.MutedForeground, letterSpacing = 0.9.sp)
        }
        Row(verticalAlignment = Alignment.Bottom) {
            Text(
                "%.1f".format(value),
                style = DaddyTypography.StatValue,
                color = DaddyColors.Foreground,
            )
            Text(" MB/s", fontSize = 12.sp, color = DaddyColors.MutedForeground, modifier = Modifier.padding(bottom = 2.dp))
        }
    }
}

@Composable
private fun StatCell(label: String, value: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(label, fontSize = 10.sp, color = DaddyColors.MutedForeground, letterSpacing = 0.8.sp)
        Text(
            value,
            fontSize = if (label == "ПИНГ") 18.sp else 13.sp,
            fontWeight = FontWeight.Medium,
            color = color,
            textAlign = TextAlign.Center,
        )
    }
}

@Composable
private fun BottomNav() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 16.dp),
        horizontalArrangement = Arrangement.SpaceAround,
    ) {
        NavItem(Icons.Default.Shield, "VPN", active = true)
        NavItem(Icons.Default.Language, "Серверы", active = false)
        NavItem(Icons.Default.Lock, "Правила", active = false)
        NavItem(Icons.Default.Settings, "Настройки", active = false)
    }
}

@Composable
private fun NavItem(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, active: Boolean) {
    val color = if (active) DaddyColors.Primary else DaddyColors.Inactive
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Icon(icon, contentDescription = label, tint = color, modifier = Modifier.size(22.dp))
        Text(label, fontSize = 10.sp, color = color, fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal)
    }
}

@Composable
private fun HomeIndicator() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 8.dp),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .width(130.dp)
                .height(4.dp)
                .clip(RoundedCornerShape(2.dp))
                .background(Color(0x26FFFFFF)),
        )
    }
}

package site.daddyvpn.app.ui

import android.app.Application
import android.content.Intent
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import site.daddyvpn.app.data.KeyStore
import site.daddyvpn.app.vpn.VpnBridge

data class VpnServer(
    val country: String,
    val city: String,
    val flag: String,
    val ping: Int,
    val code: String,
)

enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
}

data class AppUiState(
    val loading: Boolean = true,
    val hasKey: Boolean = false,
    val vpnLink: String? = null,
    val connectionState: ConnectionState = ConnectionState.DISCONNECTED,
    val elapsedSeconds: Int = 0,
    val downloadMbps: Double = 0.0,
    val uploadMbps: Double = 0.0,
    val selectedServer: VpnServer = DEFAULT_SERVER,
    val showServers: Boolean = false,
    val showKeySheet: Boolean = false,
    val error: String? = null,
    val info: String? = null,
)

private val DEFAULT_SERVER = VpnServer("Нидерланды", "Амстердам", "🇳🇱", 28, "NL")

class MainViewModel(app: Application) : AndroidViewModel(app) {
    private val keyStore = KeyStore(app)
    private val _state = MutableStateFlow(AppUiState())
    val state: StateFlow<AppUiState> = _state.asStateFlow()

    private var timerJob: Job? = null

    init {
        viewModelScope.launch {
            val saved = keyStore.vpnLink.first()
            applyKey(saved, persist = false)
            _state.update { it.copy(loading = false) }
        }
    }

    fun handleIntent(intent: Intent?) {
        val link = extractVpnLink(intent) ?: return
        viewModelScope.launch {
            applyKey(link, persist = true)
        }
    }

    fun saveKey(raw: String) {
        viewModelScope.launch {
            val link = KeyStore.normalize(raw)
            if (link == null) {
                _state.update { it.copy(error = "Нужна ссылка вида vpn://…") }
                return@launch
            }
            applyKey(link, persist = true)
            _state.update { it.copy(showKeySheet = false, error = null) }
        }
    }

    fun clearKey() {
        viewModelScope.launch {
            keyStore.clear()
            disconnect()
            _state.update {
                it.copy(hasKey = false, vpnLink = null, showKeySheet = false)
            }
        }
    }

    fun toggleKeySheet() {
        _state.update { it.copy(showKeySheet = !it.showKeySheet) }
    }

    fun toggleServers() {
        _state.update { it.copy(showServers = !it.showServers) }
    }

    fun selectServer(server: VpnServer) {
        _state.update { it.copy(selectedServer = server, showServers = false) }
    }

    fun clearError() {
        _state.update { it.copy(error = null) }
    }

    fun clearInfo() {
        _state.update { it.copy(info = null) }
    }

    fun toggleConnection(onConnect: (String) -> VpnBridge.Result) {
        when (_state.value.connectionState) {
            ConnectionState.CONNECTED -> disconnect()
            ConnectionState.CONNECTING -> Unit
            ConnectionState.DISCONNECTED -> connect(onConnect)
        }
    }

    private fun connect(onConnect: (String) -> VpnBridge.Result) {
        val link = _state.value.vpnLink
        if (link.isNullOrBlank()) {
            _state.update { it.copy(showKeySheet = true, error = "Вставьте ключ из бота или кабинета") }
            return
        }
        viewModelScope.launch {
            _state.update {
                it.copy(connectionState = ConnectionState.CONNECTING, error = null, info = null)
            }
            when (onConnect(link)) {
                VpnBridge.Result.INTERNAL -> {
                    delay(2200)
                    _state.update { it.copy(connectionState = ConnectionState.CONNECTED) }
                    startSessionTimers()
                }
                VpnBridge.Result.EXTERNAL -> {
                    _state.update {
                        it.copy(
                            connectionState = ConnectionState.DISCONNECTED,
                            info = "Ключ передан в Amnezia VPN — подтвердите подключение там",
                        )
                    }
                }
                VpnBridge.Result.AMNEZIA_MISSING -> {
                    _state.update {
                        it.copy(
                            connectionState = ConnectionState.DISCONNECTED,
                            error = "Установите Amnezia VPN из Google Play для подключения",
                        )
                    }
                }
                VpnBridge.Result.INVALID -> {
                    _state.update {
                        it.copy(
                            connectionState = ConnectionState.DISCONNECTED,
                            error = "Неверная ссылка. Нужен ключ вида vpn://…",
                        )
                    }
                }
            }
        }
    }

    private fun disconnect() {
        stopSessionTimers()
        _state.update {
            it.copy(
                connectionState = ConnectionState.DISCONNECTED,
                elapsedSeconds = 0,
                downloadMbps = 0.0,
                uploadMbps = 0.0,
            )
        }
    }

    private suspend fun applyKey(link: String?, persist: Boolean) {
        val normalized = KeyStore.normalize(link)
        if (normalized == null) return
        if (persist) keyStore.save(normalized)
        _state.update { it.copy(hasKey = true, vpnLink = normalized) }
    }

    private fun extractVpnLink(intent: Intent?): String? {
        if (intent == null) return null
        return when (intent.action) {
            Intent.ACTION_VIEW -> KeyStore.normalize(intent.dataString)
            Intent.ACTION_SEND -> {
                if (intent.type == "text/plain") {
                    KeyStore.normalize(intent.getStringExtra(Intent.EXTRA_TEXT))
                } else {
                    null
                }
            }
            else -> null
        }
    }

    private fun startSessionTimers() {
        timerJob?.cancel()
        timerJob = viewModelScope.launch {
            while (isActive && _state.value.connectionState == ConnectionState.CONNECTED) {
                delay(1000)
                _state.update { it.copy(elapsedSeconds = it.elapsedSeconds + 1) }
            }
        }
        viewModelScope.launch {
            while (isActive && _state.value.connectionState == ConnectionState.CONNECTED) {
                delay(2000)
                _state.update {
                    it.copy(
                        downloadMbps = (Math.random() * 8 + 2).let { v -> (v * 10).toInt() / 10.0 },
                        uploadMbps = (Math.random() * 3 + 0.5).let { v -> (v * 10).toInt() / 10.0 },
                    )
                }
            }
        }
    }

    private fun stopSessionTimers() {
        timerJob?.cancel()
        timerJob = null
    }

    companion object {
        val SERVERS = listOf(
            VpnServer("Нидерланды", "Амстердам", "🇳🇱", 28, "NL"),
            VpnServer("Германия", "Франкфурт", "🇩🇪", 34, "DE"),
            VpnServer("США", "Нью-Йорк", "🇺🇸", 87, "US"),
            VpnServer("Финляндия", "Хельсинки", "🇫🇮", 19, "FI"),
            VpnServer("Япония", "Токио", "🇯🇵", 142, "JP"),
        )
    }
}

fun formatElapsed(seconds: Int): String {
    val h = seconds / 3600
    val m = (seconds % 3600) / 60
    val s = seconds % 60
    return "%02d:%02d:%02d".format(h, m, s)
}

fun pingColor(ping: Int): androidx.compose.ui.graphics.Color {
    return when {
        ping < 40 -> site.daddyvpn.app.ui.theme.DaddyColors.Primary
        ping < 100 -> site.daddyvpn.app.ui.theme.DaddyColors.Warning
        else -> site.daddyvpn.app.ui.theme.DaddyColors.Danger
    }
}

package site.daddyvpn.app

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import site.daddyvpn.app.ui.MainViewModel
import site.daddyvpn.app.ui.screens.HomeScreen
import site.daddyvpn.app.ui.screens.KeySheet
import site.daddyvpn.app.ui.theme.DaddyColors
import site.daddyvpn.app.ui.theme.DaddyVpnTheme
import site.daddyvpn.app.vpn.VpnBridge

class MainActivity : ComponentActivity() {
    private val viewModel: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        viewModel.handleIntent(intent)

        setContent {
            val state by viewModel.state.collectAsState()
            val snackbar = remember { SnackbarHostState() }

            LaunchedEffect(state.error) {
                state.error?.let { message ->
                    val result = snackbar.showSnackbar(
                        message = message,
                        actionLabel = if (message.contains("Amnezia VPN")) "Установить" else null,
                    )
                    if (result == androidx.compose.material3.SnackbarResult.ActionPerformed) {
                        runCatching {
                            startActivity(VpnBridge.amneziaPlayStoreIntent())
                        }
                    }
                    viewModel.clearError()
                }
            }

            LaunchedEffect(state.info) {
                state.info?.let {
                    snackbar.showSnackbar(it)
                    viewModel.clearInfo()
                }
            }

            DaddyVpnTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    containerColor = DaddyColors.Background,
                    snackbarHost = { SnackbarHost(snackbar) },
                ) { padding ->
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(padding),
                    ) {
                        if (state.loading) {
                            CircularProgressIndicator(
                                modifier = Modifier.align(Alignment.Center),
                                color = DaddyColors.Primary,
                            )
                        } else {
                            HomeScreen(
                                state = state,
                                onToggleConnection = {
                                    viewModel.toggleConnection { link ->
                                        VpnBridge.connect(this@MainActivity, link)
                                    }
                                },
                                onToggleServers = viewModel::toggleServers,
                                onSelectServer = viewModel::selectServer,
                                onOpenKey = viewModel::toggleKeySheet,
                            )
                        }
                    }

                    if (state.showKeySheet) {
                        KeySheet(
                            currentKey = state.vpnLink,
                            hasKey = state.hasKey,
                            onDismiss = viewModel::toggleKeySheet,
                            onSave = viewModel::saveKey,
                            onClear = viewModel::clearKey,
                        )
                    }
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        viewModel.handleIntent(intent)
    }
}

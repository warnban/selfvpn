package site.daddyvpn.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import site.daddyvpn.app.ui.theme.DaddyColors
import site.daddyvpn.app.ui.theme.DaddyTypography

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun KeySheet(
    currentKey: String?,
    hasKey: Boolean,
    onDismiss: () -> Unit,
    onSave: (String) -> Unit,
    onClear: () -> Unit,
) {
    var draft by rememberSaveable { mutableStateOf(currentKey.orEmpty()) }
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = DaddyColors.Card,
    ) {
        Column(modifier = Modifier.padding(horizontal = 24.dp, vertical = 8.dp)) {
            Text("Ключ VPN", style = DaddyTypography.BrandTitle, color = DaddyColors.Foreground)
            Text(
                "Скопируйте vpn:// из Telegram-бота или личного кабинета",
                color = DaddyColors.MutedForeground,
                fontSize = 13.sp,
                modifier = Modifier.padding(top = 8.dp, bottom = 16.dp),
            )
            OutlinedTextField(
                value = draft,
                onValueChange = { draft = it },
                label = { Text("vpn://…") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                colors = fieldColors(),
            )
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                if (hasKey) {
                    Button(
                        onClick = onClear,
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = DaddyColors.Secondary,
                            contentColor = DaddyColors.Foreground,
                        ),
                        shape = RoundedCornerShape(12.dp),
                    ) { Text("Удалить") }
                }
                Button(
                    onClick = { onSave(draft) },
                    modifier = Modifier.weight(1f),
                    enabled = draft.isNotBlank(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = DaddyColors.Primary,
                        contentColor = DaddyColors.PrimaryForeground,
                    ),
                    shape = RoundedCornerShape(12.dp),
                ) { Text("Сохранить") }
            }
            Spacer(Modifier.height(32.dp))
        }
    }
}

@Composable
private fun fieldColors() = OutlinedTextFieldDefaults.colors(
    focusedBorderColor = DaddyColors.Primary,
    unfocusedBorderColor = DaddyColors.BorderStrong,
    focusedTextColor = DaddyColors.Foreground,
    unfocusedTextColor = DaddyColors.Foreground,
    focusedLabelColor = DaddyColors.SecondaryForeground,
    unfocusedLabelColor = DaddyColors.MutedForeground,
    cursorColor = DaddyColors.Primary,
    focusedContainerColor = DaddyColors.Secondary,
    unfocusedContainerColor = DaddyColors.Secondary,
)

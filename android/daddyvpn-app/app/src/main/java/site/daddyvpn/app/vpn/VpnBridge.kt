package site.daddyvpn.app.vpn

import android.content.Context
import android.content.Intent
import android.content.Intent.FLAG_ACTIVITY_NEW_TASK
import android.content.pm.PackageManager
import android.net.Uri

object VpnBridge {
    private const val AMNEZIA_PACKAGE = "org.amnezia.vpn"
    private const val AMNEZIA_ACTIVITY = "org.amnezia.vpn.AmneziaActivity"
    private const val ACTION_IMPORT_CONFIG = "org.amnezia.vpn.IMPORT_CONFIG"
    private const val EXTRA_CONFIG = "CONFIG"

    enum class Result {
        /** VPN engine inside this APK (merged Amnezia build). */
        INTERNAL,

        /** Config sent to the official Amnezia VPN app. */
        EXTERNAL,

        /** Amnezia VPN is not installed. */
        AMNEZIA_MISSING,

        /** Invalid vpn:// link. */
        INVALID,
    }

    /**
     * Standalone UI apk: opens org.amnezia.vpn with the config.
     * Merged amnezia apk: uses org.amnezia.vpn.AmneziaActivity in the same package.
     */
    fun connect(context: Context, vpnLink: String): Result {
        val payload = vpnLink.trim().takeIf { it.startsWith("vpn://", ignoreCase = true) }
            ?: return Result.INVALID

        if (launchInternal(context, payload)) {
            return Result.INTERNAL
        }

        if (!isAmneziaInstalled(context)) {
            return Result.AMNEZIA_MISSING
        }

        return if (launchExternal(context, payload)) {
            Result.EXTERNAL
        } else {
            Result.AMNEZIA_MISSING
        }
    }

    fun amneziaPlayStoreIntent(): Intent =
        Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$AMNEZIA_PACKAGE")).apply {
            addFlags(FLAG_ACTIVITY_NEW_TASK)
        }

    private fun launchInternal(context: Context, payload: String): Boolean =
        runCatching {
            val clazz = Class.forName(AMNEZIA_ACTIVITY)
            val intent = Intent(context, clazz).apply {
                action = ACTION_IMPORT_CONFIG
                addCategory(Intent.CATEGORY_DEFAULT)
                putExtra(EXTRA_CONFIG, payload)
                flags = FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
            true
        }.getOrDefault(false)

    private fun launchExternal(context: Context, payload: String): Boolean =
        runCatching {
            // Must pin org.amnezia.vpn — otherwise Android resolves vpn:// back to us.
            context.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(payload)).apply {
                    setPackage(AMNEZIA_PACKAGE)
                    addFlags(FLAG_ACTIVITY_NEW_TASK)
                },
            )
            true
        }.getOrDefault(false)

    private fun isAmneziaInstalled(context: Context): Boolean =
        runCatching {
            context.packageManager.getPackageInfo(AMNEZIA_PACKAGE, PackageManager.GET_ACTIVITIES)
            true
        }.getOrDefault(false)
}

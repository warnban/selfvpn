import base64
import re


def config_from_vpn_link(vpn_link: str) -> str:
    if not vpn_link or not vpn_link.startswith("vpn://"):
        return ""
    try:
        return base64.b64decode(vpn_link[6:], validate=True).decode("utf-8").strip()
    except Exception:
        return ""


def config_from_panel_result(result: dict) -> str:
    config = result.get("config") or result.get("Config") or ""
    if config:
        return str(config).strip()
    link = result.get("vpn_link") or result.get("vpnLink") or ""
    return config_from_vpn_link(link)


def extract_vpn_link(result: dict) -> str:
    link = result.get("vpn_link") or result.get("vpnLink")
    config = result.get("config") or result.get("Config")
    if not link and config:
        link = "vpn://" + base64.b64encode(str(config).encode()).decode()
    return link or ""


def device_config_text(vpn_config: str | None, vpn_link: str | None) -> str:
    if vpn_config:
        return vpn_config.strip()
    return config_from_vpn_link(vpn_link or "")


def safe_conf_filename(name: str, device_id: int) -> str:
    # HTTP headers (Content-Disposition) must be latin-1 — keep filename ASCII-only.
    slug = re.sub(r"[^\w\-]+", "_", name, flags=re.ASCII).strip("_") or f"device_{device_id}"
    return f"{slug}.conf"

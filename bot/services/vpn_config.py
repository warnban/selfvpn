import base64
import json
import re
import zlib

from bot.config import settings


def server_display_name() -> str:
    return (settings.brand_name or "VPN").strip()


def decode_vpn_link(vpn_link: str) -> dict | None:
    if not vpn_link or not vpn_link.startswith("vpn://"):
        return None

    encoded_data = vpn_link[6:]
    padding = 4 - (len(encoded_data) % 4)
    encoded_data += "=" * padding
    try:
        raw = base64.urlsafe_b64decode(encoded_data)
        original_len = int.from_bytes(raw[:4], byteorder="big")
        payload = zlib.decompress(raw[4:])
        if len(payload) != original_len:
            return None
        return json.loads(payload)
    except Exception:
        try:
            return json.loads(base64.b64decode(vpn_link[6:], validate=True).decode("utf-8"))
        except Exception:
            return None


def encode_vpn_link(config: dict) -> str:
    json_bytes = json.dumps(config, indent=4, ensure_ascii=False).encode("utf-8")
    compressed = zlib.compress(json_bytes)
    header = len(json_bytes).to_bytes(4, byteorder="big")
    encoded = base64.urlsafe_b64encode(header + compressed).decode().rstrip("=")
    return f"vpn://{encoded}"


def _patch_display_name(node: object, name: str) -> None:
    if isinstance(node, dict):
        for key in ("hostName", "hostname", "serverName"):
            if key in node:
                node[key] = name
        if "description" in node:
            node["description"] = name
        for value in node.values():
            _patch_display_name(value, name)
    elif isinstance(node, list):
        for item in node:
            _patch_display_name(item, name)


def apply_server_display_name(vpn_link: str, display_name: str | None = None) -> str:
    name = (display_name or server_display_name()).strip()
    if not name or not vpn_link:
        return vpn_link

    config = decode_vpn_link(vpn_link)
    if not config:
        return vpn_link

    _patch_display_name(config, name)
    return encode_vpn_link(config)


def public_vpn_link(vpn_link: str | None) -> str:
    if not vpn_link:
        return ""
    return apply_server_display_name(vpn_link)


def config_from_vpn_link(vpn_link: str) -> str:
    if not vpn_link or not vpn_link.startswith("vpn://"):
        return ""
    config = decode_vpn_link(vpn_link)
    if not config:
        try:
            return base64.b64decode(vpn_link[6:], validate=True).decode("utf-8").strip()
        except Exception:
            return ""
    for proto in ("awg", "awg2", "wireguard", "openvpn", "xray"):
        data = config.get(proto)
        if isinstance(data, dict) and data.get("config"):
            return str(data["config"]).strip()
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


def prepare_panel_vpn(result: dict) -> tuple[str, str]:
    """Из ответа панели — ключ и conf с брендовым именем сервера."""
    vpn_link = public_vpn_link(extract_vpn_link(result))
    vpn_config = config_from_panel_result(result)
    if not vpn_config and vpn_link:
        vpn_config = config_from_vpn_link(vpn_link)
    return vpn_link, vpn_config


def device_config_text(vpn_config: str | None, vpn_link: str | None) -> str:
    if vpn_config:
        return vpn_config.strip()
    return config_from_vpn_link(public_vpn_link(vpn_link))


def safe_conf_filename(name: str, device_id: int) -> str:
    slug = re.sub(r"[^\w\-]+", "_", name, flags=re.ASCII).strip("_") or f"device_{device_id}"
    return f"{slug}.conf"

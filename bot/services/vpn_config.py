import base64
import re


def vpn_link_to_conf(vpn_link: str) -> str:
    """Декодирует vpn:// из Amnezia Panel в .conf для AmneziaWG."""
    raw = vpn_link.strip()
    if not raw.startswith("vpn://"):
        raise ValueError("Неверный формат ключа")
    try:
        conf = base64.b64decode(raw[6:], validate=True).decode("utf-8")
    except Exception as exc:
        raise ValueError("Не удалось декодировать ключ") from exc
    if not conf.strip().startswith("[Interface]"):
        raise ValueError("Не удалось получить .conf из ключа")
    return conf.strip() + "\n"


def conf_filename(device_name: str = "", device_id: int | None = None) -> str:
    """ASCII-имя файла — так Android надёжнее находит его в «Загрузках»."""
    if device_id is not None:
        return f"daddyvpn_{device_id}.conf"
    safe = re.sub(r"[^\w\-]+", "_", device_name.strip(), flags=re.ASCII)
    safe = safe.strip("_") or "vpn"
    return f"{safe}.conf"

import logging
import re
import time

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)

# WireGuard keepalive ~25s; 3 min covers idle tunnels without counting stale peers.
ONLINE_HANDSHAKE_MAX_AGE_SECONDS = 180


def parse_handshake_age_seconds(handshake: str) -> int | None:
    """Parse `wg show` handshake text like '2 minutes, 30 seconds ago'."""
    if not handshake:
        return None
    text = handshake.strip().lower()
    if not text or text in {"never", "(never)"}:
        return None
    if text.isdigit():
        ts = int(text)
        if ts > 1_000_000_000:
            return max(0, int(time.time()) - ts)
        return ts if ts > 0 else None
    if text.endswith(" ago"):
        text = text[:-4].strip()
    total = 0
    for amount, unit in re.findall(
        r"(\d+)\s*(day|days|hour|hours|minute|minutes|second|seconds)",
        text,
    ):
        n = int(amount)
        if unit.startswith("day"):
            total += n * 86400
        elif unit.startswith("hour"):
            total += n * 3600
        elif unit.startswith("minute"):
            total += n * 60
        elif unit.startswith("second"):
            total += n
    return total if total > 0 else None


def count_online_clients(
    clients: list[dict],
    known_client_ids: set[str],
    *,
    max_handshake_age_seconds: int = ONLINE_HANDSHAKE_MAX_AGE_SECONDS,
) -> int:
    online = 0
    for client in clients:
        client_id = client.get("clientId") or client.get("client_id") or ""
        if client_id not in known_client_ids:
            continue
        user_data = client.get("userData") or client.get("user_data") or {}
        if user_data.get("enabled") is False:
            continue
        age = parse_handshake_age_seconds(
            user_data.get("latestHandshake") or user_data.get("latest_handshake") or ""
        )
        if age is not None and age <= max_handshake_age_seconds:
            online += 1
    return online


class PanelClient:
    def __init__(self) -> None:
        self.base_url = settings.panel_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {settings.panel_api_token}"}

    async def create_client(self, name: str) -> dict:
        url = f"{self.base_url}/api/servers/{settings.panel_server_id}/connections/add"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers={**self.headers, "Content-Type": "application/json"},
                    json={
                        "protocol": settings.panel_protocol,
                        "name": name,
                    },
                )
        except httpx.ConnectError as exc:
            raise ValueError(
                f"Не удалось подключиться к Amnezia Panel ({self.base_url}). "
                f"Панель установлена и запущена? ({exc})"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ValueError("Таймаут при обращении к Amnezia Panel") from exc

        if response.status_code >= 400:
            detail = response.text.strip()[:400] or response.reason_phrase
            raise ValueError(f"Panel API ошибка {response.status_code}: {detail}")

        return response.json()

    async def remove_client(self, client_id: str) -> None:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/servers/{settings.panel_server_id}/connections/remove",
                headers={**self.headers, "Content-Type": "application/json"},
                json={
                    "protocol": settings.panel_protocol,
                    "client_id": client_id,
                },
            )
            response.raise_for_status()

    async def toggle_client(self, client_id: str, enable: bool) -> None:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/servers/{settings.panel_server_id}/connections/toggle",
                headers={**self.headers, "Content-Type": "application/json"},
                json={
                    "protocol": settings.panel_protocol,
                    "client_id": client_id,
                    "enable": enable,
                },
            )
            response.raise_for_status()

    async def list_connections(self) -> list[dict] | None:
        if not settings.panel_api_token:
            return None
        url = f"{self.base_url}/api/servers/{settings.panel_server_id}/connections"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params={"protocol": settings.panel_protocol},
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Panel list_connections unreachable: %s", exc)
            return None

        if response.status_code >= 400:
            logger.warning(
                "Panel list_connections HTTP %s: %s",
                response.status_code,
                response.text.strip()[:200],
            )
            return None

        payload = response.json()
        clients = payload.get("clients")
        if not isinstance(clients, list):
            logger.warning("Panel list_connections unexpected payload: %s", type(payload))
            return None
        return clients

    async def count_online_clients(
        self,
        known_client_ids: set[str],
        *,
        max_handshake_age_seconds: int = ONLINE_HANDSHAKE_MAX_AGE_SECONDS,
    ) -> int | None:
        clients = await self.list_connections()
        if clients is None:
            return None
        if not known_client_ids:
            return 0
        return count_online_clients(
            clients,
            known_client_ids,
            max_handshake_age_seconds=max_handshake_age_seconds,
        )


panel_client = PanelClient()

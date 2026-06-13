import httpx

from bot.config import settings


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


panel_client = PanelClient()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    bot_token: str
    admin_ids: str = ""

    daily_price_rub: float = 5.0
    trial_days: int = 2
    referral_bonus_rub: float = 5.0
    max_devices: int = 5

    panel_url: str = "http://127.0.0.1:5000"
    panel_api_token: str = ""
    panel_server_id: int = 0
    panel_protocol: str = "awg2"

    payment_card: str = "0000 0000 0000 0000"
    payment_bank: str = "Банк"
    payment_holder: str = "Получатель"

    database_url: str = "sqlite+aiosqlite:///./data/bot.db"
    billing_hour: int = 3

    web_base_url: str = "http://127.0.0.1:8080"
    web_secret_key: str = "change-me-in-production"
    admin_web_password: str = "admin"
    uploads_dir: str = "./data/uploads"
    brand_name: str = "VPN от дяди Сани"

    @property
    def admin_id_list(self) -> list[int]:
        if not self.admin_ids.strip():
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def trial_balance_rub(self) -> float:
        return self.daily_price_rub * self.trial_days

    def price_for_days(self, days: int) -> float:
        return round(self.daily_price_rub * days, 2)

    def cabinet_url(self, token: str) -> str:
        return f"{self.web_base_url.rstrip('/')}/cabinet/{token}"

    def admin_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/admin"


settings = Settings()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_list

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

    daily_price_rub: float = 10.0
    trial_days: int = 2
    referral_bonus_rub: float = 5.0
    max_devices: int = 5
    stars_per_day: int = 6
    stars_enabled: bool = True

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
    brand_name: str = "Интернет от дяди Сани"
    support_tg: str = "aleblanche"

    freekassa_merchant_id: int = 0
    freekassa_secret_1: str = ""
    freekassa_secret_2: str = ""

    @property
    def freekassa_enabled(self) -> bool:
        return bool(
            self.freekassa_merchant_id
            and self.freekassa_secret_1
            and self.freekassa_secret_2
        )

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

    def default_stars_for_days(self, days: int) -> int:
        return self.stars_per_day * days

    def cabinet_url(self, token: str) -> str:
        return f"{self.web_base_url.rstrip('/')}/cabinet/{token}"

    def cabinet_pay_url(self, token: str) -> str:
        return f"{self.web_base_url.rstrip('/')}/cabinet/{token}/pay"

    def admin_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/admin"

    def payment_notify_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/payment/notify"

    def payment_success_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/payment/success"

    def payment_fail_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/payment/fail"

    @property
    def support_tg_handle(self) -> str:
        return self.support_tg.lstrip("@")

    def support_tg_url(self) -> str:
        handle = self.support_tg_handle
        return f"https://t.me/{handle}" if handle else ""


settings = Settings()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_list

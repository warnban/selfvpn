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
    # Код страны для дефолтного сервера: "Бренд NL". Для нескольких: PANEL_SERVER_LABELS=0:NL,1:DE
    panel_server_country: str = ""
    panel_server_labels: str = ""

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
    freekassa_api_key: str = ""
    freekassa_secret_1: str = ""
    freekassa_secret_2: str = ""
    freekassa_client_ip_fallback: str = ""

    # Cardlink. payment_provider выбирает активную онлайн-кассу: "freekassa" или "cardlink".
    payment_provider: str = "freekassa"
    cardlink_api_token: str = ""
    cardlink_shop_id: str = ""

    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_ssl: bool = True
    smtp_timeout: int = 30

    @property
    def freekassa_enabled(self) -> bool:
        return bool(
            self.freekassa_merchant_id
            and self.freekassa_api_key
            and self.freekassa_secret_2
        )

    @property
    def cardlink_enabled(self) -> bool:
        return bool(self.cardlink_api_token and self.cardlink_shop_id)

    @property
    def active_payment_provider(self) -> str:
        """Какая онлайн-касса используется для веб-оплаты прямо сейчас."""
        provider = (self.payment_provider or "freekassa").strip().lower()
        if provider == "cardlink" and self.cardlink_enabled:
            return "cardlink"
        return "freekassa"

    @property
    def online_payment_enabled(self) -> bool:
        if self.active_payment_provider == "cardlink":
            return self.cardlink_enabled
        return self.freekassa_enabled

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

    def cardlink_success_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/cardlink/success"

    def cardlink_fail_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/cardlink/fail"

    def cardlink_result_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/cardlink/result"

    def cardlink_refund_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/cardlink/refund"

    def cardlink_chargeback_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/cardlink/chargeback"

    @property
    def support_tg_handle(self) -> str:
        return self.support_tg.lstrip("@")

    def about_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/about"

    def support_tg_url(self) -> str:
        handle = self.support_tg_handle
        return f"https://t.me/{handle}" if handle else ""

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    @property
    def smtp_from_address(self) -> str:
        return self.smtp_from or self.smtp_user

    def register_url(self, ref: int | None = None) -> str:
        url = f"{self.web_base_url.rstrip('/')}/auth/register"
        if ref:
            url += f"?ref={ref}"
        return url

    def login_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/auth/login"

    def cabinet_session_url(self) -> str:
        return f"{self.web_base_url.rstrip('/')}/cabinet"

    def panel_server_label_map(self) -> dict[int, str]:
        labels: dict[int, str] = {}
        raw = self.panel_server_labels.strip()
        if raw:
            for part in raw.split(","):
                part = part.strip()
                if ":" not in part:
                    continue
                sid, code = part.split(":", 1)
                sid = sid.strip()
                code = code.strip().upper()
                if sid.isdigit() and code:
                    labels[int(sid)] = code
        elif self.panel_server_country.strip():
            labels[self.panel_server_id] = self.panel_server_country.strip().upper()
        return labels

    def vpn_server_display_name(self, server_id: int | None = None) -> str:
        brand = (self.brand_name or "VPN").strip()
        sid = self.panel_server_id if server_id is None else server_id
        code = self.panel_server_label_map().get(sid, "")
        return f"{brand} {code}" if code else brand


settings = Settings()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_list

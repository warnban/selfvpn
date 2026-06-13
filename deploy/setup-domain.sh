#!/bin/bash
# Настройка домена daddyvpn.site → HTTPS → веб-кабинет на :8080
set -e

DOMAIN="daddyvpn.site"
VPS_IP="72.56.124.163"

echo "=== Домен: $DOMAIN → $VPS_IP ==="
echo "Перед запуском добавьте DNS A-запись:"
echo "  @    → $VPS_IP"
echo "  www  → $VPS_IP  (или CNAME на $DOMAIN)"
echo ""
read -r -p "DNS уже настроен? (y/n) " ok
if [[ "$ok" != "y" && "$ok" != "Y" ]]; then
  echo "Настройте DNS в панели регистратора, подождите 5–30 мин и запустите снова."
  exit 1
fi

apt update
apt install -y nginx certbot python3-certbot-nginx

ufw allow OpenSSH 2>/dev/null || true
ufw allow 80 2>/dev/null || true
ufw allow 443 2>/dev/null || true

cp /opt/selfvpn/deploy/nginx-daddyvpn.site.conf /etc/nginx/sites-available/selfvpn
ln -sf /etc/nginx/sites-available/selfvpn /etc/nginx/sites-enabled/selfvpn
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
nginx -t
systemctl enable nginx
systemctl reload nginx

certbot --nginx -d daddyvpn.site -d www.daddyvpn.site --non-interactive --agree-tos -m admin@daddyvpn.site || \
  certbot --nginx -d daddyvpn.site -d www.daddyvpn.site

echo ""
echo "=== Обновите .env ==="
echo "WEB_BASE_URL=https://daddyvpn.site"
echo ""
echo "Затем: cd /opt/selfvpn && docker compose restart"
echo ""
echo "Проверка:"
curl -s -o /dev/null -w "https://daddyvpn.site/admin/login → HTTP %{http_code}\n" https://daddyvpn.site/admin/login || true

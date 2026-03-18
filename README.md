# HealthSync v2.0

Персональный трекер привычек и биометрики.

## Быстрый старт

### 1. Конфигурация

```bash
cp .env.example .env
```

Заполни `.env`:
- `TELEGRAM_BOT_TOKEN` — токен от @BotFather
- `GARMIN_ENCRYPTION_KEY` — генерация: `python3 -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"`
- `ANTHROPIC_API_KEY` — ключ Claude API
- `JWT_SECRET` — любая длинная случайная строка
- `USER1_USERNAME/PASSWORD/TELEGRAM_ID` — первый пользователь
- `USER2_USERNAME/PASSWORD/TELEGRAM_ID` — второй пользователь

### 2. Запуск

```bash
docker compose up -d
```

### 3. HTTPS (Let's Encrypt на Hetzner)

```bash
apt install certbot
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/certs/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/certs/
```

Обнови `nginx/nginx.conf` — замени `yourdomain.com` на свой домен.

### 4. Добавление Garmin

Через Telegram: `/settings` → введи email и пароль от Garmin Connect.

Или через дашборд: Настройки → Garmin Connect.

## Структура

```
healthsync/
├── backend/          # FastAPI + Telegram bot
│   ├── main.py
│   ├── models.py
│   ├── routers/      # auth, habits, metrics, heart_rate, insights
│   ├── services/     # garmin_sync, ai_insights, scheduler
│   └── bot/          # Telegram bot
├── frontend/         # React + Vite + Tailwind
│   └── src/pages/    # Dashboard, HeartRate, Sleep, Habits, Correlations, Insights, Settings
├── migrations/       # Alembic
└── nginx/
```

## Расписание

- **03:00** — ночная синхронизация Garmin
- **Воскресенье 09:00** — еженедельный AI-инсайт
- **10:00** — проверка аномалий (sleep score −15%, resting HR +10%)
- **08:00** — опциональное утреннее напоминание о сне (включается в /settings)

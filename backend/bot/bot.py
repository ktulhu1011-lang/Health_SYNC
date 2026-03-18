import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import settings
from bot.handlers.log_handler import (
    cmd_log, cmd_today, cmd_stats, cmd_insight, cmd_history, button_callback
)
from bot.handlers.settings_handler import (
    cmd_settings, settings_callback, handle_garmin_email, handle_garmin_password
)


async def cmd_start(update: Update, context):
    await update.message.reply_text(
        "👋 Добро пожаловать в HealthSync!\n\n"
        "Доступные команды:\n"
        "/log — ввести данные о привычках\n"
        "/today — сводка за сегодня + Garmin\n"
        "/stats — статистика за 7 дней\n"
        "/insight — AI-инсайт прямо сейчас\n"
        "/history — последние 7 записей\n"
        "/settings — настройки (добавки, напоминания, Garmin)\n"
    )


def main():
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    app = Application.builder().token(settings.telegram_bot_token).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("log", cmd_log))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("insight", cmd_insight))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("settings", cmd_settings))

    # Callbacks
    app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^(settings:|supp_set:)"))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Text messages (for Garmin credential input)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        _handle_text
    ))

    print("[bot] Starting HealthSync bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def _handle_text(update: Update, context):
    if context.user_data.get("waiting_garmin_email"):
        await handle_garmin_email(update, context)
    elif context.user_data.get("waiting_garmin_password"):
        await handle_garmin_password(update, context)


if __name__ == "__main__":
    main()

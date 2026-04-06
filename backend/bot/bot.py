import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from telegram import Update, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import settings
from bot.handlers.log_handler import (
    cmd_log, cmd_today, cmd_stats, cmd_insight, cmd_ask, cmd_history, button_callback
)
from bot.handlers.settings_handler import (
    cmd_settings, settings_callback, handle_garmin_email, handle_garmin_password
)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📝 Лог"), KeyboardButton("📊 Сегодня")],
        [KeyboardButton("🤖 Инсайт"), KeyboardButton("💬 Спросить AI")],
        [KeyboardButton("📋 История"), KeyboardButton("⚙️ Настройки")],
    ],
    resize_keyboard=True,
)

async def cmd_start(update: Update, context):
    await update.message.reply_text(
        "👋 Добро пожаловать в HealthSync!\n\n"
        "Используй кнопки меню внизу 👇",
        reply_markup=MAIN_KEYBOARD,
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
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("settings", cmd_settings))

    # Callbacks
    app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^(settings:|supp_set:)"))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Text messages
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        _handle_text
    ))

    async def post_init(app):
        await app.bot.set_my_commands([
            BotCommand("log", "📝 Ввести данные о привычках"),
            BotCommand("today", "📊 Сводка за сегодня + Garmin"),
            BotCommand("stats", "📈 Статистика за 7 дней"),
            BotCommand("insight", "🤖 AI-инсайт прямо сейчас"),
            BotCommand("ask", "💬 Задать вопрос AI по своим данным"),
            BotCommand("history", "📋 Последние 7 записей"),
            BotCommand("settings", "⚙️ Настройки"),
        ])

    app.post_init = post_init
    print("[bot] Starting HealthSync bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


BUTTON_MAP = {
    "📝 Лог": cmd_log,
    "📊 Сегодня": cmd_today,
    "📈 Статистика": cmd_stats,
    "🤖 Инсайт": cmd_insight,
    "💬 Спросить AI": cmd_ask,
    "📋 История": cmd_history,
    "⚙️ Настройки": cmd_settings,
}

async def _handle_text(update: Update, context):
    text = update.message.text
    if text in BUTTON_MAP:
        await BUTTON_MAP[text](update, context)
        return
    if context.user_data.get("waiting_ai_question"):
        from bot.handlers.log_handler import handle_ai_question
        await handle_ai_question(update, context)
    elif context.user_data.get("waiting_garmin_email"):
        await handle_garmin_email(update, context)
    elif context.user_data.get("waiting_garmin_password"):
        await handle_garmin_password(update, context)


if __name__ == "__main__":
    main()

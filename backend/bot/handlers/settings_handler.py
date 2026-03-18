"""
/settings handler — supplements config, reminders, Garmin credentials.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from database import SessionLocal
import models
from bot.keyboards import SUPPLEMENT_GROUPS

WAITING_GARMIN_EMAIL = 1
WAITING_GARMIN_PASSWORD = 2


def _get_user(telegram_id: int):
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    return user, db


def settings_keyboard(user_settings: dict) -> InlineKeyboardMarkup:
    reminder_on = user_settings.get("morning_reminder_enabled", False)
    reminder_emoji = "✅" if reminder_on else "⬜"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💊 Настроить добавки", callback_data="settings:supplements")],
        [InlineKeyboardButton(f"{reminder_emoji} Утреннее напоминание о сне", callback_data="settings:toggle_reminder")],
        [InlineKeyboardButton("🏃 Подключить Garmin", callback_data="settings:garmin")],
        [InlineKeyboardButton("🔄 Синхронизировать Garmin сейчас", callback_data="settings:sync_now")],
    ])


def supplement_settings_keyboard(active: set) -> InlineKeyboardMarkup:
    rows = []
    for group, supps in SUPPLEMENT_GROUPS.items():
        for key, label in supps:
            emoji = "✅" if key in active else "⬜"
            rows.append([InlineKeyboardButton(f"{emoji} {label}", callback_data=f"supp_set:{key}")])
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="settings:back")])
    return InlineKeyboardMarkup(rows)


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, db = _get_user(update.effective_user.id)
    if db:
        db.close()
    if not user:
        await update.message.reply_text("❌ Не зарегистрирован.")
        return
    settings_data = user.settings_json or {}
    await update.message.reply_text(
        "⚙️ Настройки HealthSync:",
        reply_markup=settings_keyboard(settings_data)
    )


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user, db = _get_user(query.from_user.id)
    if not user:
        await query.edit_message_text("❌ Не зарегистрирован.")
        if db:
            db.close()
        return

    try:
        user_settings = dict(user.settings_json or {})

        if data == "settings:back":
            await query.edit_message_text("⚙️ Настройки:", reply_markup=settings_keyboard(user_settings))
            return

        if data == "settings:supplements":
            active = set(user_settings.get("active_supplements", []))
            if not active:
                # Default: all active
                active = set(key for group in SUPPLEMENT_GROUPS.values() for key, _ in group)
            await query.edit_message_text(
                "💊 Выбери активные добавки (✅ = включена):",
                reply_markup=supplement_settings_keyboard(active)
            )
            return

        if data.startswith("supp_set:"):
            key = data.split(":")[1]
            active = set(user_settings.get("active_supplements", []))
            if not active:
                active = set(k for group in SUPPLEMENT_GROUPS.values() for k, _ in group)
            if key in active:
                active.discard(key)
            else:
                active.add(key)
            user_settings["active_supplements"] = list(active)
            user.settings_json = user_settings
            db.commit()
            await query.edit_message_reply_markup(reply_markup=supplement_settings_keyboard(active))
            return

        if data == "settings:toggle_reminder":
            current = user_settings.get("morning_reminder_enabled", False)
            user_settings["morning_reminder_enabled"] = not current
            user.settings_json = user_settings
            db.commit()
            await query.edit_message_text(
                "⚙️ Настройки:",
                reply_markup=settings_keyboard(user_settings)
            )
            return

        if data == "settings:garmin":
            await query.edit_message_text(
                "🏃 Введи email от Garmin Connect (следующим сообщением):"
            )
            context.user_data["waiting_garmin_email"] = True
            return

        if data == "settings:sync_now":
            await query.edit_message_text("🔄 Запускаю синхронизацию Garmin...")
            from services.garmin_sync import sync_user
            try:
                count = sync_user(user.id, db, days_back=2)
                await query.edit_message_text(f"✅ Синхронизировано! Получено {count} метрик.")
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка синхронизации: {e}")
            return

    finally:
        db.close()


async def handle_garmin_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_garmin_email"):
        return
    context.user_data["garmin_email"] = update.message.text
    context.user_data["waiting_garmin_email"] = False
    context.user_data["waiting_garmin_password"] = True
    await update.message.reply_text("🔑 Теперь введи пароль от Garmin Connect:")


async def handle_garmin_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_garmin_password"):
        return
    email = context.user_data.get("garmin_email")
    password = update.message.text
    context.user_data["waiting_garmin_password"] = False

    user, db = _get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Не зарегистрирован.")
        if db:
            db.close()
        return
    try:
        from services.garmin_sync import encrypt_value
        user.garmin_email_enc = encrypt_value(email)
        user.garmin_token_enc = encrypt_value(password)
        db.commit()
        await update.message.reply_text(
            "✅ Данные Garmin сохранены! Используй /settings → Синхронизировать для проверки."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка сохранения: {e}")
    finally:
        db.close()


def get_handlers():
    return [
        CommandHandler("settings", cmd_settings),
        CallbackQueryHandler(settings_callback, pattern=r"^(settings:|supp_set:)"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_garmin_email),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_garmin_password),
    ]

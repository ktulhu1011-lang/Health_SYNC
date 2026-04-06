"""
Main /log handler — shows category menu and routes to sub-handlers.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import date, datetime
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from database import SessionLocal
import models
from bot.keyboards import (
    main_log_menu, bad_habits_menu, supplements_group_menu,
    water_keyboard, wellbeing_menu, date_select_keyboard,
    smoking_keyboard, smoking_count_keyboard, alcohol_keyboard, sweets_keyboard,
    fastfood_keyboard, screen_keyboard, coffee_count_keyboard,
    coffee_time_keyboard, supplement_list_keyboard,
    nutr_pre_sleep_eating_keyboard,
    meditation_keyboard, walk_keyboard, feeling_keyboard, stress_keyboard,
    insight_period_keyboard,
    SUPPLEMENT_GROUPS,
)


def _get_user(telegram_id: int):
    db = SessionLocal()
    try:
        return db.query(models.User).filter(models.User.telegram_id == telegram_id).first(), db
    except Exception:
        db.close()
        return None, None


def _save_habit(user_id: int, category: str, habit_key: str, value, db=None, log_date=None):
    close = False
    if db is None:
        db = SessionLocal()
        close = True
    try:
        log = models.HabitLog(
            user_id=user_id,
            date=log_date or date.today(),
            category=category,
            habit_key=habit_key,
            value=value,
        )
        db.add(log)
        db.commit()
    finally:
        if close:
            db.close()


def _get_log_date(context) -> date:
    from datetime import timedelta
    days_back = context.user_data.get("log_days_back", 0)
    return date.today() - timedelta(days=days_back)


async def cmd_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, db = _get_user(update.effective_user.id)
    if db:
        db.close()
    if not user:
        await update.message.reply_text(
            "❌ Ты не зарегистрирован в системе. Обратись к администратору."
        )
        return
    context.user_data["log_days_back"] = 0
    await update.message.reply_text(
        "📅 За какой день вносишь данные?",
        reply_markup=date_select_keyboard()
    )


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, db = _get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Не зарегистрирован.")
        if db:
            db.close()
        return
    try:
        today = date.today()
        logs = db.query(models.HabitLog).filter(
            models.HabitLog.user_id == user.id,
            models.HabitLog.date == today
        ).all()

        # Garmin — try today first, fall back to yesterday
        from datetime import timedelta
        yesterday = today - timedelta(days=1)
        garmin = db.query(models.GarminDaily).filter(
            models.GarminDaily.user_id == user.id,
            models.GarminDaily.date == today
        ).first()
        garmin_date = today
        if not garmin:
            garmin = db.query(models.GarminDaily).filter(
                models.GarminDaily.user_id == user.id,
                models.GarminDaily.date == yesterday
            ).first()
            garmin_date = yesterday

        lines = [f"📊 Данные за {today.strftime('%d.%m.%Y')}:"]
        if logs:
            lines.append("\n🗒 Привычки сегодня:")
            for log in logs:
                lines.append(f"  • {log.habit_key}: {log.value}")
        else:
            lines.append("\n⬜ Привычки ещё не внесены. Используй /log")

        if garmin:
            lines.append(f"\n📡 Данные Garmin за {garmin_date.strftime('%d.%m.%Y')}:")
            if garmin.sleep_score:
                lines.append(f"  💤 Sleep score: {garmin.sleep_score}")
            if garmin.deep_sleep_sec:
                lines.append(f"  🔵 Глубокий сон: {garmin.deep_sleep_sec // 60} мин")
            if garmin.resting_hr:
                lines.append(f"  💗 Пульс покоя: {garmin.resting_hr} BPM")
            if garmin.hrv_status:
                lines.append(f"  ❤️ HRV: {garmin.hrv_status}")
            if garmin.body_battery_charged:
                lines.append(f"  🔋 Body Battery: +{garmin.body_battery_charged}")
        else:
            lines.append(f"\n⚠️ Данные Garmin ещё не синхронизированы")

        await update.message.reply_text("\n".join(lines))
    finally:
        db.close()


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, db = _get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Не зарегистрирован.")
        if db:
            db.close()
        return
    try:
        from datetime import timedelta
        week_ago = date.today() - timedelta(days=7)
        logs = db.query(models.HabitLog).filter(
            models.HabitLog.user_id == user.id,
            models.HabitLog.date >= week_ago
        ).all()

        # Count by habit_key
        counts: dict = {}
        for log in logs:
            k = log.habit_key
            counts[k] = counts.get(k, 0) + 1

        garmin_rows = db.query(models.GarminDaily).filter(
            models.GarminDaily.user_id == user.id,
            models.GarminDaily.date >= week_ago
        ).all()

        lines = ["📈 Сводка за 7 дней:"]
        if counts:
            lines.append("\n🗒 Привычки:")
            for k, cnt in sorted(counts.items()):
                lines.append(f"  • {k}: {cnt} записей")

        if garmin_rows:
            sleep_scores = [r.sleep_score for r in garmin_rows if r.sleep_score]
            hrv_vals = [r.hrv_last_night_avg for r in garmin_rows if r.hrv_last_night_avg]
            rhr_vals = [r.resting_hr for r in garmin_rows if r.resting_hr]
            lines.append("\n📡 Garmin (среднее за неделю):")
            if sleep_scores:
                lines.append(f"  💤 Sleep score: {sum(sleep_scores)//len(sleep_scores)}")
            if rhr_vals:
                lines.append(f"  💗 Пульс покоя: {sum(rhr_vals)//len(rhr_vals)} BPM")
            if hrv_vals:
                lines.append(f"  ❤️ HRV avg: {sum(hrv_vals)/len(hrv_vals):.1f} мс")

        await update.message.reply_text("\n".join(lines))
    finally:
        db.close()


async def cmd_insight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, db = _get_user(update.effective_user.id)
    if db:
        db.close()
    if not user:
        await update.message.reply_text("❌ Не зарегистрирован.")
        return
    await update.message.reply_text(
        "📊 За какой период сделать AI-анализ?",
        reply_markup=insight_period_keyboard()
    )


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, db = _get_user(update.effective_user.id)
    if db: db.close()
    if not user:
        await update.message.reply_text("❌ Не зарегистрирован.")
        return
    context.user_data["waiting_ai_question"] = True
    context.user_data["ai_question_days"] = 30
    await update.message.reply_text(
        "💬 Задай любой вопрос — AI ответит на основе твоих данных за 30 дней.\n\n"
        "Например:\n"
        "• Как кофе влияет на мой сон?\n"
        "• В какие дни у меня лучший HRV?\n"
        "• Помогают ли тренировки со стрессом?\n\n"
        "Просто напиши вопрос:"
    )


async def handle_ai_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    days = context.user_data.get("ai_question_days", 30)
    context.user_data.pop("waiting_ai_question", None)

    user, db = _get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Не зарегистрирован.")
        if db: db.close()
        return

    try:
        await update.message.reply_text("🤔 Анализирую твои данные, подожди...")
        from services.ai_insights import ask_question_for_user
        answer = ask_question_for_user(user.id, question, db, days=days)
        chunks = _split_text(f"💬 Вопрос: {question}\n\n{answer}", limit=4000)
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk = f"...продолжение ({i+1}/{len(chunks)}):\n\n" + chunk
            await update.message.reply_text(chunk)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    finally:
        db.close()


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, db = _get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Не зарегистрирован.")
        if db:
            db.close()
        return
    try:
        from datetime import timedelta
        week_ago = date.today() - timedelta(days=7)
        logs = db.query(models.HabitLog).filter(
            models.HabitLog.user_id == user.id,
            models.HabitLog.date >= week_ago
        ).order_by(models.HabitLog.date.desc(), models.HabitLog.logged_at.desc()).limit(14).all()

        if not logs:
            await update.message.reply_text("📭 Последних записей нет.")
            return

        lines = ["📜 Последние записи:"]
        for log in logs:
            lines.append(f"  {log.date.strftime('%d.%m')} • {log.habit_key}: {log.value}")

        await update.message.reply_text("\n".join(lines))
    finally:
        db.close()


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    user, db = _get_user(user_id)
    if not user:
        await query.edit_message_text("❌ Не зарегистрирован.")
        if db:
            db.close()
        return

    try:
        await _route_callback(query, data, user, db, context)
    finally:
        db.close()


async def _route_callback(query, data: str, user, db, context):
    # AI Insight period selection
    if data.startswith("insight:days:"):
        days = int(data.split(":")[-1])
        await query.edit_message_text(f"🤖 Генерирую AI-анализ за {days} дней, подожди 20–30 секунд...")
        try:
            from services.ai_insights import generate_insight_for_user
            insight = generate_insight_for_user(user.id, db, trigger_type="on_demand", days=days)
            text = insight.insight_text
            header = f"📊 AI-анализ за {days} дней:\n\n"
            # Split by paragraphs to avoid cutting mid-sentence
            chunks = _split_text(header + text, limit=4000)
            for i, chunk in enumerate(chunks):
                if i > 0:
                    chunk = f"📊 продолжение ({i+1}/{len(chunks)}):\n\n" + chunk
                await query.message.reply_text(chunk)
        except Exception as e:
            await query.message.reply_text(f"❌ Ошибка генерации: {e}")
        return

    # Date selection
    if data.startswith("date:"):
        from datetime import timedelta
        days_back = int(data.split(":")[1])
        context.user_data["log_days_back"] = days_back
        log_date = date.today() - timedelta(days=days_back)
        date_str = log_date.strftime("%d.%m.%Y")
        await query.edit_message_text(
            f"📋 Записываем за {date_str}. Выбери категорию:",
            reply_markup=main_log_menu()
        )
        return

    # Main menu navigation
    if data == "log:menu":
        log_date = _get_log_date(context)
        await query.edit_message_text(
            f"📋 Записываем за {log_date.strftime('%d.%m.%Y')}. Выбери категорию:",
            reply_markup=main_log_menu()
        )
        return

    if data == "log:done":
        await query.edit_message_text("✅ Готово! Данные сохранены. Используй /today для просмотра.")
        return

    # Category routing
    if data == "cat:bad_habits":
        await query.edit_message_text("🚬 Вредные привычки:", reply_markup=bad_habits_menu())
        return

    if data == "cat:supplements":
        active = set((user.settings_json or {}).get("active_supplements", []))
        await query.edit_message_text("💊 Добавки NOW — выбери группу:", reply_markup=supplements_group_menu())
        return

    if data == "cat:water":
        await query.edit_message_text("💧 Сколько воды выпил сегодня?", reply_markup=water_keyboard())
        return

    if data == "cat:wellbeing":
        await query.edit_message_text("🧘 Активности / самочувствие:", reply_markup=wellbeing_menu())
        return

    # Bad habits sub-menu
    if data == "bh:smoking":
        await query.edit_message_text("🚬 Курение сегодня:", reply_markup=smoking_keyboard())
        return
    if data == "bh:smoking_count":
        await query.edit_message_text("🚬 Сколько сигарет?", reply_markup=smoking_count_keyboard())
        return
    if data == "bh:alcohol":
        await query.edit_message_text("🍷 Алкоголь сегодня:", reply_markup=alcohol_keyboard())
        return
    if data == "bh:sweets":
        await query.edit_message_text("🍭 Сладкое сегодня:", reply_markup=sweets_keyboard())
        return
    if data == "bh:fastfood":
        await query.edit_message_text("🍔 Фастфуд сегодня:", reply_markup=fastfood_keyboard())
        return
    if data == "bh:screen":
        await query.edit_message_text("📱 Экран перед сном:", reply_markup=screen_keyboard())
        return
    if data == "bh:coffee":
        await query.edit_message_text("☕ Кофе сегодня:", reply_markup=coffee_count_keyboard())
        return

    # Coffee flow
    if data.startswith("habit:coffee_count:"):
        count = data.split(":")[-1]
        context.user_data["coffee_count"] = count
        await query.edit_message_text(
            f"☕ {count} чашки — когда был последний кофе?",
            reply_markup=coffee_time_keyboard(count)
        )
        return

    if data.startswith("habit:coffee:") and len(data.split(":")) == 4:
        parts = data.split(":")
        count, time_val = parts[2], parts[3]
        _save_habit(user.id, "bad_habits", "coffee", {"count": count, "last_time": time_val}, db, _get_log_date(context))
        await query.edit_message_text(
            f"☕ Записано: {count} чашки, последний — {time_val}",
            reply_markup=bad_habits_menu()
        )
        return

    # Supplements
    if data.startswith("supp:group:"):
        group = data.split(":")[-1]
        active = set((user.settings_json or {}).get("active_supplements", []))
        taken = _get_today_taken_supplements(user.id, db, group, _get_log_date(context))
        group_name = {"antistress": "Антистресс 🧘", "antioxidants": "Антиоксиданты 🛡", "basic": "Базовые ⚡"}.get(group, group)
        await query.edit_message_text(
            f"💊 {group_name} — отметь принятые:",
            reply_markup=supplement_list_keyboard(group, taken, active)
        )
        return

    if data.startswith("supp:toggle:"):
        _, _, group, key = data.split(":")
        taken = _get_today_taken_supplements(user.id, db, group, _get_log_date(context))
        if key in taken:
            # Remove
            _remove_habit(user.id, "supplements", f"supp_{key}", db, _get_log_date(context))
            taken.discard(key)
        else:
            _save_habit(user.id, "supplements", f"supp_{key}", True, db, _get_log_date(context))
            taken.add(key)
        active = set((user.settings_json or {}).get("active_supplements", []))
        await query.edit_message_reply_markup(reply_markup=supplement_list_keyboard(group, taken, active))
        return

    # Nutrition sub-menu

    # Wellbeing sub-menu
    if data == "wb:meditation":
        await query.edit_message_text("🧘 Медитация:", reply_markup=meditation_keyboard())
        return
    if data == "wb:walk":
        await query.edit_message_text("🚶 Прогулка на воздухе:", reply_markup=walk_keyboard())
        return
    if data == "wb:feeling":
        await query.edit_message_text("😊 Самочувствие (1–5):", reply_markup=feeling_keyboard())
        return
    if data == "wb:stress":
        await query.edit_message_text("😤 Уровень стресса:", reply_markup=stress_keyboard())
        return
    if data == "wb:pre_sleep_eating":
        await query.edit_message_text("🕐 Ел за 2ч до сна?", reply_markup=nutr_pre_sleep_eating_keyboard())
        return

    # Generic habit save: habit:{key}:{value}
    if data.startswith("habit:") and len(data.split(":")) == 3:
        _, key, value = data.split(":")
        category = _key_to_category(key)
        _save_habit(user.id, category, key, value, db, _get_log_date(context))
        label = _key_label(key)
        await query.edit_message_text(
            f"✅ {label} записано: {value}",
            reply_markup=_back_keyboard(category)
        )
        return


def _split_text(text: str, limit: int = 4000) -> list:
    """Split text into chunks by paragraph boundaries, max `limit` chars each."""
    if len(text) <= limit:
        return [text]
    chunks = []
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= limit:
            current = (current + "\n\n" + para).lstrip("\n")
        else:
            if current:
                chunks.append(current)
            # If single paragraph is too long, split by sentence
            if len(para) > limit:
                sentences = para.split(". ")
                current = ""
                for s in sentences:
                    if len(current) + len(s) + 2 <= limit:
                        current = (current + ". " + s).lstrip(". ")
                    else:
                        if current:
                            chunks.append(current)
                        current = s
            else:
                current = para
    if current:
        chunks.append(current)
    return chunks


def _get_today_taken_supplements(user_id: int, db, group: str, log_date=None) -> set:
    log_date = log_date or date.today()
    keys = [key for key, _ in SUPPLEMENT_GROUPS.get(group, [])]
    logs = db.query(models.HabitLog).filter(
        models.HabitLog.user_id == user_id,
        models.HabitLog.date == log_date,
        models.HabitLog.category == "supplements",
    ).all()
    taken = set()
    for log in logs:
        key = log.habit_key.replace("supp_", "")
        if key in keys and log.value:
            taken.add(key)
    return taken


def _remove_habit(user_id: int, category: str, habit_key: str, db, log_date=None):
    db.query(models.HabitLog).filter(
        models.HabitLog.user_id == user_id,
        models.HabitLog.date == log_date or date.today(),
        models.HabitLog.category == category,
        models.HabitLog.habit_key == habit_key,
    ).delete()
    db.commit()


def _key_to_category(key: str) -> str:
    mapping = {
        "smoking": "bad_habits",
        "alcohol": "bad_habits",
        "sweets": "bad_habits",
        "fastfood": "bad_habits",
        "screen_bedtime": "bad_habits",
        "coffee": "bad_habits",
        "pre_sleep_eating": "wellbeing",
        "water": "water",
        "meditation": "wellbeing",
        "walk": "wellbeing",
        "feeling": "wellbeing",
        "subjective_stress": "wellbeing",
    }
    return mapping.get(key, "misc")


def _key_label(key: str) -> str:
    labels = {
        "smoking": "Курение",
        "alcohol": "Алкоголь",
        "sweets": "Сладкое",
        "fastfood": "Фастфуд",
        "screen_bedtime": "Экран перед сном",
        "coffee": "Кофе",
        "nutrition_sweets": "Сладкое (питание)",
        "nutrition_fastfood": "Фастфуд (питание)",
        "late_eating": "Поздний приём пищи",
        "pre_sleep_eating": "Еда за 2ч до сна",
        "nutrition_quality": "Качество питания",
        "water": "Вода",
        "meditation": "Медитация",
        "walk": "Прогулка",
        "feeling": "Самочувствие",
        "subjective_stress": "Стресс",
    }
    return labels.get(key, key)


def _back_keyboard(category: str):
    from bot.keyboards import bad_habits_menu, nutrition_menu, water_keyboard, wellbeing_menu, main_log_menu
    mapping = {
        "bad_habits": bad_habits_menu,
        "nutrition": nutrition_menu,
        "water": water_keyboard,
        "wellbeing": wellbeing_menu,
    }
    return mapping.get(category, main_log_menu)()


def get_handlers():
    from telegram.ext import CommandHandler, CallbackQueryHandler
    return [
        CommandHandler("log", cmd_log),
        CommandHandler("today", cmd_today),
        CommandHandler("stats", cmd_stats),
        CommandHandler("insight", cmd_insight),
        CommandHandler("history", cmd_history),
        CallbackQueryHandler(button_callback),
    ]

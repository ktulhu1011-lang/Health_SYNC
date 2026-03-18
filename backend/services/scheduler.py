from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal
from config import settings


def _garmin_sync_job():
    from services.garmin_sync import sync_all_users
    db = SessionLocal()
    try:
        sync_all_users(db)
    finally:
        db.close()


def _weekly_insight_job():
    from services.ai_insights import generate_insight_for_user
    import models as m
    db = SessionLocal()
    try:
        users = db.query(m.User).all()
        for user in users:
            try:
                insight = generate_insight_for_user(user.id, db, trigger_type="weekly")
                # Send to Telegram if bot token is set
                _notify_user(user, insight.insight_text)
            except Exception as e:
                print(f"[scheduler] Weekly insight error for user {user.id}: {e}")
    finally:
        db.close()


def _anomaly_check_job():
    from services.ai_insights import check_and_trigger_anomaly_insights
    db = SessionLocal()
    try:
        check_and_trigger_anomaly_insights(db)
    finally:
        db.close()


def _morning_reminder_job():
    """Optional morning sleep summary from Garmin."""
    import models as m
    db = SessionLocal()
    try:
        users = db.query(m.User).all()
        for user in users:
            user_settings = user.settings_json or {}
            if not user_settings.get("morning_reminder_enabled"):
                continue
            _send_morning_summary(user, db)
    finally:
        db.close()


def _notify_user(user, text: str):
    """Send Telegram notification to user."""
    if not user.telegram_id or not settings.telegram_bot_token:
        return
    import httpx
    try:
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        httpx.post(url, json={
            "chat_id": user.telegram_id,
            "text": f"📊 Еженедельный AI-инсайт:\n\n{text}",
            "parse_mode": "HTML",
        }, timeout=10)
    except Exception as e:
        print(f"[scheduler] Telegram notify error: {e}")


def _send_morning_summary(user, db):
    """Send morning sleep summary from Garmin."""
    from datetime import date, timedelta
    import models as m
    yesterday = date.today() - timedelta(days=1)
    garmin = db.query(m.GarminDaily).filter(
        m.GarminDaily.user_id == user.id,
        m.GarminDaily.date == yesterday
    ).first()
    if not garmin:
        return

    lines = [f"🌅 Данные сна за {yesterday.strftime('%d.%m.%Y')}:"]
    if garmin.sleep_score:
        lines.append(f"💤 Sleep score: {garmin.sleep_score}")
    if garmin.deep_sleep_sec:
        lines.append(f"🔵 Глубокий сон: {garmin.deep_sleep_sec // 60} мин")
    if garmin.rem_sleep_sec:
        lines.append(f"🟣 REM: {garmin.rem_sleep_sec // 60} мин")
    if garmin.hrv_status:
        lines.append(f"❤️ HRV: {garmin.hrv_status}")
    if garmin.resting_hr:
        lines.append(f"💗 Пульс покоя: {garmin.resting_hr} BPM")

    _notify_user(user, "\n".join(lines))


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    # Garmin sync at configured hour (default 03:00)
    scheduler.add_job(
        _garmin_sync_job,
        CronTrigger(hour=settings.garmin_sync_hour, minute=0),
        id="garmin_sync",
        replace_existing=True,
    )

    # Weekly AI insights on Sunday at 09:00
    scheduler.add_job(
        _weekly_insight_job,
        CronTrigger(day_of_week="sun", hour=9, minute=0),
        id="weekly_insight",
        replace_existing=True,
    )

    # Anomaly check daily at 10:00
    scheduler.add_job(
        _anomaly_check_job,
        CronTrigger(hour=10, minute=0),
        id="anomaly_check",
        replace_existing=True,
    )

    # Morning reminder at configured time
    reminder_time = settings.optional_morning_reminder.split(":")
    scheduler.add_job(
        _morning_reminder_job,
        CronTrigger(hour=int(reminder_time[0]), minute=int(reminder_time[1])),
        id="morning_reminder",
        replace_existing=True,
    )

    return scheduler

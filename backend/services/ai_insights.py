from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import anthropic
import models
from config import settings


INSIGHT_PROMPT = """Ты — персональный AI-аналитик здоровья. Анализируй данные и давай конкретные,
числовые инсайты на русском языке. Будь кратким и конкретным, используй числа.

Данные пользователя за последние {days} дней:

ПРИВЫЧКИ (по дням):
{habits_json}

БИОМЕТРИКА Garmin (по дням, поля: sleep_score, hrv_avg — средний HRV за ночь мс, hrv_status, resting_hr, avg_stress, body_battery, deep_sleep_min, steps, vigorous_min — минуты интенсивных нагрузок, workouts — список тренировок с типом и длительностью):
{metrics_json}

АГРЕГАТЫ (среднее "с привычкой" vs "без привычки"):
{aggregates_json}

Найди 2-3 наиболее значимые корреляции между привычками и биометрикой. Также проанализируй влияние тренировок на сон и HRV. Для каждого инсайта укажи:
- Конкретную привычку или тип тренировки и метрику
- Числовые значения ("с" vs "без")
- Количество наблюдений
- Практическую рекомендацию

Формат ответа: чёткие абзацы без markdown-заголовков. Начни с самой сильной корреляции."""


def generate_insight_for_user(user_id: int, db: Session, trigger_type: str = "on_demand") -> models.AIInsight:
    days = 30
    since = date.today() - timedelta(days=days)

    # Fetch habits
    habits = db.query(models.HabitLog).filter(
        and_(models.HabitLog.user_id == user_id, models.HabitLog.date >= since)
    ).order_by(models.HabitLog.date).all()

    # Fetch garmin metrics
    garmin = db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == user_id, models.GarminDaily.date >= since)
    ).order_by(models.GarminDaily.date).all()

    if len(garmin) < 14:
        days_remaining = 14 - len(garmin)
        insight_text = f"Продолжай заполнять данные — инсайты появятся через {days_remaining} дней. Нужно минимум 14 дней данных для анализа."
        insight = models.AIInsight(
            user_id=user_id,
            insight_text=insight_text,
            trigger_type=trigger_type,
            metrics_snapshot_json={"days_available": len(garmin)},
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)
        return insight

    # Build JSON summaries
    habits_by_date: dict = {}
    for h in habits:
        d = str(h.date)
        if d not in habits_by_date:
            habits_by_date[d] = {}
        habits_by_date[d][h.habit_key] = h.value

    # Fetch activities for the period
    activities = db.query(models.GarminActivity).filter(
        and_(models.GarminActivity.user_id == user_id, models.GarminActivity.date >= since)
    ).order_by(models.GarminActivity.date).all()

    activities_by_date: dict = {}
    for a in activities:
        d = str(a.date)
        if d not in activities_by_date:
            activities_by_date[d] = []
        activities_by_date[d].append({
            "type": a.activity_type,
            "duration_min": round(a.duration_sec / 60) if a.duration_sec else None,
            "avg_hr": a.avg_hr,
            "calories": a.calories,
            "training_effect": a.training_effect,
        })

    metrics_by_date = {}
    for g in garmin:
        d = str(g.date)
        metrics_by_date[d] = {
            "sleep_score": g.sleep_score,
            "hrv_avg": g.hrv_last_night_avg,
            "hrv_status": g.hrv_status,
            "resting_hr": g.resting_hr,
            "avg_stress": g.avg_stress,
            "body_battery": g.body_battery_charged,
            "deep_sleep_min": round(g.deep_sleep_sec / 60, 1) if g.deep_sleep_sec else None,
            "steps": g.steps,
            "vigorous_min": g.vigorous_intensity_minutes,
            "workouts": activities_by_date.get(d, []),
        }

    # Compute aggregates
    aggregates = _compute_aggregates(habits_by_date, metrics_by_date)

    import json
    prompt = INSIGHT_PROMPT.format(
        days=days,
        habits_json=json.dumps(habits_by_date, ensure_ascii=False, default=str)[:3000],
        metrics_json=json.dumps(metrics_by_date, ensure_ascii=False, default=str)[:3500],
        aggregates_json=json.dumps(aggregates, ensure_ascii=False, default=str)[:2000],
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    insight_text = message.content[0].text

    insight = models.AIInsight(
        user_id=user_id,
        insight_text=insight_text,
        trigger_type=trigger_type,
        metrics_snapshot_json={"aggregates": aggregates, "garmin_days": len(garmin)},
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


def _compute_aggregates(habits_by_date: dict, metrics_by_date: dict) -> dict:
    all_habit_keys: set = set()
    for day_habits in habits_by_date.values():
        all_habit_keys.update(day_habits.keys())

    metric_fields = ["sleep_score", "hrv_avg", "resting_hr", "avg_stress", "body_battery", "steps", "vigorous_min"]
    aggregates = {}

    for habit_key in all_habit_keys:
        aggregates[habit_key] = {}
        for metric in metric_fields:
            vals_with, vals_without = [], []
            for d, mvals in metrics_by_date.items():
                val = mvals.get(metric)
                if val is None:
                    continue
                try:
                    val = float(val)
                except (TypeError, ValueError):
                    continue
                has_habit = d in habits_by_date and habit_key in habits_by_date[d]
                if has_habit and _is_active(habits_by_date[d][habit_key]):
                    vals_with.append(val)
                else:
                    vals_without.append(val)
            if vals_with and vals_without:
                aggregates[habit_key][metric] = {
                    "avg_with": round(sum(vals_with) / len(vals_with), 1),
                    "avg_without": round(sum(vals_without) / len(vals_without), 1),
                    "delta": round(sum(vals_with) / len(vals_with) - sum(vals_without) / len(vals_without), 1),
                    "n_with": len(vals_with),
                    "n_without": len(vals_without),
                }
    return aggregates


def _is_active(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        no_values = {"нет", "не курил", "не пил", "не ел", "0", "no", "false"}
        return value.lower().replace(" ✅", "").strip() not in no_values
    if isinstance(value, dict):
        try:
            return int(value.get("count", 0)) > 0
        except (TypeError, ValueError):
            return bool(value)
    return False


def check_and_trigger_anomaly_insights(db: Session):
    """Check for anomalies and trigger insights if needed."""
    from datetime import datetime
    users = db.query(models.User).all()
    for user in users:
        try:
            _check_user_anomalies(user.id, db)
        except Exception as e:
            print(f"[ai_insights] Anomaly check error for user {user.id}: {e}")


def _check_user_anomalies(user_id: int, db: Session):
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    recent = db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == user_id,
             models.GarminDaily.date == yesterday)
    ).first()

    if not recent:
        return

    week_avg = db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == user_id,
             models.GarminDaily.date >= week_ago,
             models.GarminDaily.date < yesterday)
    ).all()

    if not week_avg:
        return

    avg_sleep = [r.sleep_score for r in week_avg if r.sleep_score]
    avg_hr = [r.resting_hr for r in week_avg if r.resting_hr]

    trigger = False
    if avg_sleep and recent.sleep_score:
        avg = sum(avg_sleep) / len(avg_sleep)
        if recent.sleep_score < avg * 0.85:  # 15% drop
            trigger = True

    if avg_hr and recent.resting_hr:
        avg = sum(avg_hr) / len(avg_hr)
        if recent.resting_hr > avg * 1.10:  # 10% increase
            trigger = True

    if trigger:
        generate_insight_for_user(user_id, db, trigger_type="triggered")

from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import anthropic
import models
import csv
import io
from config import settings


INSIGHT_PROMPT = """Ты — персональный AI-аналитик здоровья и биохакинга. Твоя задача — дать глубокий, детальный анализ данных пользователя и выдать максимально полезные, персонализированные инсайты на русском языке.

Данные пользователя за последние {days} дней ({date_from} — {date_to}):

БИОМЕТРИКА Garmin (CSV: date,sleep_score,sleep_start,sleep_end,deep_min,rem_min,light_min,awake_min,hrv_avg,hrv_status,hrv_baseline,resting_hr,avg_stress,body_battery_charged,body_battery_drained,steps,vigorous_min,moderate_min,workouts):
{metrics_csv}

ПРИВЫЧКИ (CSV: date,habit_key,value):
{habits_csv}

АГРЕГАТЫ по привычкам (habit_key,metric,avg_with,avg_without,delta,n_with,n_without):
{aggregates_csv}

Проведи полный анализ по следующим блокам:

1. КОРРЕЛЯЦИИ ПРИВЫЧЕК И БИОМЕТРИКИ
Найди все значимые корреляции между привычками и биометрикой. Для каждой укажи конкретные числа ("с" vs "без"), количество наблюдений, и оцени статистическую надёжность. Начни с самых сильных эффектов.

2. АНАЛИЗ ТРЕНИРОВОК
Как разные типы тренировок влияют на сон, HRV, пульс покоя и Body Battery на следующий день? Есть ли оптимальное время или интенсивность?

3. ПАТТЕРНЫ СНА
Что коррелирует с лучшим sleep score и глубоким сном? Анализируй поведение вечером (экран, еда, стресс, алкоголь).

4. ВОССТАНОВЛЕНИЕ И СТРЕСС
Динамика HRV, Body Battery и пульса покоя. Какие привычки помогают восстановлению? Есть ли признаки перетренированности или хронического стресса?

5. ТОП-3 РЕКОМЕНДАЦИИ
Конкретные, измеримые изменения с наибольшим ожидаемым эффектом на основе данных. Укажи какую метрику и на сколько ожидаешь улучшить.

Используй числа везде где это возможно. Пиши развёрнуто и детально — это персональный отчёт здоровья, а не краткая сводка. Формат: чёткие блоки с заголовками каждого раздела."""


def generate_insight_for_user(user_id: int, db: Session, trigger_type: str = "on_demand", days: int = 30) -> models.AIInsight:
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
        row = {
            "sleep_score": g.sleep_score,
            "sleep_start": g.sleep_start.strftime("%H:%M") if g.sleep_start else None,
            "sleep_end": g.sleep_end.strftime("%H:%M") if g.sleep_end else None,
            "deep_min": round(g.deep_sleep_sec / 60) if g.deep_sleep_sec else None,
            "rem_min": round(g.rem_sleep_sec / 60) if g.rem_sleep_sec else None,
            "light_min": round(g.light_sleep_sec / 60) if g.light_sleep_sec else None,
            "awake_min": round(g.awake_sec / 60) if g.awake_sec else None,
            "hrv_avg": g.hrv_last_night_avg,
            "hrv_status": g.hrv_status,
            "hrv_baseline": f"{g.hrv_baseline_low}-{g.hrv_baseline_high}" if g.hrv_baseline_low else None,
            "resting_hr": g.resting_hr,
            "avg_stress": g.avg_stress,
            "body_battery_charged": g.body_battery_charged,
            "body_battery_drained": g.body_battery_drained,
            "steps": g.steps,
            "vigorous_min": g.vigorous_intensity_minutes,
            "moderate_min": g.moderate_intensity_minutes,
            "workouts": activities_by_date.get(d, []) or None,
        }
        # Drop None values to save space
        metrics_by_date[d] = {k: v for k, v in row.items() if v is not None}

    # Compute aggregates
    aggregates = _compute_aggregates(habits_by_date, metrics_by_date)

    date_from = since.strftime("%d.%m.%Y")
    date_to = date.today().strftime("%d.%m.%Y")
    prompt = INSIGHT_PROMPT.format(
        days=days,
        date_from=date_from,
        date_to=date_to,
        metrics_csv=_build_metrics_csv(metrics_by_date),
        habits_csv=_build_habits_csv(habits_by_date),
        aggregates_csv=_build_aggregates_csv(aggregates),
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    insight_text = message.content[0].text

    insight = models.AIInsight(
        user_id=user_id,
        insight_text=insight_text,
        trigger_type=trigger_type,
        metrics_snapshot_json={"aggregates": aggregates, "garmin_days": len(garmin), "days_period": days},
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


ASK_PROMPT = """Ты — персональный AI-аналитик здоровья. Отвечай на русском языке, конкретно и с цифрами.

Данные пользователя за последние {days} дней ({date_from} — {date_to}):

БИОМЕТРИКА Garmin (CSV: date,sleep_score,sleep_start,sleep_end,deep_min,rem_min,light_min,awake_min,hrv_avg,hrv_status,resting_hr,avg_stress,body_battery_charged,body_battery_drained,steps,vigorous_min,workouts):
{metrics_csv}

ПРИВЫЧКИ (CSV: date,habit_key,value):
{habits_csv}

АГРЕГАТЫ (habit_key,metric,avg_with,avg_without,delta,n_with,n_without):
{aggregates_csv}

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {question}

Ответь на вопрос максимально точно, опираясь на реальные данные выше. Используй конкретные числа из данных. Если данных недостаточно для ответа — честно скажи об этом."""


def ask_question_for_user(user_id: int, question: str, db: Session, days: int = 30) -> str:
    """Answer a user's custom question based on their health data."""
    since = date.today() - timedelta(days=days)

    habits = db.query(models.HabitLog).filter(
        and_(models.HabitLog.user_id == user_id, models.HabitLog.date >= since)
    ).order_by(models.HabitLog.date).all()

    garmin = db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == user_id, models.GarminDaily.date >= since)
    ).order_by(models.GarminDaily.date).all()

    habits_by_date: dict = {}
    for h in habits:
        d = str(h.date)
        if d not in habits_by_date:
            habits_by_date[d] = {}
        habits_by_date[d][h.habit_key] = h.value

    activities = db.query(models.GarminActivity).filter(
        and_(models.GarminActivity.user_id == user_id, models.GarminActivity.date >= since)
    ).all()
    activities_by_date: dict = {}
    for a in activities:
        d = str(a.date)
        if d not in activities_by_date:
            activities_by_date[d] = []
        activities_by_date[d].append({"type": a.activity_type, "duration_min": round(a.duration_sec / 60) if a.duration_sec else None})

    metrics_by_date = {}
    for g in garmin:
        d = str(g.date)
        row = {
            "sleep_score": g.sleep_score,
            "sleep_start": g.sleep_start.strftime("%H:%M") if g.sleep_start else None,
            "sleep_end": g.sleep_end.strftime("%H:%M") if g.sleep_end else None,
            "deep_min": round(g.deep_sleep_sec / 60) if g.deep_sleep_sec else None,
            "rem_min": round(g.rem_sleep_sec / 60) if g.rem_sleep_sec else None,
            "light_min": round(g.light_sleep_sec / 60) if g.light_sleep_sec else None,
            "awake_min": round(g.awake_sec / 60) if g.awake_sec else None,
            "hrv_avg": g.hrv_last_night_avg,
            "hrv_status": g.hrv_status,
            "resting_hr": g.resting_hr,
            "avg_stress": g.avg_stress,
            "body_battery_charged": g.body_battery_charged,
            "body_battery_drained": g.body_battery_drained,
            "steps": g.steps,
            "vigorous_min": g.vigorous_intensity_minutes,
            "workouts": activities_by_date.get(d, []) or None,
        }
        metrics_by_date[d] = {k: v for k, v in row.items() if v is not None}

    aggregates = _compute_aggregates(habits_by_date, metrics_by_date)
    date_from = since.strftime("%d.%m.%Y")
    date_to = date.today().strftime("%d.%m.%Y")

    prompt = ASK_PROMPT.format(
        days=days,
        date_from=date_from,
        date_to=date_to,
        question=question,
        metrics_csv=_build_metrics_csv(metrics_by_date),
        habits_csv=_build_habits_csv(habits_by_date),
        aggregates_csv=_build_aggregates_csv(aggregates),
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _build_metrics_csv(metrics_by_date: dict, max_chars: int = 20000) -> str:
    fields = [
        "sleep_score", "sleep_start", "sleep_end",
        "deep_min", "rem_min", "light_min", "awake_min",
        "hrv_avg", "hrv_status", "hrv_baseline",
        "resting_hr", "avg_stress",
        "body_battery_charged", "body_battery_drained",
        "steps", "vigorous_min", "moderate_min", "workouts",
    ]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["date"] + fields)
    for d in sorted(metrics_by_date.keys()):
        row = metrics_by_date[d]
        workouts = row.get("workouts")
        workout_str = ""
        if workouts:
            workout_str = "|".join(
                f"{wk.get('type','?')}({wk.get('duration_min','?')}min)" for wk in workouts
            )
        vals = [row.get(f, "") for f in fields[:-1]] + [workout_str]
        w.writerow([d] + vals)
    result = out.getvalue()
    if len(result) > max_chars:
        lines = result.splitlines()
        header = lines[0]
        data_lines = lines[1:]
        # Drop oldest days
        while len("\n".join([header] + data_lines)) > max_chars and len(data_lines) > 14:
            data_lines = data_lines[1:]
        result = "\n".join([header] + data_lines)
    return result


def _build_habits_csv(habits_by_date: dict, max_chars: int = 15000) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["date", "habit_key", "value"])
    for d in sorted(habits_by_date.keys()):
        for key, val in habits_by_date[d].items():
            if isinstance(val, dict):
                val = val.get("count", val)
            w.writerow([d, key, val])
    result = out.getvalue()
    if len(result) > max_chars:
        lines = result.splitlines()
        header = lines[0]
        data_lines = lines[1:]
        while len("\n".join([header] + data_lines)) > max_chars and len(data_lines) > 20:
            # Find first date and drop all its rows
            first_date = data_lines[0].split(",")[0]
            data_lines = [l for l in data_lines if not l.startswith(first_date + ",")]
        result = "\n".join([header] + data_lines)
    return result


def _build_aggregates_csv(aggregates: dict, max_chars: int = 8000) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["habit_key", "metric", "avg_with", "avg_without", "delta", "n_with", "n_without"])
    rows = []
    for habit_key, metrics in aggregates.items():
        for metric, vals in metrics.items():
            rows.append([
                habit_key, metric,
                vals["avg_with"], vals["avg_without"], vals["delta"],
                vals["n_with"], vals["n_without"],
            ])
    # Sort by abs delta desc
    rows.sort(key=lambda r: abs(r[4]), reverse=True)
    for row in rows:
        w.writerow(row)
    return out.getvalue()[:max_chars]


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

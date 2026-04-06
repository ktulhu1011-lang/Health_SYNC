import csv
import io
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import get_db
import models
import auth as auth_utils

router = APIRouter(prefix="/api/export", tags=["export"])

GARMIN_FIELDS = [
    "sleep_score", "deep_sleep_sec", "rem_sleep_sec", "light_sleep_sec", "awake_sec",
    "sleep_start", "sleep_end",
    "hrv_last_night_avg", "hrv_weekly_avg", "hrv_baseline_low", "hrv_baseline_high",
    "hrv_status", "hrv_peak",
    "resting_hr", "avg_hr", "avg_stress", "max_stress", "stress_qualifier",
    "body_battery_charged", "body_battery_drained",
    "steps", "active_calories",
    "moderate_intensity_minutes", "vigorous_intensity_minutes",
    "avg_spo2", "min_spo2",
]

HABIT_KEYS_ORDER = [
    "feeling", "subjective_stress", "smoking", "alcohol", "sweets", "fastfood",
    "screen_bedtime", "coffee", "water", "meditation", "walk",
    "nutrition_quality", "late_eating", "pre_sleep_eating", "had_workout",
    "supp_magnesium", "supp_vitamin_d", "supp_vitamin_c", "supp_zinc",
    "supp_omega3", "supp_ashwagandha", "supp_theanine", "supp_melatonin",
    "supp_5htp", "supp_glycine", "supp_coq10", "supp_b_complex",
]


def _habit_value_str(val) -> str:
    if val is None:
        return ""
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        no_vals = {"нет", "не курил", "не пил", "не ел", "0", "no", "false",
                   "нет ✅", "не курил ✅", "не пил ✅", "ask_count"}
        return "0" if val.lower() in no_vals else val
    if isinstance(val, dict):
        count = val.get("count", "")
        return str(count) if count else ""
    return str(val)


@router.get("/csv")
def export_csv(
    days: int = Query(365, ge=1, le=3650),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    since = date.today() - timedelta(days=days)

    garmin_rows = db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == current_user.id,
             models.GarminDaily.date >= since)
    ).order_by(models.GarminDaily.date).all()

    habit_rows = db.query(models.HabitLog).filter(
        and_(models.HabitLog.user_id == current_user.id,
             models.HabitLog.date >= since)
    ).all()

    activity_rows = db.query(models.GarminActivity).filter(
        and_(models.GarminActivity.user_id == current_user.id,
             models.GarminActivity.date >= since)
    ).all()

    # Index habits by date
    habits_by_date: dict = {}
    all_habit_keys: set = set()
    for h in habit_rows:
        d = str(h.date)
        if d not in habits_by_date:
            habits_by_date[d] = {}
        habits_by_date[d][h.habit_key] = h.value
        all_habit_keys.add(h.habit_key)

    # Synthetic workout habit
    for act in activity_rows:
        d = str(act.date)
        if d not in habits_by_date:
            habits_by_date[d] = {}
        if "had_workout" not in habits_by_date[d]:
            habits_by_date[d]["had_workout"] = 1
        all_habit_keys.add("had_workout")

    # Final habit columns: known order first, then any extras
    extra_keys = sorted(all_habit_keys - set(HABIT_KEYS_ORDER))
    habit_columns = [k for k in HABIT_KEYS_ORDER if k in all_habit_keys] + extra_keys

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["date"] + GARMIN_FIELDS + habit_columns)

    # Collect all dates (union of garmin + habit dates)
    all_dates = sorted(set(
        [str(r.date) for r in garmin_rows] + list(habits_by_date.keys())
    ))
    garmin_by_date = {str(r.date): r for r in garmin_rows}

    for d in all_dates:
        g = garmin_by_date.get(d)
        garmin_vals = []
        for field in GARMIN_FIELDS:
            val = getattr(g, field, None) if g else None
            if val is None:
                garmin_vals.append("")
            else:
                garmin_vals.append(str(val))

        habit_vals = []
        day_habits = habits_by_date.get(d, {})
        for key in habit_columns:
            habit_vals.append(_habit_value_str(day_habits.get(key)))

        writer.writerow([d] + garmin_vals + habit_vals)

    output.seek(0)
    filename = f"healthsync_{current_user.username}_{date.today()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

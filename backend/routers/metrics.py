from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, timedelta
from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/daily", response_model=List[schemas.GarminDailyOut])
def get_daily(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    since = date.today() - timedelta(days=days)
    return db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == current_user.id,
             models.GarminDaily.date >= since)
    ).order_by(models.GarminDaily.date.desc()).all()


@router.get("/daily/{target_date}", response_model=Optional[schemas.GarminDailyOut])
def get_daily_by_date(
    target_date: date,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    rec = db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == current_user.id,
             models.GarminDaily.date == target_date)
    ).first()
    return rec


@router.post("/garmin/credentials")
def save_garmin_credentials(
    body: schemas.GarminCredentials,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    from services.garmin_sync import encrypt_value
    current_user.garmin_email_enc = encrypt_value(body.email)
    current_user.garmin_token_enc = encrypt_value(body.password)
    db.commit()
    return {"status": "saved"}


@router.post("/garmin/inject-tokens")
def inject_garmin_tokens(
    body: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    """Upload garth tokens generated from a non-banned IP (e.g. local machine)."""
    import time
    tokens = body.get("tokens")
    if not tokens or not isinstance(tokens, dict):
        raise HTTPException(status_code=400, detail="tokens dict required")
    s = dict(current_user.settings_json or {})
    s["garmin_tokens"] = tokens
    s["garmin_token_ts"] = time.time()
    current_user.settings_json = s
    db.commit()
    return {"status": "ok", "files": list(tokens.keys())}


@router.get("/garmin/export-tokens")
def export_garmin_tokens(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    """Export stored garth token files so they can be refreshed on a non-banned IP."""
    tokens = (current_user.settings_json or {}).get("garmin_tokens")
    if not tokens:
        raise HTTPException(status_code=404, detail="No tokens stored")
    return {"tokens": tokens}


@router.get("/garmin/debug")
def debug_garmin(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    """Debug: check garmin session, display_name and test a simple API call."""
    from services.garmin_sync import decrypt_value, _load_tokens, _garmin_client_cache
    import tempfile, os, shutil
    from garminconnect import Garmin
    result = {}
    try:
        email = decrypt_value(current_user.garmin_email_enc)
        result["email"] = email
        token_dir = _load_tokens(current_user.id, db)
        result["has_tokens"] = bool(token_dir)
        if token_dir:
            client = Garmin(email, "")
            client.garth.load(token_dir)
            shutil.rmtree(token_dir, ignore_errors=True)
            try:
                profile = client.garth.profile
                result["profile_keys"] = list(profile.keys()) if profile else []
                client.display_name = profile.get("displayName") or profile.get("userName")
                result["display_name"] = client.display_name
            except Exception as e:
                result["profile_error"] = str(e)
            try:
                from datetime import date, timedelta
                yesterday = (date.today() - timedelta(days=1)).isoformat()
                stats = client.get_stats(yesterday)
                result["stats_keys"] = list(stats.keys()) if stats else []
                result["stats_sample"] = {k: stats[k] for k in list(stats.keys())[:5]} if stats else {}
            except Exception as e:
                result["stats_error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    return result


@router.post("/garmin/sync")
def manual_sync(
    days_back: int = Query(1, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    from services.garmin_sync import sync_user
    try:
        count = sync_user(current_user.id, db, days_back=days_back)
        return {"status": "ok", "metrics_fetched": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlations")
def get_correlations(
    days: int = Query(30, ge=14, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    since = date.today() - timedelta(days=days)

    garmin_rows = db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == current_user.id,
             models.GarminDaily.date >= since)
    ).all()
    garmin_by_date = {str(r.date): r for r in garmin_rows}

    habit_rows = db.query(models.HabitLog).filter(
        and_(models.HabitLog.user_id == current_user.id,
             models.HabitLog.date >= since)
    ).all()

    # Group habits by (date, habit_key)
    habits_by_date: dict = {}
    for h in habit_rows:
        d = str(h.date)
        if d not in habits_by_date:
            habits_by_date[d] = {}
        habits_by_date[d][h.habit_key] = h.value

    # Add synthetic "had_workout" habit from Activity table
    activity_rows = db.query(models.GarminActivity).filter(
        and_(models.GarminActivity.user_id == current_user.id,
             models.GarminActivity.date >= since)
    ).all()
    for act in activity_rows:
        d = str(act.date)
        if d not in habits_by_date:
            habits_by_date[d] = {}
        habits_by_date[d]["had_workout"] = 1

    # Collect unique habit keys
    all_habit_keys: set = set()
    for day_habits in habits_by_date.values():
        all_habit_keys.update(day_habits.keys())

    metrics_fields = [
        "sleep_score", "hrv_last_night_avg", "resting_hr",
        "avg_stress", "body_battery_charged", "steps",
    ]
    results = []

    for habit_key in all_habit_keys:
        # Skip supplement keys — too granular for correlations
        if habit_key.startswith("supp_"):
            continue
        for metric in metrics_fields:
            vals_with = []
            vals_without = []
            for d, garmin in garmin_by_date.items():
                metric_val = getattr(garmin, metric, None)
                if metric_val is None:
                    continue
                try:
                    metric_val = float(metric_val)
                except (TypeError, ValueError):
                    continue
                has_habit = d in habits_by_date and habit_key in habits_by_date[d]
                if has_habit:
                    val = habits_by_date[d][habit_key]
                    if _is_habit_active(val):
                        vals_with.append(metric_val)
                    else:
                        vals_without.append(metric_val)
                else:
                    vals_without.append(metric_val)

            if len(vals_with) >= 2 and len(vals_without) >= 2:
                avg_with = sum(vals_with) / len(vals_with)
                avg_without = sum(vals_without) / len(vals_without)
                delta = avg_with - avg_without
                results.append({
                    "habit_key": habit_key,
                    "metric": metric,
                    "avg_with": round(avg_with, 2),
                    "avg_without": round(avg_without, 2),
                    "delta": round(delta, 2),
                    "days_with": len(vals_with),
                    "days_without": len(vals_without),
                })

    # Sort by absolute delta descending
    results.sort(key=lambda x: abs(x["delta"]), reverse=True)
    return results


def _is_habit_active(value) -> bool:
    """Check if a habit value represents an 'active' state (not 'no/none/0')."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        no_values = {"нет", "не курил", "не пил", "не ел", "0", "no", "false",
                     "нет ✅", "не курил ✅", "не пил ✅", "ask_count"}
        return value.lower() not in no_values
    if isinstance(value, dict):
        try:
            return int(value.get("count", 0)) > 0
        except (TypeError, ValueError):
            return False
    return False

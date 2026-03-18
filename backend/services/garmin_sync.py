import base64
import os
import time
from datetime import date, timedelta, datetime, timezone
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.orm import Session
import models
from config import settings


def _get_key() -> bytes:
    key_b64 = settings.garmin_encryption_key
    if not key_b64:
        raise ValueError("GARMIN_ENCRYPTION_KEY not set")
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError("GARMIN_ENCRYPTION_KEY must be 32 bytes (base64-encoded)")
    return key


def encrypt_value(plaintext: str) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_value(ciphertext: str) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    raw = base64.b64decode(ciphertext)
    nonce, ct = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()


def sync_user(user_id: int, db: Session, days_back: int = 1) -> int:
    """Sync Garmin data for a user. Returns number of metrics fetched."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.garmin_email_enc or not user.garmin_token_enc:
        raise ValueError(f"User {user_id} has no Garmin credentials")

    email = decrypt_value(user.garmin_email_enc)
    password = decrypt_value(user.garmin_token_enc)

    try:
        from garminconnect import Garmin
        client = Garmin(email, password)
        client.login()
    except Exception as e:
        _log_sync(db, user_id, "error", str(e))
        raise

    metrics_count = 0
    for i in range(days_back):
        target = date.today() - timedelta(days=i + 1)
        try:
            metrics_count += _sync_day(client, user_id, target, db)
        except Exception as e:
            print(f"[garmin_sync] Error syncing {target} for user {user_id}: {e}")

    _log_sync(db, user_id, "ok", metrics_fetched=metrics_count)
    return metrics_count


def _sync_day(client, user_id: int, target: date, db: Session) -> int:
    date_str = target.isoformat()
    count = 0

    # --- Daily stats (sleep, stress, steps, etc.) ---
    daily_data = {}
    sleep_data = {}

    try:
        stats = client.get_stats(date_str)
        daily_data.update(stats)
        count += 1
    except Exception as e:
        print(f"[garmin_sync] stats error {date_str}: {e}")

    try:
        sleep = client.get_sleep_data(date_str)
        sleep_data = sleep.get("dailySleepDTO", {})
        count += 1
    except Exception as e:
        print(f"[garmin_sync] sleep error {date_str}: {e}")

    # Upsert garmin_daily
    existing = db.query(models.GarminDaily).filter(
        models.GarminDaily.user_id == user_id,
        models.GarminDaily.date == target
    ).first()
    if not existing:
        existing = models.GarminDaily(user_id=user_id, date=target)
        db.add(existing)

    existing.sleep_score = sleep_data.get("sleepScores", {}).get("overall", {}).get("value") or sleep_data.get("sleepScore")
    existing.deep_sleep_sec = sleep_data.get("deepSleepSeconds")
    existing.rem_sleep_sec = sleep_data.get("remSleepSeconds")
    existing.light_sleep_sec = sleep_data.get("lightSleepSeconds")
    existing.awake_sec = sleep_data.get("awakeSleepSeconds")

    start_ts = sleep_data.get("sleepStartTimestampGMT")
    end_ts = sleep_data.get("sleepEndTimestampGMT")
    if start_ts:
        existing.sleep_start = datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc).replace(tzinfo=None)
    if end_ts:
        existing.sleep_end = datetime.fromtimestamp(end_ts / 1000, tz=timezone.utc).replace(tzinfo=None)

    existing.hrv_status = sleep_data.get("hrvStatus")
    existing.hrv_peak = sleep_data.get("hrv5MinHigh")

    # --- HRV from dedicated endpoint ---
    try:
        hrv_data = client.get_hrv_data(date_str)
        hrv_summary = hrv_data.get("hrvSummary", {}) if isinstance(hrv_data, dict) else {}
        if hrv_summary:
            existing.hrv_last_night_avg = hrv_summary.get("lastNightAvg")
            existing.hrv_weekly_avg = hrv_summary.get("weeklyAvg")
            existing.hrv_status = hrv_summary.get("status") or existing.hrv_status
            baseline = hrv_summary.get("baseline", {})
            existing.hrv_baseline_low = baseline.get("balancedLow")
            existing.hrv_baseline_high = baseline.get("balancedUpper")
    except Exception as e:
        print(f"[garmin_sync] HRV error {date_str}: {e}")
    existing.resting_hr = daily_data.get("restingHeartRate")
    existing.avg_stress = daily_data.get("averageStressLevel")
    existing.max_stress = daily_data.get("maxStressLevel")
    existing.stress_qualifier = daily_data.get("stressQualifier")
    existing.body_battery_charged = daily_data.get("bodyBatteryChargedValue")
    existing.body_battery_drained = daily_data.get("bodyBatteryDrainedValue")
    existing.steps = daily_data.get("totalSteps")
    existing.active_calories = daily_data.get("activeKilocalories")
    existing.moderate_intensity_minutes = daily_data.get("moderateIntensityMinutes")
    existing.vigorous_intensity_minutes = daily_data.get("vigorousIntensityMinutes")
    existing.avg_spo2 = daily_data.get("averageSpO2Value")
    existing.min_spo2 = daily_data.get("minSpO2Value")
    existing.raw_json = {"stats": daily_data, "sleep": sleep_data}

    db.commit()

    # --- Intraday HR ---
    try:
        hr_data = client.get_heart_rates(date_str)
        hr_values = hr_data.get("heartRateValues", [])
        if hr_values:
            # Delete existing intraday for this day
            db.query(models.HeartRateIntraday).filter(
                models.HeartRateIntraday.user_id == user_id,
                models.HeartRateIntraday.date == target
            ).delete()

            for entry in hr_values:
                if entry and len(entry) == 2 and entry[0] and entry[1]:
                    ts = datetime.fromtimestamp(entry[0] / 1000, tz=timezone.utc)
                    db.add(models.HeartRateIntraday(
                        user_id=user_id,
                        date=target,
                        timestamp=ts,
                        bpm=entry[1]
                    ))
            db.commit()
            count += 1

        # avg_hr from intraday
        if hr_values:
            valid_bpms = [e[1] for e in hr_values if e and len(e) == 2 and e[1]]
            if valid_bpms:
                existing.avg_hr = int(sum(valid_bpms) / len(valid_bpms))
                db.commit()

    except Exception as e:
        print(f"[garmin_sync] intraday HR error {date_str}: {e}")

    # --- Activities ---
    try:
        activities = client.get_activities_by_date(date_str, date_str)
        for act in activities:
            garmin_id = act.get("activityId")
            if not garmin_id:
                continue
            existing_act = db.query(models.GarminActivity).filter(
                models.GarminActivity.garmin_activity_id == garmin_id
            ).first()
            if existing_act:
                continue
            db.add(models.GarminActivity(
                user_id=user_id,
                garmin_activity_id=garmin_id,
                date=target,
                activity_type=act.get("activityType", {}).get("typeKey"),
                duration_sec=int(act.get("duration", 0)),
                avg_hr=act.get("averageHR"),
                max_hr=act.get("maxHR"),
                calories=act.get("calories"),
                training_effect=act.get("trainingEffectLabel"),
                aerobic_training_effect=act.get("aerobicTrainingEffect"),
                distance_meters=act.get("distance"),
                hr_zones_json=act.get("heartRateZones"),
            ))
        db.commit()
        count += 1
    except Exception as e:
        print(f"[garmin_sync] activities error {date_str}: {e}")

    return count


def _log_sync(db: Session, user_id: int, status: str, error_message: str = None, metrics_fetched: int = None):
    log = models.SyncLog(
        user_id=user_id,
        status=status,
        error_message=error_message,
        metrics_fetched=metrics_fetched,
    )
    db.add(log)
    db.commit()


def sync_all_users(db: Session):
    """Called by scheduler at 03:00."""
    users = db.query(models.User).filter(
        models.User.garmin_email_enc.isnot(None)
    ).all()
    for user in users:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                sync_user(user.id, db, days_back=2)
                break
            except Exception as e:
                print(f"[garmin_sync] Attempt {attempt+1}/{max_retries} failed for user {user.id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3600)  # Wait 1 hour before retry

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Float, Text, Boolean,
    ForeignKey, BigInteger, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    garmin_email_enc = Column(Text, nullable=True)
    garmin_token_enc = Column(Text, nullable=True)
    settings_json = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())

    habit_logs = relationship("HabitLog", back_populates="user")
    habit_definitions = relationship("HabitDefinition", back_populates="user")
    garmin_daily = relationship("GarminDaily", back_populates="user")
    heart_rate_intraday = relationship("HeartRateIntraday", back_populates="user")
    garmin_activities = relationship("GarminActivity", back_populates="user")
    ai_insights = relationship("AIInsight", back_populates="user")
    sync_logs = relationship("SyncLog", back_populates="user")


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    logged_at = Column(DateTime, server_default=func.now())
    category = Column(String(50), nullable=False)
    habit_key = Column(String(100), nullable=False)
    value = Column(JSONB, nullable=False)

    user = relationship("User", back_populates="habit_logs")


class HabitDefinition(Base):
    __tablename__ = "habit_definitions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)  # select, bool, number
    options_json = Column(JSONB, default=[])
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    user = relationship("User", back_populates="habit_definitions")


class GarminDaily(Base):
    __tablename__ = "garmin_daily"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    sleep_score = Column(Integer, nullable=True)
    deep_sleep_sec = Column(Integer, nullable=True)
    rem_sleep_sec = Column(Integer, nullable=True)
    light_sleep_sec = Column(Integer, nullable=True)
    awake_sec = Column(Integer, nullable=True)
    sleep_start = Column(DateTime, nullable=True)
    sleep_end = Column(DateTime, nullable=True)
    hrv_status = Column(String(20), nullable=True)
    hrv_last_night_avg = Column(Integer, nullable=True)
    hrv_weekly_avg = Column(Integer, nullable=True)
    hrv_baseline_low = Column(Integer, nullable=True)
    hrv_baseline_high = Column(Integer, nullable=True)
    hrv_peak = Column(Float, nullable=True)
    resting_hr = Column(Integer, nullable=True)
    avg_hr = Column(Integer, nullable=True)
    avg_stress = Column(Integer, nullable=True)
    max_stress = Column(Integer, nullable=True)
    stress_qualifier = Column(String(50), nullable=True)
    body_battery_charged = Column(Integer, nullable=True)
    body_battery_drained = Column(Integer, nullable=True)
    steps = Column(Integer, nullable=True)
    active_calories = Column(Integer, nullable=True)
    moderate_intensity_minutes = Column(Integer, nullable=True)
    vigorous_intensity_minutes = Column(Integer, nullable=True)
    avg_spo2 = Column(Float, nullable=True)
    min_spo2 = Column(Float, nullable=True)
    raw_json = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="garmin_daily")


class HeartRateIntraday(Base):
    __tablename__ = "heart_rate_intraday"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    bpm = Column(Integer, nullable=False)

    user = relationship("User", back_populates="heart_rate_intraday")


class GarminActivity(Base):
    __tablename__ = "garmin_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    garmin_activity_id = Column(BigInteger, unique=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    activity_type = Column(String(100), nullable=True)
    duration_sec = Column(Integer, nullable=True)
    avg_hr = Column(Integer, nullable=True)
    max_hr = Column(Integer, nullable=True)
    calories = Column(Integer, nullable=True)
    training_effect = Column(String(50), nullable=True)
    aerobic_training_effect = Column(Float, nullable=True)
    distance_meters = Column(Float, nullable=True)
    hr_zones_json = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="garmin_activities")


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime, server_default=func.now())
    insight_text = Column(Text, nullable=False)
    trigger_type = Column(String(50), nullable=False)  # weekly, on_demand, triggered
    metrics_snapshot_json = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="ai_insights")


class SyncLog(Base):
    __tablename__ = "sync_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sync_at = Column(DateTime, server_default=func.now())
    status = Column(String(10), nullable=False)  # ok / error
    error_message = Column(Text, nullable=True)
    metrics_fetched = Column(Integer, nullable=True)

    user = relationship("User", back_populates="sync_logs")

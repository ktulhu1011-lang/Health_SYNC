from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import date, datetime


# Auth
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    name: Optional[str]
    telegram_id: Optional[int]

    class Config:
        from_attributes = True


# Habits
class HabitLogCreate(BaseModel):
    date: date
    category: str
    habit_key: str
    value: Any


class HabitLogOut(BaseModel):
    id: int
    date: date
    logged_at: datetime
    category: str
    habit_key: str
    value: Any

    class Config:
        from_attributes = True


class HabitDefinitionOut(BaseModel):
    id: int
    key: str
    label: str
    category: str
    type: str
    options_json: List[Any]
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True


# Garmin Daily
class GarminDailyOut(BaseModel):
    date: date
    sleep_score: Optional[int]
    deep_sleep_sec: Optional[int]
    rem_sleep_sec: Optional[int]
    light_sleep_sec: Optional[int]
    awake_sec: Optional[int]
    sleep_start: Optional[datetime]
    sleep_end: Optional[datetime]
    hrv_status: Optional[str]
    hrv_last_night_avg: Optional[int]
    hrv_weekly_avg: Optional[int]
    hrv_baseline_low: Optional[int]
    hrv_baseline_high: Optional[int]
    hrv_peak: Optional[float]
    resting_hr: Optional[int]
    avg_hr: Optional[int]
    avg_stress: Optional[int]
    max_stress: Optional[int]
    body_battery_charged: Optional[int]
    body_battery_drained: Optional[int]
    steps: Optional[int]
    active_calories: Optional[int]
    avg_spo2: Optional[float]
    min_spo2: Optional[float]

    class Config:
        from_attributes = True


# Heart Rate
class HeartRatePoint(BaseModel):
    timestamp: datetime
    bpm: int

    class Config:
        from_attributes = True


class ActivityOut(BaseModel):
    id: int
    garmin_activity_id: int
    date: date
    activity_type: Optional[str]
    duration_sec: Optional[int]
    avg_hr: Optional[int]
    max_hr: Optional[int]
    calories: Optional[int]
    training_effect: Optional[str]
    distance_meters: Optional[float]
    hr_zones_json: Optional[Any]

    class Config:
        from_attributes = True


# AI Insights
class InsightOut(BaseModel):
    id: int
    generated_at: datetime
    insight_text: str
    trigger_type: str

    class Config:
        from_attributes = True


# Correlations
class CorrelationRow(BaseModel):
    habit_key: str
    habit_label: str
    metric: str
    avg_with: Optional[float]
    avg_without: Optional[float]
    delta: Optional[float]
    days_with: int
    days_without: int


# Settings
class UserSettingsUpdate(BaseModel):
    active_supplements: Optional[List[str]] = None
    morning_reminder_enabled: Optional[bool] = None
    morning_reminder_time: Optional[str] = None

# Garmin credentials
class GarminCredentials(BaseModel):
    email: str
    password: str

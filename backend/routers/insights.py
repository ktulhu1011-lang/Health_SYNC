from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/", response_model=List[schemas.InsightOut])
def get_insights(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    return db.query(models.AIInsight).filter(
        models.AIInsight.user_id == current_user.id
    ).order_by(models.AIInsight.generated_at.desc()).limit(limit).all()


@router.post("/generate", response_model=schemas.InsightOut)
def generate_insight(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    from services.ai_insights import generate_insight_for_user
    try:
        insight = generate_insight_for_user(current_user.id, db, trigger_type="on_demand")
        return insight
    except Exception as e:
        import traceback
        print(f"[insights] ERROR: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings", response_model=dict)
def get_settings(
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    return current_user.settings_json or {}


@router.put("/settings")
def update_settings(
    body: schemas.UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    settings = dict(current_user.settings_json or {})
    if body.active_supplements is not None:
        settings["active_supplements"] = body.active_supplements
    if body.morning_reminder_enabled is not None:
        settings["morning_reminder_enabled"] = body.morning_reminder_enabled
    if body.morning_reminder_time is not None:
        settings["morning_reminder_time"] = body.morning_reminder_time
    current_user.settings_json = settings
    db.commit()
    return {"status": "ok", "settings": settings}

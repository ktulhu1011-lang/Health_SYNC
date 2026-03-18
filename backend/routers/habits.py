from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, timedelta
from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.post("/log", response_model=schemas.HabitLogOut)
def log_habit(body: schemas.HabitLogCreate, db: Session = Depends(get_db),
              current_user: models.User = Depends(auth_utils.get_current_user)):
    log = models.HabitLog(
        user_id=current_user.id,
        date=body.date,
        category=body.category,
        habit_key=body.habit_key,
        value=body.value,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/today", response_model=List[schemas.HabitLogOut])
def today_habits(db: Session = Depends(get_db),
                 current_user: models.User = Depends(auth_utils.get_current_user)):
    today = date.today()
    logs = db.query(models.HabitLog).filter(
        and_(models.HabitLog.user_id == current_user.id, models.HabitLog.date == today)
    ).all()
    return logs


@router.get("/history", response_model=List[schemas.HabitLogOut])
def habit_history(
    days: int = Query(7, ge=1, le=365),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    since = date.today() - timedelta(days=days)
    q = db.query(models.HabitLog).filter(
        and_(models.HabitLog.user_id == current_user.id, models.HabitLog.date >= since)
    )
    if category:
        q = q.filter(models.HabitLog.category == category)
    return q.order_by(models.HabitLog.date.desc(), models.HabitLog.logged_at.desc()).all()


@router.get("/definitions", response_model=List[schemas.HabitDefinitionOut])
def get_definitions(db: Session = Depends(get_db),
                    current_user: models.User = Depends(auth_utils.get_current_user)):
    return db.query(models.HabitDefinition).filter(
        models.HabitDefinition.user_id == current_user.id
    ).order_by(models.HabitDefinition.sort_order).all()


@router.get("/heatmap")
def heatmap(
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    since = date.today() - timedelta(days=days)
    logs = db.query(models.HabitLog).filter(
        and_(models.HabitLog.user_id == current_user.id, models.HabitLog.date >= since)
    ).all()

    # Group by date
    by_date: dict = {}
    for log in logs:
        d = str(log.date)
        if d not in by_date:
            by_date[d] = []
        by_date[d].append({"category": log.category, "habit_key": log.habit_key, "value": log.value})

    return by_date

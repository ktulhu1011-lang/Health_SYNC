from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from datetime import date, timedelta
from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/api/heart", tags=["heart_rate"])


@router.get("/intraday", response_model=List[schemas.HeartRatePoint])
def get_intraday(
    target_date: date = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    points = db.query(models.HeartRateIntraday).filter(
        and_(models.HeartRateIntraday.user_id == current_user.id,
             models.HeartRateIntraday.date == target_date)
    ).order_by(models.HeartRateIntraday.timestamp).all()
    return points


@router.get("/activities", response_model=List[schemas.ActivityOut])
def get_activities(
    target_date: date = Query(default=None),
    days: int = Query(default=1, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    if target_date:
        activities = db.query(models.GarminActivity).filter(
            and_(models.GarminActivity.user_id == current_user.id,
                 models.GarminActivity.date == target_date)
        ).all()
    else:
        since = date.today() - timedelta(days=days)
        activities = db.query(models.GarminActivity).filter(
            and_(models.GarminActivity.user_id == current_user.id,
                 models.GarminActivity.date >= since)
        ).order_by(models.GarminActivity.date.desc()).all()
    return activities


@router.get("/trend")
def get_trend(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    since = date.today() - timedelta(days=days)
    rows = db.query(models.GarminDaily).filter(
        and_(models.GarminDaily.user_id == current_user.id,
             models.GarminDaily.date >= since)
    ).order_by(models.GarminDaily.date).all()

    return [
        {
            "date": str(r.date),
            "resting_hr": r.resting_hr,
            "avg_hr": r.avg_hr,
        }
        for r in rows
    ]

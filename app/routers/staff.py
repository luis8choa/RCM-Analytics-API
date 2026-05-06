from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Staff
from app.schemas import StaffErrorRate, StaffProductivity, StaffWorkload
from app.services import staff_service

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/productivity", response_model=list[StaffProductivity])
def staff_productivity(
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return staff_service.get_staff_productivity(
        db, from_date=from_date, to_date=to_date
    )


@router.get("/error-rate", response_model=list[StaffErrorRate])
def staff_error_rate(
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return staff_service.get_staff_error_rate(
        db, from_date=from_date, to_date=to_date
    )


@router.get("/workload", response_model=list[StaffWorkload])
def staff_workload(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return staff_service.get_staff_workload(db)
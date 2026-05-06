from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Staff
from app.schemas import AgingBucket, ARDaysResponse
from app.services import ar_service

router = APIRouter(prefix="/ar", tags=["ar"])


@router.get("/days", response_model=ARDaysResponse)
def ar_days(
    department: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return ar_service.get_ar_days(db, department=department)


@router.get("/aging-buckets", response_model=list[AgingBucket])
def aging_buckets(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return ar_service.get_aging_buckets(db)


@router.get("/by-department", response_model=list[ARDaysResponse])
def ar_by_department(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return ar_service.get_ar_by_department(db)
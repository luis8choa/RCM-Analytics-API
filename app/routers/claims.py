from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Staff
from app.schemas import ClaimCreate, ClaimResponse, DenialRateItem, TrendPoint
from app.services import claims_service

router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("", response_model=list[ClaimResponse])
def list_claims(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    payer: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return claims_service.get_claims(
        db, skip=skip, limit=limit, payer=payer, status=status
    )


@router.get("/denial-rate", response_model=list[DenialRateItem])
def denial_rate(
    payer: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return claims_service.get_denial_rate(
        db, payer=payer, from_date=from_date, to_date=to_date
    )


@router.get("/trends", response_model=list[TrendPoint])
def claims_trends(
    weeks: int = Query(default=8, ge=1, le=52),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return claims_service.get_claims_trends(db, weeks=weeks)


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    claim = claims_service.get_claim_by_id(db, claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )
    return claim


@router.post("", response_model=ClaimResponse, status_code=201)
def create_claim(
    claim_in: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return claims_service.create_claim(db, claim_in.model_dump())
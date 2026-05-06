from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Staff
from app.schemas import AlertConfigCreate, AlertConfigResponse, AlertTriggered
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertConfigResponse])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return alert_service.get_alerts(db)


@router.post("/configure", response_model=AlertConfigResponse, status_code=201)
def configure_alert(
    alert_in: AlertConfigCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return alert_service.create_alert(db, alert_in.model_dump())


@router.delete("/{alert_id}", status_code=204)
def deactivate_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    success = alert_service.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )


@router.post("/evaluate", response_model=list[AlertTriggered])
async def evaluate_alerts(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    return await alert_service.evaluate_alerts(db)
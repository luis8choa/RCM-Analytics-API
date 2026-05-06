from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models import AlertConfig
from app.services.ar_service import get_ar_days
from app.services.claims_service import get_denial_rate


def get_alerts(db: Session) -> list[AlertConfig]:
    return db.query(AlertConfig).filter(
        AlertConfig.is_active == True
    ).all()


def get_alert_by_id(db: Session, alert_id: int) -> AlertConfig | None:
    return db.query(AlertConfig).filter(
        AlertConfig.id == alert_id
    ).first()


def create_alert(db: Session, alert_data: dict) -> AlertConfig:
    alert = AlertConfig(**alert_data)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def delete_alert(db: Session, alert_id: int) -> bool:
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        return False
    alert.is_active = False
    db.commit()
    return True


def _evaluate_condition(
    current_value: float,
    threshold: float,
    operator: str,
) -> bool:
    if operator == "gt":
        return current_value > threshold
    if operator == "lt":
        return current_value < threshold
    if operator == "gte":
        return current_value >= threshold
    if operator == "lte":
        return current_value <= threshold
    return False


def _get_current_metric(db: Session, metric: str) -> float | None:
    if metric == "denial_rate":
        results = get_denial_rate(db)
        if not results:
            return None
        total = sum(r["total"] for r in results)
        denied = sum(r["denied"] for r in results)
        return round(denied / total * 100, 2) if total > 0 else 0.0

    if metric == "ar_days":
        result = get_ar_days(db)
        return result["average_ar_days"]

    return None


async def send_webhook(webhook_url: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            return response.status_code < 400
    except httpx.RequestError:
        return False


async def evaluate_alerts(db: Session) -> list[dict]:
    alerts = get_alerts(db)
    triggered = []

    for alert in alerts:
        current_value = _get_current_metric(db, alert.metric)
        if current_value is None:
            continue

        if _evaluate_condition(current_value, alert.threshold, alert.operator):
            payload = {
                "alert_id": alert.id,
                "metric": alert.metric,
                "current_value": current_value,
                "threshold": alert.threshold,
                "operator": alert.operator,
                "triggered_at": datetime.now(timezone.utc).isoformat(),
            }
            success = await send_webhook(alert.webhook_url, payload)
            triggered.append({
                **payload,
                "webhook_sent": success,
            })

    return triggered
from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import Claim, Staff, StaffActivity


def get_staff_productivity(
    db: Session,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[dict]:
    query = db.query(
        Staff.id.label("staff_id"),
        Staff.name.label("name"),
        Staff.role.label("role"),
        func.count(StaffActivity.id).label("claims_processed"),
        func.sum(Claim.expected_amount).label("total_amount"),
    ).join(
        StaffActivity, Staff.id == StaffActivity.staff_id
    ).join(
        Claim, StaffActivity.claim_id == Claim.id
    ).filter(
        Staff.is_active == True
    )

    if from_date:
        query = query.filter(StaffActivity.timestamp >= from_date)
    if to_date:
        query = query.filter(StaffActivity.timestamp <= to_date)

    results = query.group_by(
        Staff.id, Staff.name, Staff.role
    ).all()

    if not results:
        return []

    total_claims = sum(r.claims_processed for r in results)
    num_staff = len(results)
    team_average = round(total_claims / num_staff, 2) if num_staff > 0 else 0.0

    return [
        {
            "staff_id": row.staff_id,
            "name": row.name,
            "role": row.role,
            "claims_processed": row.claims_processed,
            "total_amount": round(row.total_amount or 0.0, 2),
            "daily_average": round(
                row.claims_processed / 30, 2
            ),
            "team_average": team_average,
            "performance": (
                "above_average" if row.claims_processed > team_average
                else "below_average" if row.claims_processed < team_average
                else "average"
            ),
        }
        for row in results
    ]


def get_staff_error_rate(
    db: Session,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[dict]:
    query = db.query(
        Staff.id.label("staff_id"),
        Staff.name.label("name"),
        func.count(StaffActivity.id).label("total_actions"),
        func.sum(
            case((StaffActivity.error_flag == True, 1), else_=0)
        ).label("errors"),
    ).join(
        StaffActivity, Staff.id == StaffActivity.staff_id
    ).filter(
        Staff.is_active == True
    )

    if from_date:
        query = query.filter(StaffActivity.timestamp >= from_date)
    if to_date:
        query = query.filter(StaffActivity.timestamp <= to_date)

    results = query.group_by(
        Staff.id, Staff.name
    ).order_by(
        func.sum(
            case((StaffActivity.error_flag == True, 1), else_=0)
        ).desc()
    ).all()

    return [
        {
            "staff_id": row.staff_id,
            "name": row.name,
            "total_actions": row.total_actions,
            "errors": row.errors or 0,
            "error_rate": round(
                (row.errors or 0) / row.total_actions * 100, 2
            ) if row.total_actions > 0 else 0.0,
        }
        for row in results
    ]


def get_staff_workload(db: Session) -> list[dict]:
    results = db.query(
        Staff.id.label("staff_id"),
        Staff.name.label("name"),
        func.count(StaffActivity.id).label("pending_claims"),
        func.max(Claim.payer).label("top_payer"),
    ).join(
        StaffActivity, Staff.id == StaffActivity.staff_id
    ).join(
        Claim, StaffActivity.claim_id == Claim.id
    ).filter(
        Staff.is_active == True,
        Claim.status.in_(["pending", "appealed"]),
    ).group_by(
        Staff.id, Staff.name
    ).order_by(
        func.count(StaffActivity.id).desc()
    ).all()

    return [
        {
            "staff_id": row.staff_id,
            "name": row.name,
            "pending_claims": row.pending_claims,
            "top_payer": row.top_payer,
        }
        for row in results
    ]
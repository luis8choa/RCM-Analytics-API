from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import Claim


def get_claims(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    payer: str | None = None,
    status: str | None = None,
) -> list[Claim]:
    query = db.query(Claim)
    if payer:
        query = query.filter(Claim.payer == payer)
    if status:
        query = query.filter(Claim.status == status)
    return query.offset(skip).limit(limit).all()


def get_claim_by_id(db: Session, claim_id: int) -> Claim | None:
    return db.query(Claim).filter(Claim.id == claim_id).first()


def create_claim(db: Session, claim_data: dict) -> Claim:
    claim = Claim(**claim_data)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def get_denial_rate(
    db: Session,
    payer: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[dict]:
    query = db.query(
        Claim.payer,
        func.count(Claim.id).label("total"),
        func.sum(
            case((Claim.status == "denied", 1), else_=0)
        ).label("denied"),
    )
    if payer:
        query = query.filter(Claim.payer == payer)
    if from_date:
        query = query.filter(Claim.submitted_at >= from_date)
    if to_date:
        query = query.filter(Claim.submitted_at <= to_date)

    results = query.group_by(Claim.payer).all()

    return [
        {
            "payer": row.payer,
            "total": row.total,
            "denied": row.denied or 0,
            "rate": round((row.denied or 0) / row.total * 100, 2),
        }
        for row in results
        if row.total > 0
    ]


def get_claims_trends(
    db: Session,
    weeks: int = 8,
) -> list[dict]:
    dialect = db.bind.dialect.name

    if dialect == "postgresql":
        week_expr = func.date_trunc("week", Claim.submitted_at)
    else:
        week_expr = func.strftime("%Y-%W", Claim.submitted_at)

    results = db.query(
        week_expr.label("week"),
        func.count(Claim.id).label("total_claims"),
        func.sum(
            case((Claim.status == "denied", 1), else_=0)
        ).label("denied"),
    ).group_by(
        week_expr
    ).order_by(
        week_expr.desc()
    ).limit(weeks).all()

    return [
        {
            "week": row.week,
            "total_claims": row.total_claims,
            "denial_rate": round(
                (row.denied or 0) / row.total_claims * 100, 2
            ),
        }
        for row in results
    ]
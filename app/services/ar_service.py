from datetime import datetime, timezone

from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from app.models import Claim

AR_BENCHMARK_DAYS = 40.0


def _days_diff_expr(end_col, start_col, db: Session):
    dialect = db.bind.dialect.name
    if dialect == "postgresql":
        return func.extract("epoch", end_col - start_col) / 86400
    else:
        return func.julianday(end_col) - func.julianday(start_col)


def _age_in_days_expr(db: Session):
    dialect = db.bind.dialect.name
    if dialect == "postgresql":
        return func.extract("epoch", func.now() - Claim.submitted_at) / 86400
    else:
        return func.julianday("now") - func.julianday(Claim.submitted_at)


def get_ar_days(db: Session, department: str | None = None) -> dict:
    diff_expr = _days_diff_expr(Claim.paid_at, Claim.submitted_at, db)

    query = db.query(
        func.avg(diff_expr).label("avg_days")
    ).filter(
        Claim.status == "paid",
        Claim.paid_at.isnot(None),
    )

    if department:
        query = query.filter(Claim.department == department)

    result = query.scalar()
    avg_days = round(result, 2) if result else 0.0

    return {
        "department": department,
        "average_ar_days": avg_days,
        "benchmark_days": AR_BENCHMARK_DAYS,
        "status": "ok" if avg_days <= AR_BENCHMARK_DAYS else "above_benchmark",
    }


def get_aging_buckets(db: Session) -> list[dict]:
    age_expr = _age_in_days_expr(db)

    bucket_expr = case(
        (age_expr <= 30, "0-30"),
        (age_expr <= 60, "31-60"),
        (age_expr <= 90, "61-90"),
        else_="90+",
    )

    results = db.query(
        bucket_expr.label("bucket"),
        func.count(Claim.id).label("count"),
        func.sum(Claim.expected_amount).label("total_amount"),
    ).filter(
        Claim.status.in_(["pending", "appealed"]),
        Claim.paid_at.is_(None),
    ).group_by(
        bucket_expr
    ).all()

    bucket_order = {"0-30": 0, "31-60": 1, "61-90": 2, "90+": 3}

    return sorted(
        [
            {
                "bucket": row.bucket,
                "count": row.count,
                "total_amount": round(row.total_amount or 0.0, 2),
            }
            for row in results
        ],
        key=lambda x: bucket_order.get(x["bucket"], 99),
    )


def get_ar_by_department(db: Session) -> list[dict]:
    diff_expr = _days_diff_expr(Claim.paid_at, Claim.submitted_at, db)

    results = db.query(
        Claim.department,
        func.avg(diff_expr).label("avg_days"),
        func.count(Claim.id).label("total_paid"),
    ).filter(
        Claim.status == "paid",
        Claim.paid_at.isnot(None),
        Claim.department.isnot(None),
    ).group_by(
        Claim.department
    ).all()

    return [
        {
            "department": row.department,
            "average_ar_days": round(row.avg_days, 2) if row.avg_days else 0.0,
            "total_paid_claims": row.total_paid,
            "benchmark_days": AR_BENCHMARK_DAYS,
            "status": (
                "ok" if (row.avg_days or 0) <= AR_BENCHMARK_DAYS
                else "above_benchmark"
            ),
        }
        for row in results
    ]
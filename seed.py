import random
from datetime import datetime, timedelta, timezone

from faker import Faker

from app.database import SessionLocal
from app.models import AlertConfig, Claim, Staff, StaffActivity

fake = Faker()

PAYERS = [
    "BlueCross_Test",
    "Aetna_Test",
    "UnitedHealth_Test",
    "Cigna_Test",
    "Humana_Test",
]

CPT_CODES = ["99213", "99214", "99215", "93000", "71046", "80053", "36415"]

ROLES = ["biller", "coder", "collector"]

DEPARTMENTS = ["cardiology", "radiology", "laboratory", "primary_care"]

CLAIM_STATUSES = ["paid", "denied", "pending", "appealed"]

DENIAL_REASONS = [
    "Duplicate claim",
    "Service not covered",
    "Prior authorization required",
    "Timely filing exceeded",
    "Invalid CPT code for diagnosis",
]

ACTIONS = ["submitted", "reviewed", "corrected", "appealed", "closed"]


def create_staff(db, n: int = 15) -> list[Staff]:
    staff_list = []
    for _ in range(n):
        member = Staff(
            name=fake.name(),
            email=fake.unique.email(),
            role=random.choice(ROLES),
            department=random.choice(DEPARTMENTS),
            is_active=random.choices([True, False], weights=[90, 10])[0],
        )
        db.add(member)
        staff_list.append(member)
    db.commit()
    for s in staff_list:
        db.refresh(s)
    return staff_list


def create_claims(db, n: int = 500) -> list[Claim]:
    claims_list = []
    for _ in range(n):
        status = random.choices(
            CLAIM_STATUSES, weights=[50, 25, 15, 10]
        )[0]
        submitted = fake.date_time_between(
            start_date="-12M", end_date="now", tzinfo=timezone.utc
        )
        paid_at = None
        paid_amount = None
        denial_reason = None

        if status == "paid":
            paid_at = submitted + timedelta(days=random.randint(5, 45))
            expected = round(random.uniform(100, 5000), 2)
            paid_amount = round(expected * random.uniform(0.85, 1.0), 2)
        elif status == "denied":
            denial_reason = random.choice(DENIAL_REASONS)
            expected = round(random.uniform(100, 5000), 2)
        else:
            expected = round(random.uniform(100, 5000), 2)

        claim = Claim(
            patient_id=f"PAT-{fake.numerify('######')}",
            cpt_code=random.choice(CPT_CODES),
            payer=random.choice(PAYERS),
            department=random.choice(DEPARTMENTS),   # línea nueva
            expected_amount=expected,
            paid_amount=paid_amount,
            status=status,
            submitted_at=submitted,
            paid_at=paid_at,
            denial_reason=denial_reason,
        )
        db.add(claim)
        claims_list.append(claim)
    db.commit()
    for c in claims_list:
        db.refresh(c)
    return claims_list


def create_activity(db, staff_list: list[Staff], claims_list: list[Claim]) -> None:
    for claim in claims_list:
        num_actions = random.randint(1, 3)
        assigned_staff = random.sample(staff_list, min(num_actions, len(staff_list)))
        for member in assigned_staff:
            activity = StaffActivity(
                staff_id=member.id,
                claim_id=claim.id,
                action=random.choice(ACTIONS),
                error_flag=random.choices([False, True], weights=[85, 15])[0],
            )
            db.add(activity)
    db.commit()


def create_alert_configs(db) -> None:
    alerts = [
        AlertConfig(
            metric="denial_rate",
            threshold=25.0,
            operator="gt",
            webhook_url="https://webhook.site/test-rcm",
            is_active=True,
        ),
        AlertConfig(
            metric="ar_days",
            threshold=45.0,
            operator="gt",
            webhook_url="https://webhook.site/test-rcm",
            is_active=True,
        ),
    ]
    for alert in alerts:
        db.add(alert)
    db.commit()


def main():
    db = SessionLocal()
    try:
        print("Seeding staff...")
        staff_list = create_staff(db, n=15)
        print(f"  {len(staff_list)} staff members created")

        print("Seeding claims...")
        claims_list = create_claims(db, n=500)
        print(f"  {len(claims_list)} claims created")

        print("Seeding staff activity...")
        create_activity(db, staff_list, claims_list)
        print("  Activity records created")

        print("Seeding alert configs...")
        create_alert_configs(db)
        print("  Alert configs created")

        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


# ── Auth ──────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


# ── Staff ─────────────────────────────────────────────
class StaffBase(BaseModel):
    name: str
    email: EmailStr
    role: str
    department: str


class StaffCreate(StaffBase):
    password: str


class StaffResponse(StaffBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


# ── Claims ────────────────────────────────────────────
class ClaimBase(BaseModel):
    patient_id: str
    cpt_code: str
    payer: str
    expected_amount: float
    status: str
    submitted_at: datetime


class ClaimCreate(ClaimBase):
    pass


class ClaimResponse(ClaimBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paid_amount: float | None
    paid_at: datetime | None
    denial_reason: str | None
    created_at: datetime


# ── Analytics ─────────────────────────────────────────
class DenialRateItem(BaseModel):
    payer: str
    total: int
    denied: int
    rate: float


class TrendPoint(BaseModel):
    week: datetime
    total_claims: int
    denial_rate: float


class ARDaysResponse(BaseModel):
    department: str | None
    average_ar_days: float
    benchmark_days: float = 40.0
    status: str


class AgingBucket(BaseModel):
    bucket: str
    count: int
    total_amount: float


# ── Staff Analytics ───────────────────────────────────
class StaffProductivity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_id: int
    name: str
    role: str
    claims_processed: int
    total_amount: float
    daily_average: float
    team_average: float
    performance: str


class StaffErrorRate(BaseModel):
    staff_id: int
    name: str
    total_actions: int
    errors: int
    error_rate: float


class StaffWorkload(BaseModel):
    staff_id: int
    name: str
    pending_claims: int
    top_payer: str | None

    # ── Alerts ────────────────────────────────────────────
class AlertConfigBase(BaseModel):
    metric: str
    threshold: float
    operator: str
    webhook_url: str


class AlertConfigCreate(AlertConfigBase):
    pass


class AlertConfigResponse(AlertConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class AlertTriggered(BaseModel):
    alert_id: int
    metric: str
    current_value: float
    threshold: float
    operator: str
    triggered_at: str
    webhook_sent: bool
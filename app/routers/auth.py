from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import authenticate_user, create_access_token, hash_password
from app.database import get_db
from app.models import Staff
from app.schemas import StaffCreate, StaffResponse, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=StaffResponse, status_code=201)
def register(
    staff_in: StaffCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(Staff).filter(Staff.email == staff_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    new_staff = Staff(
        name=staff_in.name,
        email=staff_in.email,
        role=staff_in.role,
        department=staff_in.department,
        hashed_password=hash_password(staff_in.password),
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff
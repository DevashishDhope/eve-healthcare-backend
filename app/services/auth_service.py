from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserSignup, UserLogin


class AuthService:
    @staticmethod
    def register_user(db: Session, signup_data: UserSignup) -> User:
        normalized_email = signup_data.email.strip().lower()
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )

        new_user = User(
            email=normalized_email,
            password_hash=hash_password(signup_data.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> tuple[User, str]:
        normalized_email = login_data.email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        token = create_access_token(subject=str(user.id), extra_claims={"email": user.email})
        return user, token

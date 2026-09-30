import os
import sys
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.core.security import hash_password, create_access_token
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.models.centre_test import CentreTest

# Ensure test DB is distinct from production DB
assert "test" in settings.TEST_DATABASE_URL.lower(), "Safety check failed: TEST_DATABASE_URL must contain 'test'"

test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables on eve_healthcare_test before tests run and drop after session."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Yield a database session and clean up tables after each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # Clean up tables between test runs
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Creates and returns a test user."""
    user = User(
        email="patient1@example.com",
        password_hash=hash_password("password123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Returns valid Authorization Bearer headers for test_user."""
    token = create_access_token(subject=str(test_user.id), extra_claims={"email": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_2(db_session: Session) -> User:
    """Creates and returns a second test user for authorization tests."""
    user = User(
        email="patient2@example.com",
        password_hash=hash_password("password123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_user_2(test_user_2: User) -> dict:
    """Returns valid Authorization Bearer headers for test_user_2."""
    token = create_access_token(subject=str(test_user_2.id), extra_claims={"email": test_user_2.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_offering(db_session: Session) -> CentreTest:
    """Creates a centre, a test, and links them with a price of 500.00."""
    centre = DiagnosticCentre(
        name="Metro Diagnostics",
        location="Indiranagar, Bangalore"
    )
    test = DiagnosticTest(
        name="Complete Blood Count",
        description="Comprehensive hemogram analysis"
    )
    db_session.add_all([centre, test])
    db_session.commit()
    db_session.refresh(centre)
    db_session.refresh(test)

    offering = CentreTest(
        centre_id=centre.id,
        test_id=test.id,
        price=500.00
    )
    db_session.add(offering)
    db_session.commit()
    db_session.refresh(offering)
    return offering

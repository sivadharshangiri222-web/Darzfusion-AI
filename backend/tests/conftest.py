"""Pytest fixtures for DARZFUSION AI test suite."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment variables before importing app
os.environ["ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database.connection import Base, get_db
from app.main import app
from app.models.user import User
from app.core.security import hash_password, create_access_token

# Setup in-memory SQLite for testing
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables before running tests and teardown after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provides a transactional database session rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Provides a FastAPI TestClient overriding the get_db dependency."""
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
def test_user(db_session):
    """Creates a primary test user."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=hash_password("Password123!"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Returns Bearer authorization headers for the primary test user."""
    token = create_access_token(data={"sub": test_user.id, "username": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user(db_session):
    """Creates a second distinct user to verify ownership isolation."""
    user = User(
        email="other@example.com",
        username="otheruser",
        hashed_password=hash_password("OtherPassword123!"),
        full_name="Other User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_auth_headers(other_user):
    """Returns Bearer authorization headers for the second user."""
    token = create_access_token(data={"sub": other_user.id, "username": other_user.username})
    return {"Authorization": f"Bearer {token}"}

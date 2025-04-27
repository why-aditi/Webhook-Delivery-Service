import pytest
import asyncio
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:aditiKasequel_2024@localhost:5432/webhook_service_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture(autouse=True)
async def setup_test_environment():
    """Set up the test environment."""
    # Set test environment variables
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["ENVIRONMENT"] = "test"
    
    yield
    
    # Clean up
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    if "ENVIRONMENT" in os.environ:
        del os.environ["ENVIRONMENT"] 
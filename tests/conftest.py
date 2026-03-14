import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.core.database import Base, get_db
from src.core.security import hash_password
from src.domain.enums import ProjectRole
from src.main import app
from src.models.project import ProjectModel
from src.models.project_member import ProjectMemberModel
from src.models.task import TaskModel
from src.models.user import UserModel

# Test database — NullPool creates a fresh connection each time, no reuse conflicts
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}_test"
    f"?ssl=disable"
)

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
async_session_test = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

_tables_created = False


@pytest_asyncio.fixture
async def db_session():
    """Provides a DB session for fixture setup (creating users, projects, etc.)."""
    global _tables_created
    if not _tables_created:
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _tables_created = True

    async with async_session_test() as session:
        yield session

    # Truncate after each test
    async with engine_test.begin() as conn:
        await conn.execute(
            text("TRUNCATE TABLE tasks, project_members, projects, users CASCADE")
        )


@pytest_asyncio.fixture
async def client():
    """HTTP test client — endpoints get their own session from the test DB."""

    async def override_get_db():
        async with async_session_test() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    password = "testpass123"
    user = UserModel(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password(password),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user, password


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession):
    password = "secondpass123"
    user = UserModel(
        email="second@example.com",
        full_name="Second User",
        hashed_password=hash_password(password),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user, password


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_user):
    user, _ = test_user
    project = ProjectModel(
        name="Test Project",
        description="A test project",
        owner_id=user.id,
    )
    db_session.add(project)
    await db_session.flush()

    member = ProjectMemberModel(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.OWNER.value,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user):
    user, password = test_user
    response = await client.post(
        "/api/auth/login",
        json={"email": user.email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient, second_user):
    user, password = second_user
    response = await client.post(
        "/api/auth/login",
        json={"email": user.email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
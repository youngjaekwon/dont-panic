import pytest
from alembic import command
from alembic.config import Config

from app.di import create_container


@pytest.fixture(scope="session", autouse=True)
def migrate():
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
async def container():
    c = create_container()
    yield c
    await c.close()

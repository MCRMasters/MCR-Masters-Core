import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    load_dotenv(".env.test", override=True)
    yield

    load_dotenv(".env", override=True)

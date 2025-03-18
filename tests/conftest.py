import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    테스트 환경 설정을 위한 글로벌 fixture
    모든 테스트 세션에 자동으로 적용되며 테스트 환경 변수를 로드합니다.
    """
    # 테스트용 환경 변수 파일 로드 (프로젝트 설정에 맞게 조정)
    load_dotenv(".env.test", override=True)
    yield
    # 테스트 종료 후 기본 환경 변수로 복원 (필요한 경우)
    load_dotenv(".env", override=True)

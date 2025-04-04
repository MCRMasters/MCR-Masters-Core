import asyncio
import logging
import sys

import alembic.config
import uvicorn
from pytest import main as pytest_main

from app.db.session import init_db

# 로깅 설정: DEBUG 레벨 이상의 로그를 콘솔에 출력
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def start_dev_server() -> None:
    logger.info("Starting development server with reload")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


def start_prod_server() -> None:
    """프로덕션 서버를 시작합니다."""
    logger.info("Starting production server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


def run_migrations() -> None:
    logger.info("Running migrations: upgrade head")
    alembic_args = ["upgrade", "head"]
    alembic.config.main(argv=alembic_args)
    logger.info("Migrations completed")


def rollback_migration() -> None:
    logger.info("Rolling back migration: downgrade -1")
    alembic_args = ["downgrade", "-1"]
    alembic.config.main(argv=alembic_args)
    logger.info("Migration rollback completed")


def create_migration() -> None:
    if len(sys.argv) < 2:
        logger.error("Migration message is required")
        print("Error: Migration message is required")
        print('Usage: poetry run migrate-create "your migration message"')
        sys.exit(1)

    message = sys.argv[1]
    logger.info(f"Creating migration with message: {message}")
    alembic_args = ["revision", "--autogenerate", "-m", message]
    alembic.config.main(argv=alembic_args)
    logger.info("Migration created")


def initialize_db() -> None:
    logger.info("Initializing database")
    asyncio.run(init_db())
    logger.info("Database initialization completed")


def run_coverage() -> None:
    logger.info("Running test coverage")
    sys.exit(
        pytest_main(["--cov=app", "--cov-report=term-missing", "--no-cov-on-fail"]),
    )

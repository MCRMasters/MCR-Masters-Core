import asyncio
import sys

import alembic.config
import uvicorn

from app.db.session import init_db


def start_dev_server() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


def start_prod_server() -> None:
    """프로덕션 서버를 시작합니다."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


def run_migrations() -> None:
    alembic_args = ["upgrade", "head"]
    alembic.config.main(argv=alembic_args)


def rollback_migration() -> None:
    alembic_args = ["downgrade", "-1"]
    alembic.config.main(argv=alembic_args)


def create_migration() -> None:
    if len(sys.argv) < 2:
        print("Error: Migration message is required")
        print('Usage: poetry run migrate-create "your migration message"')
        sys.exit(1)

    message = sys.argv[1]
    alembic_args = ["revision", "--autogenerate", "-m", message]
    alembic.config.main(argv=alembic_args)


def initialize_db() -> None:
    asyncio.run(init_db())

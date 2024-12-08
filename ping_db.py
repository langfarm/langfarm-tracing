import logging

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from langfarm_tracing.core.config import settings
from langfarm_tracing.core.db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def ping(db_engine: Engine) -> None:
    try:
        # Try to create session to check if DB is awake
        with Session(db_engine) as session:
            session.execute(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    logger.info("try connect db=[%s:%s] service", settings.POSTGRES_SERVER, settings.POSTGRES_PORT)
    ping(engine)
    logger.info("Service Connect Succeed!")


if __name__ == "__main__":
    main()

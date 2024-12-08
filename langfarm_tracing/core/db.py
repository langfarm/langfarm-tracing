import logging
from collections.abc import Generator
from typing import TypeVar, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .config import settings

logger = logging.getLogger(__name__)

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=settings.ECHO_SQL)


def get_db_session() -> Generator[Session, None, None]:
    session = Session(engine)
    logger.debug("db session=[%s] created", session.hash_key)
    try:
        yield session
    finally:
        session.close()
        logger.debug("db session=[%s] closed", session.hash_key)


def with_db_session(func):

    def execute(stmt, t: _T) -> _T:
        for session in get_db_session():
            return func(stmt, t, session=session)

    return execute


_T = TypeVar("_T", bound=object)


@with_db_session
def read_first(stmt, t: _T, *, session: Session = None) -> Optional[_T]:
    obj = None
    row = session.execute(stmt).first()
    if row:
        obj = row[0]
    return obj


@with_db_session
def read_list(stmt, t: _T, *, session: Session = None) -> Generator[_T, None, None]:
    rows = session.execute(stmt).all()
    for row in rows:
        yield row[0]

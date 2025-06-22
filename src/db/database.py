from contextlib import contextmanager
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from typing import Final, Generator

import db.models

db_path: Final[Path] = Path("database/bot.db").resolve()
DATABASE_URL: Final[str] = f"sqlite:///{db_path.as_posix()}"

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

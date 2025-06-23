from contextlib import asynccontextmanager
from pathlib import Path
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Final, AsyncGenerator

import db.models

db_path: Final[Path] = Path("database/bot.db").resolve()
DATABASE_URL: Final[str] = f"sqlite+aiosqlite:///{db_path.as_posix()}"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field
from sqlalchemy import Index
from uuid import UUID, uuid4


def now() -> datetime:
    return datetime.now(timezone.utc)


class CommandCategory(str, Enum):
    FUN = "fun"
    RULE34 = "rule34"
    MISC = "misc"


class User(SQLModel, table=True):
    id: str = Field(primary_key=True)


class Guild(SQLModel, table=True):
    id: str = Field(primary_key=True)
    r34_enabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=now)


class GuildUserProfile(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    guild_id: str = Field(foreign_key="guild.id")
    user_id: str = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=now)

    __table_args__ = (
        Index(
            "guild_user_profile_guild_id_user_id_key",
            "guild_id",
            "user_id",
            unique=True,
        ),
    )


class UserCommandCount(SQLModel, table=True):
    user_id: UUID = Field(primary_key=True, foreign_key="guilduserprofile.id")
    category: CommandCategory = Field(primary_key=True)
    count: int = Field(default=0)


class R34UserProfile(SQLModel, table=True):
    user_id: UUID = Field(primary_key=True, foreign_key="guilduserprofile.id")
    blacklist_enabled: bool = Field(default=True)


class R34UserBlacklist(SQLModel, table=True):
    user_id: UUID = Field(primary_key=True, foreign_key="guilduserprofile.id")
    tag: str = Field(primary_key=True)


class R34UserBookmarks(SQLModel, table=True):
    user_id: UUID = Field(primary_key=True, foreign_key="guilduserprofile.id")
    post_id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=now)

import asyncio
from cachetools import TTLCache
from sqlmodel import select
from typing import Final, Optional

from db.models import (
    User,
    Guild,
    GuildUserProfile,
    UserCommandCount,
    CommandCategory,
    now,
)
from db.engine import get_session


class DatabaseUtils:
    maxsize: Final[int] = 2048
    ttl: Final[int] = 3600

    _guild_cache: Final[TTLCache[str, Guild]] = TTLCache(maxsize, ttl)
    _guild_cache_lock = asyncio.Lock()

    _guild_user_profile_cache: Final[TTLCache[str, GuildUserProfile]] = TTLCache(
        maxsize, ttl
    )
    _guild_user_profile_cache_lock = asyncio.Lock()

    @staticmethod
    async def fetch_or_create_user(user_id: str) -> User:
        async with get_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            if user := result.scalar_one_or_none():
                return user

            user = User(id=user_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def fetch_guild(guild_id: str) -> Optional[Guild]:
        async with DatabaseUtils._guild_cache_lock:
            if guild := DatabaseUtils._guild_cache.get(guild_id):
                return guild

        async with get_session() as session:
            result = await session.execute(select(Guild).where(Guild.id == guild_id))
            guild = result.scalar_one_or_none()

            if guild:
                async with DatabaseUtils._guild_cache_lock:
                    DatabaseUtils._guild_cache[guild_id] = guild

            return guild

    @staticmethod
    async def create_guild(guild_id: str) -> Guild:
        guild = Guild(id=guild_id)

        async with get_session() as session:
            session.add(guild)
            await session.commit()
            await session.refresh(guild)

        async with DatabaseUtils._guild_cache_lock:
            DatabaseUtils._guild_cache[guild_id] = guild
        return guild

    @staticmethod
    async def fetch_or_create_guild(guild_id: str) -> Guild:
        return await DatabaseUtils.fetch_guild(
            guild_id
        ) or await DatabaseUtils.create_guild(guild_id)

    @staticmethod
    async def update_guild(guild_id: str, **kwargs) -> Guild:
        async with get_session() as session:
            result = await session.execute(select(Guild).where(Guild.id == guild_id))
            guild = result.scalar_one()

            for key, value in kwargs.items():
                setattr(guild, key, value)

            session.add(guild)
            await session.commit()
            await session.refresh(guild)

        async with DatabaseUtils._guild_cache_lock:
            if cached := DatabaseUtils._guild_cache.get(guild_id):
                for key, value in kwargs.items():
                    setattr(cached, key, value)
            DatabaseUtils._guild_cache[guild_id] = guild
        return guild

    @staticmethod
    async def fetch_guild_user_profile(
        guild_id: str, user_id: str
    ) -> Optional[GuildUserProfile]:
        cache_key = f"{guild_id}:{user_id}"
        async with DatabaseUtils._guild_user_profile_cache_lock:
            if profile := DatabaseUtils._guild_user_profile_cache.get(cache_key):
                return profile

        async with get_session() as session:
            result = await session.execute(
                select(GuildUserProfile).where(
                    (GuildUserProfile.guild_id == guild_id)
                    & (GuildUserProfile.user_id == user_id)
                )
            )
            profile = result.scalar_one_or_none()
            if profile:
                async with DatabaseUtils._guild_user_profile_cache_lock:
                    DatabaseUtils._guild_user_profile_cache[cache_key] = profile
            return profile

    @staticmethod
    async def create_guild_user_profile(
        guild_id: str, user_id: str
    ) -> GuildUserProfile:
        await DatabaseUtils.fetch_or_create_guild(guild_id)
        await DatabaseUtils.fetch_or_create_user(user_id)

        profile = GuildUserProfile(guild_id=guild_id, user_id=user_id, created_at=now())

        async with get_session() as session:
            session.add(profile)
            await session.commit()
            await session.refresh(profile)

        cache_key = f"{guild_id}:{user_id}"
        async with DatabaseUtils._guild_user_profile_cache_lock:
            DatabaseUtils._guild_user_profile_cache[cache_key] = profile

        return profile

    @staticmethod
    async def fetch_or_create_guild_user_profile(
        guild_id: str, user_id: str
    ) -> GuildUserProfile:
        return await DatabaseUtils.fetch_guild_user_profile(
            guild_id, user_id
        ) or await DatabaseUtils.create_guild_user_profile(guild_id, user_id)

    @staticmethod
    async def fetch_command_count(
        guild_id: str, user_id: str, category: CommandCategory
    ) -> int:
        profile = await DatabaseUtils.fetch_or_create_guild_user_profile(
            guild_id, user_id
        )

        async with get_session() as session:
            result = await session.execute(
                select(UserCommandCount.count).where(
                    (UserCommandCount.user_id == profile.id)
                    & (UserCommandCount.category == category)
                )
            )
            return result.scalar_one_or_none() or 0

    @staticmethod
    async def increment_command_count(
        guild_id: str, user_id: str, category: CommandCategory, amount: int = 1
    ) -> int:
        profile = await DatabaseUtils.fetch_or_create_guild_user_profile(
            guild_id, user_id
        )

        async with get_session() as session:
            result = await session.execute(
                select(UserCommandCount).where(
                    (UserCommandCount.user_id == profile.id)
                    & (UserCommandCount.category == category)
                )
            )
            command_count = result.scalar_one_or_none()

            if command_count:
                command_count.count += amount
                session.add(command_count)
                await session.commit()
                await session.refresh(command_count)
                return command_count.count

            new_count = amount
            count_obj = UserCommandCount(
                user_id=profile.id, category=category, count=new_count
            )
            session.add(count_obj)
            await session.commit()
            return new_count

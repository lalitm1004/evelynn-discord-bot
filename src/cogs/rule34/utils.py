import asyncio
from cachetools import TTLCache
from sqlmodel import select
from typing import Final, List, Optional, Set
from uuid import UUID

from db.engine import get_session
from db.models import (
    R34UserProfile,
    R34UserBlacklist,
    R34UserBookmarks,
)
from db.utils import DatabaseUtils


class Rule34DatabaseUtils(DatabaseUtils):
    _r34_profile_cache: Final[TTLCache[UUID, R34UserProfile]] = TTLCache(
        DatabaseUtils.maxsize, DatabaseUtils.ttl
    )
    _r34_profile_cache_lock = asyncio.Lock()

    _blacklist_cache: Final[TTLCache[UUID, Set[str]]] = TTLCache(
        DatabaseUtils.maxsize, DatabaseUtils.ttl
    )
    _blacklist_cache_lock = asyncio.Lock()

    _bookmark_cache: Final[TTLCache[UUID, Set[str]]] = TTLCache(
        DatabaseUtils.maxsize, DatabaseUtils.ttl
    )
    _bookmark_cache_lock = asyncio.Lock()

    @staticmethod
    async def _get_profile_id(guild_id: str, user_id: str) -> UUID:
        profile = await DatabaseUtils.fetch_or_create_guild_user_profile(
            guild_id, user_id
        )
        return profile.id

    @staticmethod
    async def fetch_r34_user_profile(
        guild_id: str, user_id: str
    ) -> Optional[R34UserProfile]:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)

        async with Rule34DatabaseUtils._r34_profile_cache_lock:
            if profile := Rule34DatabaseUtils._r34_profile_cache.get(profile_id):
                return profile

        async with get_session() as session:
            result = await session.execute(
                select(R34UserProfile).where(R34UserProfile.user_id == profile_id)
            )
            profile = result.scalar_one_or_none()

            if profile:
                async with Rule34DatabaseUtils._r34_profile_cache_lock:
                    Rule34DatabaseUtils._r34_profile_cache[profile_id] = profile

            return profile

    @staticmethod
    async def create_r34_user_profile(guild_id: str, user_id: str) -> R34UserProfile:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)
        profile = R34UserProfile(user_id=profile_id)

        async with get_session() as session:
            session.add(profile)
            await session.commit()
            await session.refresh(profile)

        async with Rule34DatabaseUtils._r34_profile_cache_lock:
            Rule34DatabaseUtils._r34_profile_cache[profile_id] = profile

        return profile

    @staticmethod
    async def fetch_or_create_r34_user_profile(
        guild_id: str, user_id: str
    ) -> R34UserProfile:
        return await Rule34DatabaseUtils.fetch_r34_user_profile(
            guild_id, user_id
        ) or await Rule34DatabaseUtils.create_r34_user_profile(guild_id, user_id)

    @staticmethod
    async def update_r34_user_profile(
        guild_id: str, user_id: str, **kwargs
    ) -> R34UserProfile:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)

        async with get_session() as session:
            result = await session.execute(
                select(R34UserProfile).where(R34UserProfile.user_id == profile_id)
            )
            profile = result.scalar_one()

            for key, value in kwargs.items():
                setattr(profile, key, value)

            session.add(profile)
            await session.commit()
            await session.refresh(profile)

        async with Rule34DatabaseUtils._r34_profile_cache_lock:
            Rule34DatabaseUtils._r34_profile_cache[profile_id] = profile

        return profile

    @staticmethod
    async def get_blacklist(guild_id: str, user_id: str) -> Set[str]:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)

        async with Rule34DatabaseUtils._bookmark_cache_lock:
            if cached := Rule34DatabaseUtils._blacklist_cache.get(profile_id):
                return cached

        async with get_session() as session:
            result = await session.execute(
                select(R34UserBlacklist.tag).where(
                    R34UserBlacklist.user_id == profile_id
                )
            )
            tags = result.scalars().all()
            tags = set(tags)

        async with Rule34DatabaseUtils._bookmark_cache_lock:
            Rule34DatabaseUtils._blacklist_cache[profile_id] = tags

        return tags

    @staticmethod
    async def add_blacklist_tags(
        guild_id: str, user_id: str, tags: List[str]
    ) -> Set[str]:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)

        existing_tags = await Rule34DatabaseUtils.get_blacklist(guild_id, user_id)
        to_insert = set(tags) - existing_tags
        rejected = set(tags) - to_insert

        async with get_session() as session:
            session.add_all(
                [R34UserBlacklist(user_id=profile_id, tag=tag) for tag in to_insert]
            )
            await session.commit()

        async with Rule34DatabaseUtils._bookmark_cache_lock:
            if profile_id in Rule34DatabaseUtils._blacklist_cache:
                Rule34DatabaseUtils._blacklist_cache[profile_id].update(to_insert)
            else:
                Rule34DatabaseUtils._blacklist_cache[profile_id] = (
                    existing_tags | to_insert
                )

        return rejected

    @staticmethod
    async def remove_blacklist_tags(
        guild_id: str, user_id: str, tags: List[str]
    ) -> Set[str]:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)

        found_tags = set()

        async with get_session() as session:
            for tag in tags:
                result = await session.execute(
                    select(R34UserBlacklist).where(
                        (R34UserBlacklist.user_id == profile_id)
                        & (R34UserBlacklist.tag == tag)
                    )
                )
                record = result.scalar_one_or_none()
                if record:
                    await session.delete(record)
                    found_tags.add(tag)

            await session.commit()

        async with Rule34DatabaseUtils._bookmark_cache_lock:
            if profile_id in Rule34DatabaseUtils._blacklist_cache:
                Rule34DatabaseUtils._blacklist_cache[profile_id] -= found_tags

        rejected = set(tags) - found_tags
        return rejected

    @staticmethod
    async def get_bookmarks(guild_id: str, user_id: str) -> Set[str]:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)

        async with Rule34DatabaseUtils._bookmark_cache_lock:
            if cached := Rule34DatabaseUtils._bookmark_cache.get(profile_id):
                return cached

        async with get_session() as session:
            result = await session.execute(
                select(R34UserBookmarks.post_id).where(
                    R34UserBookmarks.user_id == profile_id
                )
            )
            post_ids = set(result.scalars().all())

        async with Rule34DatabaseUtils._bookmark_cache_lock:
            Rule34DatabaseUtils._bookmark_cache[profile_id] = post_ids

        return post_ids

    @staticmethod
    async def add_bookmarks(
        guild_id: str, user_id: str, post_ids: List[str]
    ) -> Set[str]:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)

        existing_post_ids = await Rule34DatabaseUtils.get_bookmarks(guild_id, user_id)
        to_insert = set(post_ids) - existing_post_ids
        rejected = set(post_ids) - to_insert

        async with get_session() as session:
            session.add_all(
                [R34UserBookmarks(user_id=profile_id, post_id=pid) for pid in to_insert]
            )
            await session.commit()

        async with Rule34DatabaseUtils._bookmark_cache_lock:
            if profile_id in Rule34DatabaseUtils._bookmark_cache:
                Rule34DatabaseUtils._bookmark_cache[profile_id].update(to_insert)
            else:
                Rule34DatabaseUtils._bookmark_cache[profile_id] = (
                    existing_post_ids | to_insert
                )

        return rejected

    @staticmethod
    async def remove_bookmarks(
        guild_id: str, user_id: str, post_ids: List[str]
    ) -> Set[str]:
        profile_id = await Rule34DatabaseUtils._get_profile_id(guild_id, user_id)

        found_post_ids = set()

        async with get_session() as session:
            for pid in post_ids:
                result = await session.execute(
                    select(R34UserBookmarks).where(
                        (R34UserBookmarks.user_id == profile_id)
                        & (R34UserBookmarks.post_id == pid)
                    )
                )
                record = result.scalar_one_or_none()
                if record:
                    await session.delete(record)
                    found_post_ids.add(pid)

            await session.commit()

        async with Rule34DatabaseUtils._bookmark_cache_lock:
            if profile_id in Rule34DatabaseUtils._bookmark_cache:
                Rule34DatabaseUtils._bookmark_cache[profile_id] -= found_post_ids

        rejected = set(post_ids) - found_post_ids
        return rejected

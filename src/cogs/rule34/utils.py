from dataclasses import dataclass
from sqlmodel import select
from typing import List, Tuple

from db.models import (
    CommandCategory,
    GuildUserProfile,
    R34UserProfile,
    R34UserBlacklist,
    R34UserBookmarks,
    UserCommandCount,
)
from db.database import get_session


class Rule34DatabaseUtils:
    @staticmethod
    def fetch_r34_profile(user_id: str, guild_id: str) -> R34UserProfile:
        with get_session() as session:
            guild_profile = session.exec(
                select(GuildUserProfile).where(
                    GuildUserProfile.user_id == user_id,
                    GuildUserProfile.guild_id == guild_id,
                )
            ).first()

            assert guild_profile is not None, (
                "`before_invoke` hook should create `GuildUserProfile`"
            )

            profile = session.exec(
                select(R34UserProfile).where(R34UserProfile.user_id == guild_profile.id)
            ).first()

            if profile:
                return profile

            new_profile = R34UserProfile(user_id=guild_profile.id)
            session.add(new_profile)
            session.commit()
            session.refresh(new_profile)
            return new_profile

    @staticmethod
    def toggle_user_blacklist(user_id: str, guild_id: str) -> bool:
        with get_session() as session:
            profile = Rule34DatabaseUtils.fetch_r34_profile(user_id, guild_id)
            profile.blacklist_enabled = not profile.blacklist_enabled
            new_state = profile.blacklist_enabled
            session.add(profile)
            session.commit()
        return new_state

    @staticmethod
    def is_blacklist_enabled(user_id: str, guild_id: str) -> bool:
        profile = Rule34DatabaseUtils.fetch_r34_profile(user_id, guild_id)
        return profile.blacklist_enabled

    @staticmethod
    def push_to_blacklist(user_id: str, guild_id: str, tag: str) -> bool:
        with get_session() as session:
            profile = Rule34DatabaseUtils.fetch_r34_profile(user_id, guild_id)
            existing = session.exec(
                select(R34UserBlacklist).where(
                    R34UserBlacklist.user_id == profile.user_id,
                    R34UserBlacklist.tag == tag,
                )
            ).first()

            if existing:
                return False

            entry = R34UserBlacklist(user_id=profile.user_id, tag=tag)
            session.add(entry)
            session.commit()

        return True

    @staticmethod
    def pop_from_blacklist(user_id: str, guild_id: str, tag: str) -> bool:
        with get_session() as session:
            profile = Rule34DatabaseUtils.fetch_r34_profile(user_id, guild_id)

            existing = session.exec(
                select(R34UserBlacklist).where(
                    R34UserBlacklist.user_id == profile.user_id,
                    R34UserBlacklist.tag == tag,
                )
            ).first()

            if existing:
                session.delete(existing)
                session.commit()
                return True

        return False

    @staticmethod
    def fetch_blacklist(user_id: str, guild_id: str) -> List[str]:
        with get_session() as session:
            profile = Rule34DatabaseUtils.fetch_r34_profile(user_id, guild_id)

            entries = session.exec(
                select(R34UserBlacklist.tag).where(
                    R34UserBlacklist.user_id == profile.user_id
                )
            ).all()

            return [e for e in entries]

    @staticmethod
    def increment_command_count(user_id: str, guild_id: str) -> None:
        with get_session() as session:
            profile = session.exec(
                select(GuildUserProfile).where(
                    GuildUserProfile.user_id == user_id,
                    GuildUserProfile.guild_id == guild_id,
                )
            ).first()

            assert profile is not None, (
                "`before_invoke` hook should create `GuildUserProfile`"
            )

            existing = session.exec(
                select(UserCommandCount).where(
                    UserCommandCount.user_id == profile.id,
                    UserCommandCount.category == CommandCategory.RULE34,
                )
            ).first()

            if existing:
                existing.count += 1
                session.add(existing)
            else:
                new_count = UserCommandCount(
                    user_id=profile.id,
                    category=CommandCategory.RULE34,
                    count=1,
                )
                session.add(new_count)

            session.commit()

    @staticmethod
    def push_bookmark(user_id: str, guild_id: str, post_id: str) -> bool:
        with get_session() as session:
            profile = Rule34DatabaseUtils.fetch_r34_profile(user_id, guild_id)

            existing = session.exec(
                select(R34UserBookmarks).where(
                    R34UserBookmarks.user_id == profile.user_id,
                    R34UserBookmarks.post_id == post_id,
                )
            ).first()

            if existing:
                return False

            bookmark = R34UserBookmarks(user_id=profile.user_id, post_id=post_id)
            session.add(bookmark)
            session.commit()

        return True

    @staticmethod
    def pop_bookmark(user_id: str, guild_id: str, post_id: str) -> bool:
        with get_session() as session:
            profile = Rule34DatabaseUtils.fetch_r34_profile(user_id, guild_id)

            existing = session.exec(
                select(R34UserBookmarks).where(
                    R34UserBookmarks.user_id == profile.user_id,
                    R34UserBookmarks.post_id == post_id,
                )
            ).first()

            if existing:
                session.delete(existing)
                session.commit()
                return True

        return False

    @staticmethod
    def fetch_bookmarks(user_id: str, guild_id: str) -> List[str]:
        with get_session() as session:
            profile = Rule34DatabaseUtils.fetch_r34_profile(user_id, guild_id)

            entries = session.exec(
                select(R34UserBookmarks.post_id).where(
                    R34UserBookmarks.user_id == profile.user_id
                )
            ).all()

            return [e for e in entries]

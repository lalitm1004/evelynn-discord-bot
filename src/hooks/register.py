from discord.ext import commands
from sqlmodel import select
from uuid import uuid4

from db.models import User, Guild, GuildUserProfile
from db.database import get_session


def register_hook():
    async def before_command(ctx: commands.Context) -> None:
        author_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id) if ctx.guild else None

        with get_session() as session:
            user = session.get(User, author_id)

            if user is None:
                user = User(id=author_id)
                session.add(user)

            if guild_id is not None:
                db_guild = session.get(Guild, guild_id)

                if db_guild is None:
                    session.add(Guild(id=guild_id))

                result = session.exec(
                    select(GuildUserProfile).where(
                        GuildUserProfile.user_id == author_id,
                        GuildUserProfile.guild_id == guild_id,
                    )
                )
                profile = result.first()

                if profile is None:
                    profile = GuildUserProfile(
                        id=uuid4(),
                        user_id=author_id,
                        guild_id=guild_id,
                    )
                    session.add(profile)

                session.commit()

    return before_command

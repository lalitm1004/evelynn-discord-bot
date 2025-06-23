from discord.ext import commands
from db.utils import DatabaseUtils as DBUtils


async def register_hook_command(ctx: commands.Context) -> None:
    author_id = str(ctx.author.id)
    guild_id = str(ctx.guild.id) if ctx.guild else None

    await DBUtils.fetch_or_create_user(author_id)

    if guild_id is not None:
        await DBUtils.fetch_or_create_guild(guild_id)
        await DBUtils.fetch_or_create_guild_user_profile(guild_id, author_id)


def register_hook():
    """
    Simple hook that creates all relevant profiles when a user invokes a command
    """

    return register_hook_command

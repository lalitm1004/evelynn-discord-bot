from discord import Guild
from discord.ext import commands

from typing import Optional, Tuple


class GenUtils:
    @staticmethod
    def extract_guild_and_user_id(ctx: commands.Context) -> Tuple[str, str]:
        guild: Optional[Guild] = ctx.guild
        assert guild is not None, "Command can only be used in guilds"

        return (str(guild.id), str(ctx.author.id))

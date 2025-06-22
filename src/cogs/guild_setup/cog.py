import discord
from discord.ext import commands

from typing import Optional

from db.database import get_session
from db.models import Guild


class GuildSetupCog(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        with get_session() as session:
            existing = session.get(Guild, str(guild.id))

            if existing is None:
                db_guild = Guild(id=str(guild.id))

                session.add(db_guild)
                session.commit()

    @commands.command(name="enable_r34")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def enable_r34(self, ctx: commands.Context) -> None:
        guild: Optional[discord.Guild] = ctx.guild
        assert guild is not None, "`guild_only` command"
        guild_id = str(guild.id)

        with get_session() as session:
            db_guild = session.get(Guild, guild_id)
            assert db_guild is not None, (
                "`before_invoke` hook should create `guild_profile`"
            )

            if db_guild.r34_enabled:
                await ctx.send("`[WARNING] Rule34 is already enabled for this guild`")
                return

            db_guild.r34_enabled = True

            session.add(db_guild)
            session.commit()

        await ctx.send("`Rule34 has been ENABLED for this guild`")

    @commands.command(name="disable_r34")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def disable_r34(self, ctx: commands.Context) -> None:
        guild: Optional[discord.Guild] = ctx.guild
        assert guild is not None, "`guild_only` command"
        guild_id = str(guild.id)

        with get_session() as session:
            db_guild = session.get(Guild, guild_id)
            assert db_guild is not None, (
                "`before_invoke` hook should create `guild_profile`"
            )

            if db_guild.r34_enabled:
                await ctx.send("`[WARNING] Rule34 is already enabled for this guild`")
                return

            db_guild.r34_enabled = False

            session.add(db_guild)
            session.commit()

        await ctx.send("`Rule34 has been DISABLED for this guild`")

    @enable_r34.error
    @disable_r34.error
    async def r34_permission_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "`[ERROR] You must be a server administrator to use this command`"
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("`[ERROR] This command can only be used in servers`")
        else:
            await ctx.send("`[ERROR] An unexpected error occurred`")
            raise error


def setup(client: commands.Bot):
    client.add_cog(GuildSetupCog(client=client))

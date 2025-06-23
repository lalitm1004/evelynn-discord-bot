import discord
from discord.ext import commands

from db.utils import DatabaseUtils as DBUtils
from utils.formatter import Formatter as Fmt
from utils.general import GenUtils


class GuildSetupCog(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await DBUtils.create_guild(guild_id=str(guild.id))

    @commands.group(name="guild", invoke_without_command=True)
    @commands.guild_only()
    async def guild_group(self, ctx: commands.Context) -> None:
        await ctx.reply(Fmt.info("Available subcommands\n+ enable\n+ disable\n"))

    @guild_group.group(name="enable", invoke_without_command=True)
    async def guild_enable(self, ctx: commands.Context) -> None:
        await ctx.reply(Fmt.info("Available subcommands\n+ r34\n"))

    @guild_enable.command(name="r34")
    @commands.has_permissions(administrator=True)
    async def enable_r34(self, ctx: commands.Context) -> None:
        guild_id, _ = GenUtils.extract_guild_and_user_id(ctx)

        db_guild = await DBUtils.fetch_or_create_guild(guild_id)

        if db_guild.r34_enabled:
            await ctx.reply(
                Fmt.warning("Feature_RULE34 is already ENABLED on this guild")
            )
            return

        db_guild = await DBUtils.update_guild(guild_id, r34_enabled=True)

        await ctx.reply(Fmt.success("Feature_RULE34 has been ENABLED on this guild"))

    @guild_group.group(name="disable", invoke_without_command=True)
    async def guild_disable(self, ctx: commands.Context) -> None:
        await ctx.reply(Fmt.info("Available subcommands\n+ r34\n"))

    @guild_disable.command(name="r34")
    @commands.has_permissions(administrator=True)
    async def disable_r34(self, ctx: commands.Context) -> None:
        guild_id, _ = GenUtils.extract_guild_and_user_id(ctx)

        db_guild = await DBUtils.fetch_or_create_guild(guild_id)

        if not db_guild.r34_enabled:
            await ctx.reply(
                Fmt.warning("Feature_RULE34 is already DISABLED on this guild")
            )
            return

        db_guild = await DBUtils.update_guild(guild_id, r34_enabled=False)

        await ctx.reply(Fmt.success("Feature_RULE34 has been DISABLED on this guild"))

    @enable_r34.error
    @disable_r34.error
    async def r34_permission_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                Fmt.warning("You must be a server administrator to use this command")
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.reply(Fmt.warning("This command can only be used in guilds"))
        else:
            await ctx.reply(Fmt.error("An unexpected error occurred"))
            raise error


def setup(client: commands.Bot):
    client.add_cog(GuildSetupCog(client=client))

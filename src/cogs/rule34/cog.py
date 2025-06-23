import discord
from discord.ext import commands

from typing import Final, Optional

from cogs.rule34.api import Rule34API, TagGroup
from cogs.rule34.utils import Rule34DatabaseUtils
from db.models import CommandCategory
from db.utils import DatabaseUtils
from hooks.register import register_hook_command
from utils.formatter import Formatter as Fmt
from utils.general import GenUtils


class Rule34Cog(commands.Cog):
    RULE34_GREEN: Final[int] = 0xAAE5A4

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.r34_api = Rule34API()

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        await register_hook_command(ctx)

        guild: Optional[discord.Guild] = ctx.guild
        if guild is not None:
            db_guild = await DatabaseUtils.fetch_or_create_guild(str(guild.id))
            if not db_guild.r34_enabled:
                raise commands.CheckFailure("Feature_RULE34 is DISABLED for this guild")

    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild: Optional[discord.Guild] = ctx.guild
        if guild is not None:
            guild_id = str(guild.id)
            await DatabaseUtils.increment_command_count(
                guild_id, user_id, CommandCategory.RULE34
            )

    @commands.group(name="rule34", aliases=["r34"], invoke_without_command=True)
    @commands.guild_only()
    @commands.is_nsfw()
    async def rule34_group(self, ctx: commands.Context) -> None:
        pass

    @rule34_group.group(aliases=["blist"])
    async def blacklist_group(self, ctx: commands.Context) -> None:
        pass

    @blacklist_group.command()
    async def view(self, ctx: commands.Context) -> None:
        guild_id, user_id = GenUtils.extract_guild_and_user_id(ctx)

        blacklist = await Rule34DatabaseUtils.get_blacklist(guild_id, user_id)
        blacklist = " ".join(blacklist) if len(blacklist) != 0 else "Empty"

        r34_user_profile = await Rule34DatabaseUtils.fetch_or_create_r34_user_profile(
            guild_id, user_id
        )
        blacklist_enabled = (
            "Enabled" if r34_user_profile.blacklist_enabled else "Disabled"
        )

        blacklist_embed = discord.Embed(
            title=f"Rule34 Blacklist",
            description=f"`Blacklist` - `{blacklist}`\n\n`Blacklist is {blacklist_enabled}`",
            timestamp=ctx.message.created_at,
            color=self.RULE34_GREEN,
        )
        blacklist_embed.set_footer(
            text=ctx.author.display_name, icon_url=ctx.author.display_avatar
        )

        await ctx.reply(embed=blacklist_embed)

    @blacklist_group.command()
    async def add(self, ctx: commands.Context, *, tags: str) -> None:
        guild_id, user_id = GenUtils.extract_guild_and_user_id(ctx)

        tag_list = tags.strip().lower().replace(",", " ").split(" ")
        tag_list = [tag for tag in tag_list if tag.strip()]

        rejected = await Rule34DatabaseUtils.add_blacklist_tags(
            guild_id, user_id, tag_list
        )

        response = f"> **Given tag(s) have been added to your blacklist.**"
        if len(rejected) > 0:
            response = f"> **The following tag(s) were already in your blacklist: **`{' '.join(rejected)}`**, the rest have been inserted.**"

        await ctx.reply(response)

    @blacklist_group.command()
    async def remove(self, ctx: commands.Context, *, tags: str) -> None:
        guild_id, user_id = GenUtils.extract_guild_and_user_id(ctx)

        tag_list = tags.strip().lower().replace(",", " ").split(" ")
        tag_list = [tag for tag in tag_list if tag.strip()]

        rejected = await Rule34DatabaseUtils.remove_blacklist_tags(
            guild_id, user_id, tag_list
        )

        response = f"> **Given tag(s) have been removed from your blacklist.**"
        if len(rejected) > 0:
            response = f"> **The following tag(s) have were not present in your blacklist: **`{' '.join(rejected)}`**, the rest were removed.**"

        await ctx.reply(response)

    @blacklist_group.command()
    async def toggle(self, ctx: commands.Context) -> None:
        guild_id, user_id = GenUtils.extract_guild_and_user_id(ctx)

        r34_user_profile = await Rule34DatabaseUtils.fetch_or_create_r34_user_profile(
            guild_id, user_id
        )
        new_state = not r34_user_profile.blacklist_enabled
        await Rule34DatabaseUtils.update_r34_user_profile(
            guild_id, user_id, blacklist_enabled=new_state
        )

        await ctx.reply(
            f"> **Blacklist is now {'`ENABLED`' if new_state else '`DISABLED`'}**"
        )

    @rule34_group.command()
    async def latest(self, ctx: commands.Context) -> None:
        post = self.r34_api.latest()
        if post is None:
            await ctx.reply(
                Fmt.error(
                    "An unforseen Error has occured. Please contact walmartphilosopher immediately"
                )
            )
            return

        await ctx.reply(post.get_output_string())

    @rule34_group.command()
    async def random(self, ctx: commands.Context) -> None:
        guild_id, user_id = GenUtils.extract_guild_and_user_id(ctx)

        r34_user_profile = await Rule34DatabaseUtils.fetch_or_create_r34_user_profile(
            guild_id, user_id
        )
        if r34_user_profile.blacklist_enabled:
            blacklist = await Rule34DatabaseUtils.get_blacklist(guild_id, user_id)
        else:
            blacklist = []
        tags = TagGroup.from_list([], blacklist, additional_key=guild_id)

        post = self.r34_api.search(tags)
        if post is None:
            await ctx.reply(
                Fmt.error(
                    "An unforseen Error has occured. Please contact walmartphilosopher immediately"
                )
            )
            return

        await ctx.reply(post.get_output_string())

    @rule34_group.command()
    async def search(self, ctx: commands.Context, *, tags: str) -> None:
        guild_id, user_id = GenUtils.extract_guild_and_user_id(ctx)

        r34_user_profile = await Rule34DatabaseUtils.fetch_or_create_r34_user_profile(
            guild_id, user_id
        )
        if r34_user_profile.blacklist_enabled:
            blacklist = await Rule34DatabaseUtils.get_blacklist(guild_id, user_id)
        else:
            blacklist = []

        tag_group = TagGroup.from_string(tags, additional_key=guild_id)
        tag_group.append_to_blacklist(blacklist)

        post = self.r34_api.search(tag_group)
        if post is None:
            await ctx.reply(f"> **Error: Zero posts found for search query.**")
            return

        await ctx.reply(post.get_output_string())

    @rule34_group.error
    async def rule34_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.NSFWChannelRequired):
            await ctx.reply(
                Fmt.warning("Feature_RULE34 can only be used in channels marked NSFW")
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(Fmt.warning(str(error)))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.reply(Fmt.warning("This command can only be used in guilds"))
        else:
            await ctx.reply(Fmt.error("An unexpected error occurred"))
            raise error


def setup(client: commands.Bot):
    client.add_cog(Rule34Cog(client=client))

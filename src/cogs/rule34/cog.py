import discord
from discord.ext import commands

from typing import Final, Optional, List

from db.engine import get_session
from db.models import Guild
from cogs.rule34.api import Rule34API, TagGroup
from cogs.rule34.utils import Rule34DatabaseUtils as DBUtils


class Rule34Cog(commands.Cog):
    RULE34_GREEN: Final = 0xAAE5A4

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.r34_api = Rule34API()

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        guild: Optional[discord.Guild] = ctx.guild
        if guild is not None:
            async with get_session() as session:
                guild_config = await session.get(Guild, str(guild.id))
                if guild_config is None or not guild_config.r34_enabled:
                    raise commands.CheckFailure(
                        "[ERROR] Rule34 is disabled for this guild."
                    )

    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild: Optional[discord.Guild] = ctx.guild
        if guild is not None:
            guild_id = str(guild.id)
            DBUtils.increment_command_count(user_id, guild_id)

    @commands.group(aliases=["r34"])
    @commands.guild_only()
    @commands.is_nsfw()
    async def rule34(self, ctx: commands.Context) -> None:
        pass

    @rule34.group(aliases=["blist"])
    async def blacklist(self, ctx: commands.Context) -> None:
        pass

    @blacklist.command()
    async def view(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        user_blacklist = DBUtils.fetch_blacklist(user_id, guild_id)
        blacklist_str = (
            " ".join(user_blacklist) if len(user_blacklist) != 0 else "Empty"
        )
        if len(blacklist_str) >= 1500:
            blacklist_str = blacklist_str[:1501] + "..."

        blacklist_enabled = DBUtils.is_blacklist_enabled(user_id, guild_id)

        response = (
            f"`Blacklist` - `{blacklist_str}`\n\n"
            f"`Blacklist is {'ENABLED' if blacklist_enabled else 'DISABLED'}`"
        )
        await ctx.reply(response)

    @blacklist.command()
    async def add(self, ctx: commands.Context, *, tags: str) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        tag_list = tags.strip().lower().replace(",", " ").split(" ")
        tag_list = list(set([tag for tag in tag_list if tag.strip()]))

        success: List[str] = []
        for tag in tag_list:
            res = DBUtils.push_to_blacklist(user_id, guild_id, tag)
            if res:
                success.append(tag)

        response = f"> **Given tag(s) have been added to your blacklist.**"
        if len(tag_list) != len(success):
            response = f"> **The following tag(s) have been added to your blacklist:**`{' '.join(success)}`**, the rest were duplicates.**"

        await ctx.reply(response)

    @blacklist.command()
    async def remove(self, ctx: commands.Context, *, tags: str) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        tag_list = tags.strip().lower().replace(",", " ").split(" ")
        tag_list = list(set([tag for tag in tag_list if tag.strip()]))

        success: List[str] = []
        for tag in tag_list:
            res = DBUtils.pop_from_blacklist(user_id, guild_id, tag)
            if res:
                success.append(tag)

        response = f"> **Given tag(s) have been removed from your blacklist.**"
        if len(tag_list) != len(success):
            response = f"> **The following tag(s) have been removed from your blacklist:**`{' '.join(success)}`**, the rest did not exist.**"

        await ctx.reply(response)

    @blacklist.command()
    async def toggle(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        new_state = DBUtils.toggle_user_blacklist(user_id, guild_id)
        await ctx.reply(
            f"> **Blacklist is now` {'`ENABLED`' if new_state else '`DISABLED`'}**"
        )

    @rule34.command()
    async def random(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        blacklist = DBUtils.fetch_blacklist(user_id, guild_id)
        tags = TagGroup.from_list([], blacklist)

        post = self.r34_api.search(tags)
        if post is None:
            await ctx.reply(
                f"> **An unforseen Error has occured. Please contact walmartPhilosopher immediately.**"
            )
            return

        await ctx.reply(post.get_output_string())

    @rule34.command()
    async def search(self, ctx: commands.Context, *, tags: str) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        blacklist = DBUtils.fetch_blacklist(user_id, guild_id)
        tag_group = TagGroup.from_string(tags)
        tag_group.append_to_blacklist(blacklist)

        conflicts = tag_group.get_conflicting_tags()
        if len(conflicts) > 0:
            await ctx.reply(
                f"> **Error: Conflicting Tag(s). The following tag(s) are in your blacklist and search query at the same time:** `{' '.join(conflicts)}`**. Remove them from your blacklist or disable your blacklist to search for them.**"
            )
            return

        post = self.r34_api.search(tag_group)
        if post is None:
            await ctx.reply(f"> **Error: Zero posts found for search query.**")
            return

        await ctx.reply(post.get_output_string())

    @rule34.command()
    async def latest(self, ctx: commands.Context) -> None:
        post = self.r34_api.latest()
        if post is None:
            await ctx.reply(
                f"> **An unforseen Error has occured. Please contact walmartPhilosopher immediately.**"
            )
            return

        await ctx.reply(post.get_output_string())

    @rule34.error
    async def rule34_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.NSFWChannelRequired):
            await ctx.reply(
                f"> **Error: Command can only be run on channels marked NSFW.**"
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(f"{error}")


def setup(client: commands.Bot):
    client.add_cog(Rule34Cog(client=client))

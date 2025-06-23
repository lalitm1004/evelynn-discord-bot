import discord
from discord.ext import commands

import asyncio
from math import ceil
from pathlib import Path

from db.engine import init_db
from env import EnvConfig
from hooks.register import register_hook

environment = EnvConfig.from_env()


async def setup_bot() -> commands.Bot:
    await init_db()

    client = commands.Bot(
        command_prefix=">>", help_command=None, intents=discord.Intents.all()
    )

    client.before_invoke(register_hook())

    @client.event
    async def on_ready() -> None:
        if environment.DEBUG_CHANNEL_ID:
            channel = await client.fetch_channel(environment.DEBUG_CHANNEL_ID)

            if isinstance(channel, discord.TextChannel):
                await channel.send(f"## Logged in as {client.user}")
            else:
                raise TypeError("DEBUG_CHANNEL_ID does not point to a text channel")

        print(f"Logged in as {client.user}")

    # TEST command
    @client.command()
    async def ping(ctx: commands.Context) -> None:
        await ctx.message.channel.send(
            f"pong!\n> `Client Latency > {ceil(client.latency * 100)}ms`"
        )

    # load up cogs
    cogs_path = Path("src/cogs")
    for folder in cogs_path.iterdir():
        if not folder.is_dir():
            continue

        for file in folder.glob("*cog.py"):
            module = f"cogs.{folder.name}.{file.stem}"
            client.load_extension(module)

    return client


async def main():
    client = await setup_bot()

    try:
        await client.start(environment.BOT_TOKEN)
    except KeyboardInterrupt:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

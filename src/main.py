import discord
from discord.ext import commands

from pathlib import Path

from env import EnvConfig
from db.database import init_db

from hooks.register import register_hook

environment = EnvConfig.from_env()
init_db()

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
    await ctx.message.channel.send("pong")


# load up cogs
cogs_path = Path("src/cogs")
for folder in cogs_path.iterdir():
    if not folder.is_dir():
        continue

    for file in folder.glob("*cog.py"):
        module = f"cogs.{folder.name}.{file.stem}"
        client.load_extension(module)


client.run(environment.BOT_TOKEN)

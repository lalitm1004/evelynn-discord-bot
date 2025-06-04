import discord
from discord.ext import commands
from pathlib import Path

from env import EnvConfig

environment = EnvConfig.from_env()

client = commands.Bot(
    command_prefix=">>", help_command=None, intents=discord.Intents.all()
)


@client.event
async def on_ready() -> None:
    channel = await client.fetch_channel(environment.DEBUG_CHANNEL_ID)

    if isinstance(channel, discord.TextChannel):
        await channel.send(f"## Logged in as {client.user}")
    else:
        raise TypeError("DEBUG_CHANNEL_ID does not point to a text channel")

    print(f"Logged in as {client.user}")


# load up cogs
cogs_path = Path("src/cogs")
for folder in cogs_path.iterdir():
    if not folder.is_dir():
        continue

    for file in folder.glob("*cog.py"):
        module = f"cogs.{folder.name}.{file.stem}"
        client.load_extension(module)


client.run(environment.BOT_TOKEN)

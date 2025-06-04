from dataclasses import dataclass
from dotenv import load_dotenv
from os import getenv


@dataclass
class EnvConfig:
    BOT_TOKEN: str
    DEBUG_CHANNEL_ID: int

    @classmethod
    def from_env(cls) -> "EnvConfig":
        load_dotenv()
        BOT_TOKEN = getenv("BOT_TOKEN")
        DEBUG_CHANNEL_ID = getenv("DEBUG_CHANNEL_ID")

        missing = []
        if BOT_TOKEN is None:
            missing.append("BOT_TOKEN")

        if DEBUG_CHANNEL_ID is None:
            missing.append("DEBUG_CHANNEL_ID")

        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return cls(
            BOT_TOKEN=str(BOT_TOKEN), DEBUG_CHANNEL_ID=int(str(DEBUG_CHANNEL_ID))
        )

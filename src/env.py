from dataclasses import dataclass
from dotenv import load_dotenv
from os import getenv
from typing import Optional


@dataclass
class EnvConfig:
    BOT_TOKEN: str
    DEBUG_CHANNEL_ID: int

    @classmethod
    def from_env(cls) -> "EnvConfig":
        load_dotenv()

        bot_token: Optional[str] = getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN is not set")

        debug_channel_id_str: Optional[str] = getenv("DEBUG_CHANNEL_ID")
        if not debug_channel_id_str:
            raise ValueError("DEBUG_CHANNEL_ID is not set")

        try:
            debug_channel_id: int = int(debug_channel_id_str)
        except ValueError:
            raise ValueError("DEBUG_CHANNEL_ID must be a valid integer")

        return cls(BOT_TOKEN=bot_token, DEBUG_CHANNEL_ID=debug_channel_id)

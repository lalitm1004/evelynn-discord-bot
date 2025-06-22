from dataclasses import dataclass
from dotenv import load_dotenv
from os import getenv
from typing import Optional


@dataclass
class EnvConfig:
    BOT_TOKEN: str
    DEBUG_CHANNEL_ID: Optional[int]

    @classmethod
    def from_env(cls) -> "EnvConfig":
        load_dotenv()

        bot_token: Optional[str] = getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN is not set")

        debug_channel_id_str: Optional[str] = getenv("DEBUG_CHANNEL_ID")
        debug_channel_id: Optional[int] = None

        if debug_channel_id_str:
            try:
                debug_channel_id = int(debug_channel_id_str)
            except ValueError:
                raise ValueError("DEBUG_CHANNEL_ID must be a valid integer")
        else:
            print("DEBUG_CHANNEL_ID is not set. Debug logs will be disabled")

        return cls(BOT_TOKEN=bot_token, DEBUG_CHANNEL_ID=debug_channel_id)

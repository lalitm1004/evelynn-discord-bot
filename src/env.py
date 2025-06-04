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

        errors = []

        if BOT_TOKEN is None:
            errors.append("BOT_TOKEN is not set")
        elif not BOT_TOKEN.strip():
            errors.append("BOT_TOKEN is empty")

        debug_channel_id_int = 0
        if DEBUG_CHANNEL_ID is None:
            errors.append("BOT_TOKEN is not set")
        else:
            try:
                debug_channel_id_int = int(DEBUG_CHANNEL_ID)
            except ValueError:
                errors.append(
                    f"DEBUG_CHANNEL_ID is not a valid integer, got {DEBUG_CHANNEL_ID}"
                )

        if errors:
            error_message = "Environment configuration errors:\n" + "\n".join(
                f"\t- {error}" for error in errors
            )
            raise EnvironmentError(error_message)

        assert BOT_TOKEN is not None
        return cls(BOT_TOKEN=BOT_TOKEN, DEBUG_CHANNEL_ID=debug_channel_id_int)

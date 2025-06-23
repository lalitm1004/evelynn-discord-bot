class Formatter:
    @staticmethod
    def error(error_message: str) -> str:
        return f"```\n🔴 [ ERROR ]\n\n{error_message}\n```"

    @staticmethod
    def warning(warning_message: str) -> str:
        return f"```\n🟡 [ WARNING ]\n\n{warning_message}\n```"

    @staticmethod
    def success(success_message: str) -> str:
        return f"```\n🟢 [ SUCCESS ]\n\n{success_message}\n```"

    @staticmethod
    def info(info_message: str) -> str:
        return f"```\n📑 [ INFO ]\n\n{info_message}\n```"

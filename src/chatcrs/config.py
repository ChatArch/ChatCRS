"Typed environment configuration for ChatCRS."

from chatenv import BaseEnvConfig, EnvField


class ChatcrsConfig(BaseEnvConfig):
    "ChatCRS ChatEnv configuration."

    _title = "ChatCRS Configuration"
    _aliases = ["chatcrs"]
    _storage_dir = "Chatcrs"

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; no network test is required.")

    CHATCRS_BASE_URL = EnvField(
        "CHATCRS_BASE_URL",
        desc="Remote CRS base URL, for example https://crs.example.com",
    )

    CHATCRS_API_KEY = EnvField(
        "CHATCRS_API_KEY",
        desc="CRS API key for key-only self inspection",
        is_sensitive=True,
    )

    CHATCRS_ADMIN_USERNAME = EnvField(
        "CHATCRS_ADMIN_USERNAME",
        desc="CRS administrator username",
        is_sensitive=True,
    )

    CHATCRS_ADMIN_PASSWORD = EnvField(
        "CHATCRS_ADMIN_PASSWORD",
        desc="CRS administrator password",
        is_sensitive=True,
    )

    CHATCRS_ADMIN_TOKEN = EnvField(
        "CHATCRS_ADMIN_TOKEN",
        desc="CRS administrator bearer token",
        is_sensitive=True,
    )

    CHATCRS_SSH_ALIAS = EnvField(
        "CHATCRS_SSH_ALIAS",
        desc="SSH target alias for guarded service lifecycle commands",
    )

    CHATCRS_APP_DIR = EnvField(
        "CHATCRS_APP_DIR",
        desc="Remote CRS app directory for guarded service lifecycle commands",
    )

    CHATCRS_CRS_COMMAND = EnvField(
        "CHATCRS_CRS_COMMAND",
        desc="Remote official crs command path; defaults to crs",
    )


__all__ = ["ChatcrsConfig"]

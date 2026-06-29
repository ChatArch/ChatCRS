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

    CHATCRS_API_KEY = EnvField(
        "CHATCRS_API_KEY",
        desc="API key",
        is_sensitive=True,
    )


__all__ = ["ChatcrsConfig"]

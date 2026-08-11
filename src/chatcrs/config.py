"Typed environment configuration for ChatCRS."

from chatenv import BaseEnvConfig, EnvField


class ChatcrsConfig(BaseEnvConfig):
    "CRS HTTP/API ChatEnv configuration used by ChatCRS."

    _title = "CRS Configuration"
    _aliases = ["chatcrs", "crs"]
    _storage_dir = "CRS"

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; no network test is required.")

    CRS_API_BASE = EnvField(
        "CRS_API_BASE",
        desc="Remote CRS base URL, for example https://crs.example.com",
    )

    CRS_API_KEY = EnvField(
        "CRS_API_KEY",
        desc="CRS API key for key-only self inspection",
        is_sensitive=True,
    )

    CRS_USERNAME = EnvField(
        "CRS_USERNAME",
        desc="CRS administrator username",
        is_sensitive=True,
    )

    CRS_PASSWORD = EnvField(
        "CRS_PASSWORD",
        desc="CRS administrator password",
        is_sensitive=True,
    )

__all__ = ["ChatcrsConfig"]

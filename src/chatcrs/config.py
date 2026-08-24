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


class CodexConfig(BaseEnvConfig):
    """ChatCRS-owned Codex OAuth configuration.

    The env keys intentionally keep the OpenAI/Codex protocol names, while the
    storage namespace is separate from ChatEnv's general OpenAI profiles.
    """

    _title = "Codex OAuth Configuration"
    _aliases = ["codex", "chatcrs-codex"]
    _storage_dir = "Codex"

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; no network test is required.")

    OPENAI_REFRESH_TOKEN = EnvField(
        "OPENAI_REFRESH_TOKEN",
        desc="OpenAI/Codex OAuth refresh token owned by ChatCRS.",
        is_sensitive=True,
    )

    OPENAI_OAUTH_BASE_URL = EnvField(
        "OPENAI_OAUTH_BASE_URL",
        desc="OpenAI OAuth auth server base URL used to refresh Codex access tokens.",
    )

    OPENAI_CODEX_CLIENT_ID = EnvField(
        "OPENAI_CODEX_CLIENT_ID",
        desc="OpenAI Codex OAuth client id override.",
    )

    OPENAI_OAUTH_CLIENT_ID = EnvField(
        "OPENAI_OAUTH_CLIENT_ID",
        desc="OpenAI OAuth client id override.",
    )

    OPENAI_CLIENT_ID = EnvField(
        "OPENAI_CLIENT_ID",
        desc="OpenAI client id fallback override.",
    )

    CHATGPT_BACKEND_BASE_URL = EnvField(
        "CHATGPT_BACKEND_BASE_URL",
        desc="ChatGPT backend API base URL for Codex usage/quota requests.",
    )

    OPENAI_CHATGPT_BACKEND_BASE_URL = EnvField(
        "OPENAI_CHATGPT_BACKEND_BASE_URL",
        desc="OpenAI ChatGPT backend API base URL override.",
    )

    OPENAI_CODEX_BACKEND_BASE_URL = EnvField(
        "OPENAI_CODEX_BACKEND_BASE_URL",
        desc="OpenAI Codex backend API base URL override.",
    )


__all__ = ["ChatcrsConfig", "CodexConfig"]

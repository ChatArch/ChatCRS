"Typed environment configuration for ChatCRS."

from chatenv import BaseEnvConfig, EnvField


class ChatcrsConfig(BaseEnvConfig):
    "CRS HTTP/API ChatEnv configuration used by ChatCRS."

    _title = "CRS Configuration"
    _aliases = ["chatcrs", "crs"]
    _storage_dir = "CRS"

    @classmethod
    def test(cls) -> None:
        """Authenticate the active CRS key; optionally smoke its model route."""
        import click
        from chatenv import EnvStore, get_paths

        from chatcrs.remote import CrsHttpClient, CrsProfile

        # ChatEnv 0.2.x test dispatch does not load fields. Honor its --home
        # override without resolving ChatCRS's unrelated default admin profile.
        ctx = click.get_current_context(silent=True)
        home = ctx.find_root().params.get("home") if ctx else None
        stage = "configuration"
        try:
            cls.load_from_sources(EnvStore(get_paths(home).envs_dir).load_active(cls))
            base = str(cls.CRS_API_BASE.value or "").strip().rstrip("/")
            key = str(cls.CRS_API_KEY.value or "").strip()
            model = str(cls.CRS_API_MODEL.value or "").strip()
            for name, value in (("CRS_API_BASE", base), ("CRS_API_KEY", key)):
                if not value:
                    raise click.ClickException(f"CRS test requires {name}.")
            client = CrsHttpClient(
                CrsProfile(base_url=base, api_key=key),
                home=home, explicit_admin_token=True,
            )
            stage = "key authentication"
            result = client.key_info()
            info = result["key_info"]
            if (not result["ok"] or not isinstance(info, dict) or not info
                    or info.get("success") is False or info.get("error") or "raw" in info):
                raise click.ClickException("CRS key authentication failed; check CRS_API_BASE / CRS_API_KEY.")
            print("Key authentication succeeded.")
            if not model:
                print("CRS_API_MODEL is unset: key-only verification; upstream not tested.")
                return
            stage = "Codex Responses text test"
            client.responses_smoke(model=model)
            print("Codex Responses text test succeeded.")
        except click.ClickException:
            raise
        except Exception:
            # Never render exception text, URLs, response bodies, or credentials.
            raise click.ClickException(f"CRS {stage} failed; check configuration and service availability.") from None

    CRS_API_BASE = EnvField(
        "CRS_API_BASE",
        desc="Remote CRS base URL, for example https://crs.example.com",
    )

    CRS_API_KEY = EnvField(
        "CRS_API_KEY",
        desc="CRS API key for key-only self inspection",
        is_sensitive=True,
    )

    CRS_API_MODEL = EnvField(
        "CRS_API_MODEL",
        desc="Optional Codex model for chatenv test; unset verifies only CRS key authentication",
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

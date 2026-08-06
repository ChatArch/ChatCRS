from chatcrs.redaction import redact


def test_redact_masks_sensitive_keys_and_token_patterns():
    payload = {
        "token": "«redacted:ghp_…»",
        "nested": {"REDIS_PASSWORD": "super-secret", "PORT": "12391"},
        "line": "Authorization: Bearer ***",
    }

    redacted = redact(payload)

    assert redacted["token"] == "[REDACTED]"
    assert redacted["nested"]["REDIS_PASSWORD"] == "[REDACTED]"
    assert redacted["nested"]["PORT"] == "12391"
    assert "abcdefghijklmnopqrstuvwxyz" not in redacted["line"]
    assert "[REDACTED]" in redacted["line"]

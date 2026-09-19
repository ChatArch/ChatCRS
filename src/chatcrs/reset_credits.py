"""Codex banked-reset HTTP client and guarded operator helpers.

These are ChatGPT backend endpoints, not a stable public OpenAI Platform API.
No method refreshes OAuth or generates model output. Dashboard policy belongs
in the consumer; this module owns transport, profile reads and safe receipts.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from chatenv import get_paths
from chatcrs import codex_direct

MAX_RESPONSE_BYTES = 1048576
OUTCOMES = {'reset', 'nothing_to_reset', 'no_credit', 'already_redeemed'}


class SafeResetError(RuntimeError):
    """An error whose text never embeds upstream bodies or credentials."""
    def __init__(self, status: int | None, code: str = 'request_failed'):
        self.status = status
        self.code = code if re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', code) else 'request_failed'
        super().__init__(f'Codex reset request failed: status={status} code={self.code}')


from chatcrs.http import open_request


def _base(value: str) -> str:
    parts = urllib.parse.urlsplit(value)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('Codex backend must be an HTTPS base without credentials, query or fragment')
    return value.rstrip('/')


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _http(method: str, url: str, headers: dict, body: dict | None, timeout: float) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with open_request(request, timeout=timeout) as response:
            status, raw = response.status, response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError):
        raise SafeResetError(None, 'network_error') from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise SafeResetError(status, 'response_too_large')
    try:
        return status, json.loads(raw)
    except (ValueError, UnicodeError):
        raise SafeResetError(status, 'invalid_json') from None


class CodexResetClient:
    """Profile-scoped, non-refreshing client with injectable HTTP transport.

    Raw return values are for trusted in-process consumers. Use the summary
    helpers for CLI/dashboard output. Identity is hashed for durable de-duping.
    """
    def __init__(self, access_token: str, account_id: str, backend_base_url: str, *, reset_base_url: str | None = None, transport: Callable | None = None, timeout: float = 20):
        if not isinstance(access_token, str) or not access_token or not isinstance(account_id, str) or not account_id:
            raise ValueError('Stored Codex access token and account mapping are required')
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('Timeout must be a positive finite number')
        self._access_token, self._account_id = access_token, account_id
        self.backend_base_url = _base(backend_base_url)
        self.reset_base_url = _base(reset_base_url or backend_base_url)
        self.identity = _hash(account_id)
        self.timeout = timeout
        self._transport = transport or _http

    def __repr__(self) -> str:
        return f'CodexResetClient(identity={self.identity[:12]!r})'

    @classmethod
    def from_profile(cls, profile: str = 'default', *, home: str | Path | None = None, reset_base_url: str | None = None, timeout: float = 20, transport: Callable | None = None):
        profile_name = codex_direct._normalize_profile(profile)
        values = codex_direct._stored_values(profile=profile_name, home=home)
        config = codex_direct._codex_profile_values_or_empty(profile=profile_name, home=home)
        return cls(values.get('access_token'), values.get('account_id'), codex_direct._configured_backend_base_url(config), reset_base_url=reset_base_url, timeout=timeout, transport=transport)

    def _call(self, method: str, base: str, path: str, body: dict | None = None) -> dict:
        headers = {'Authorization': 'Bearer ' + self._access_token, 'ChatGPT-Account-ID': self._account_id,
                   'Accept': 'application/json', 'OpenAI-Beta': 'codex-1', 'originator': 'Codex Desktop',
                   'User-Agent': 'codex_cli_rs/0.0.0 (ChatCRS)'}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        try:
            status, payload = self._transport(method, base + path, headers, body, self.timeout)
        except SafeResetError:
            raise
        except Exception:
            raise SafeResetError(None, 'transport_error') from None
        if status != 200 or not isinstance(payload, dict):
            detail = payload.get('detail', payload.get('error', {})) if isinstance(payload, dict) else {}
            code = detail.get('code', 'request_failed') if isinstance(detail, dict) else 'request_failed'
            raise SafeResetError(status, code if isinstance(code, str) else 'request_failed')
        return payload

    def usage(self) -> dict:
        data = self._call('GET', self.backend_base_url, '/wham/usage')
        if data.get('account_id') is not None and data['account_id'] != self._account_id:
            raise SafeResetError(200, 'account_identity_mismatch')
        return data

    def reset_credits(self) -> dict:
        return self._call('GET', self.reset_base_url, '/wham/rate-limit-reset-credits')

    def consume(self, request_id: str, *, credit_id: str | None = None, execute: bool = False) -> dict:
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 128:
            raise ValueError('A non-empty, persistent request id of at most 128 characters is required')
        if not isinstance(execute, bool):
            raise ValueError('execute must be a boolean')
        if credit_id is not None and (not isinstance(credit_id, str) or not credit_id or len(credit_id) > 256):
            raise ValueError('Invalid credit id')
        if not execute:
            return {'code': 'dry_run', 'mutated': False}
        body = {'redeem_request_id': request_id}
        if credit_id is not None:
            body['credit_id'] = credit_id
        return self._call('POST', self.reset_base_url, '/wham/rate-limit-reset-credits/consume', body)


def summarize_credits(data: dict) -> dict:
    """Allowlist credit metadata; exclude raw identities and arbitrary text."""
    count = data.get('available_count')
    if type(count) is not int or count < 0:
        raise SafeResetError(200, 'invalid_credit_count')
    rows = data.get('credits')
    safe = []
    for item in rows if isinstance(rows, list) else []:
        if not isinstance(item, dict):
            continue
        row = {key: item.get(key) for key in ('status', 'reset_type', 'granted_at', 'expires_at', 'redeemed_at') if item.get(key) is None or isinstance(item.get(key), str)}
        row = codex_direct._redact_identity(row)
        if isinstance(item.get('id'), str):
            row['id_hash'] = _hash(item['id'])[:12]
        safe.append(row)
    return {'available_count': count, 'credits': safe}


def inspect_reset_credits(*, profile: str = 'default', reset_base_url: str | None = None, timeout: float = 20, home: str | Path | None = None) -> dict:
    client = CodexResetClient.from_profile(profile, home=home, reset_base_url=reset_base_url, timeout=timeout)
    return {'ok': True, 'profile': profile, 'account_id_hash': client.identity[:12], **summarize_credits(client.reset_credits())}


def _safe_windows(usage: dict) -> dict:
    limits = usage.get('rate_limit')
    if not isinstance(limits, dict):
        return {}
    return {name: {key: value for key, value in window.items() if key in ('used_percent', 'reset_at', 'reset_after_seconds', 'limit_window_seconds') and type(value) in (int, float) and math.isfinite(value)} for name, window in limits.items() if name in ('primary_window', 'secondary_window') and isinstance(window, dict)}


def consume_reset_credit(*, profile: str = 'default', request_id: str, reset_base_url: str | None = None, execute: bool = False, timeout: float = 20, home: str | Path | None = None) -> dict:
    """Guarded manual operator path. A request id can only be attempted once.

    A dashboard should use its own policy/reservation ledger with the client.
    No automatic retry is made; uncertain requests require read-only resolution.
    """
    if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 128:
        raise ValueError('A persistent non-empty request id is required')
    if execute is not True:
        return {'ok': True, 'profile': profile, 'mutated': False, 'code': 'dry_run'}
    client = CodexResetClient.from_profile(profile, home=home, reset_base_url=reset_base_url, timeout=timeout)
    before = summarize_credits(client.reset_credits())
    before_usage = _safe_windows(client.usage())
    if before['available_count'] <= 0:
        return {'ok': False, 'profile': profile, 'mutated': False, 'code': 'no_credit'}
    root = get_paths(home).home_dir / 'chatcrs' / 'reset-audits' / client.identity
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / (_hash(request_id) + '.safe.json')
    receipt = {'profile': profile, 'account_id_hash': client.identity[:12], 'request_id': request_id, 'state': 'pending', 'before': before, 'usage_before': before_usage, 'at': datetime.now(timezone.utc).isoformat()}
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return {'ok': False, 'profile': profile, 'mutated': False, 'code': 'already_attempted', 'audit_path': str(path)}
    with os.fdopen(fd, 'w') as stream:
        json.dump(receipt, stream)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        result = client.consume(request_id, execute=True)
        outcome = result.get('code')
        receipt['code'] = outcome if outcome in OUTCOMES else 'unknown'
        receipt['windows_reset'] = result.get('windows_reset') if type(result.get('windows_reset')) is int else None
        receipt['after'] = summarize_credits(client.reset_credits())
        receipt['usage_after'] = _safe_windows(client.usage())
        decreased = any('used_percent' in old and 'used_percent' in receipt['usage_after'].get(name, {}) and receipt['usage_after'][name]['used_percent'] < old['used_percent'] for name, old in before_usage.items())
        receipt['state'] = 'verified' if outcome == 'reset' and (receipt['windows_reset'] or 0) > 0 and decreased and receipt['after']['available_count'] < before['available_count'] else 'not_verified'
    except Exception:
        receipt['state'] = 'uncertain'
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'ok': receipt['state'] == 'verified', 'profile': profile, 'code': receipt.get('code', 'unknown'), 'state': receipt['state'], 'mutated': receipt['state'] == 'verified', 'audit_path': str(path)}

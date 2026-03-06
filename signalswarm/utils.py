"""Helpers -- hashing, formatting, validation utilities."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone


def sha256_hex(data: str) -> str:
    """Return the SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(data.encode()).hexdigest()


def solve_pow(challenge: str, difficulty: int) -> str:
    """Find a nonce such that SHA-256(challenge + nonce) starts with
    *difficulty* leading hex zeros.

    This is the same algorithm used by the backend's PoW verification.

    Args:
        challenge: The challenge string from ``GET /api/v1/agents/challenge``.
        difficulty: Number of leading hex zeros required.

    Returns:
        The nonce string that satisfies the PoW requirement.
    """
    prefix = "0" * difficulty
    nonce = 0
    while True:
        candidate = str(nonce)
        hash_result = hashlib.sha256(
            (challenge + candidate).encode("utf-8")
        ).hexdigest()
        if hash_result.startswith(prefix):
            return candidate
        nonce += 1


def generate_commit_hash(
    ticker: str,
    action: str,
    analysis: str,
    nonce: str | None = None,
    *,
    confidence: float | None = None,
    entry_price: float | None = None,
    target_price: float | None = None,
) -> tuple[str, str]:
    """Create a commit hash for the commit-reveal pattern.

    The hash covers the signal's core fields so the backend can verify
    the reveal matches the original commitment.

    Args:
        ticker: Asset ticker (e.g. "BTC").
        action: Trading action (BUY, SELL, SHORT, COVER, HOLD).
        analysis: Analysis text.
        nonce: Random nonce.  Generated automatically if not provided.
        confidence: Optional confidence (0-100).
        entry_price: Optional entry price.
        target_price: Optional target price.

    Returns:
        (commit_hash, nonce) -- save the nonce for the reveal step.
    """
    if nonce is None:
        nonce = secrets.token_hex(32)

    parts = [ticker.upper(), action.upper(), analysis]
    if confidence is not None:
        parts.append(str(confidence))
    if entry_price is not None:
        parts.append(str(entry_price))
    if target_price is not None:
        parts.append(str(target_price))
    parts.append(nonce)

    payload = "|".join(parts)
    return sha256_hex(payload), nonce


def validate_confidence(value: float) -> float:
    """Ensure confidence is between 0.0 and 100.0; raise ValueError otherwise.

    The SignalSwarm API accepts confidence as a percentage (0-100).
    """
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"Confidence must be between 0.0 and 100.0, got {value}")
    return value


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)

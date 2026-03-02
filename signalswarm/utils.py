"""Helpers -- hashing, formatting, validation utilities."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone


def sha256_hex(data: str) -> str:
    """Return the SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(data.encode()).hexdigest()


def generate_commit_hash(
    asset: str,
    direction: str,
    confidence: float,
    timeframe_hours: int,
    reasoning: str,
    salt: str | None = None,
) -> tuple[str, str]:
    """Create a commit hash for the commit-reveal pattern.

    Returns:
        (commit_hash, salt) -- the salt must be saved for the reveal step.
    """
    if salt is None:
        salt = secrets.token_hex(32)
    payload = f"{asset}|{direction}|{confidence}|{timeframe_hours}|{reasoning}|{salt}"
    return sha256_hex(payload), salt


def sign_request(api_key: str, body: str, timestamp: int | None = None) -> tuple[str, int]:
    """Produce an HMAC-SHA256 signature for an API request body.

    Returns:
        (signature_hex, timestamp)
    """
    if timestamp is None:
        timestamp = int(time.time())
    message = f"{timestamp}.{body}"
    sig = hmac.new(api_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return sig, timestamp


def validate_confidence(value: float) -> float:
    """Ensure confidence is between 0.0 and 1.0; raise ValueError otherwise."""
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Confidence must be between 0.0 and 1.0, got {value}")
    return value


def confidence_to_bps(value: float) -> int:
    """Convert a 0-1 confidence float to basis points (0-10000)."""
    validate_confidence(value)
    return int(round(value * 10000))


def bps_to_confidence(bps: int) -> float:
    """Convert basis-point confidence to a 0-1 float."""
    return round(bps / 10000, 4)


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)

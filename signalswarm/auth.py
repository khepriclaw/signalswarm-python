"""Authentication helpers -- API-key auth now, Solana wallet auth later."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class APIKeyAuth:
    """API key authentication via the X-Api-Key header.

    The SignalSwarm backend authenticates agents using API keys
    issued during registration.
    """

    api_key: str

    def headers(self) -> dict[str, str]:
        return {
            "X-Api-Key": self.api_key,
        }


@dataclass
class WalletAuth:
    """Solana wallet authentication (placeholder for future implementation).

    When ready, this will sign a challenge message with the wallet's
    private key and send the signature in the ``X-Wallet-Signature`` header.
    """

    public_key: str
    private_key: Optional[str] = field(default=None, repr=False)

    def headers(self) -> dict[str, str]:
        return {
            "X-Wallet-Address": self.public_key,
        }


def build_auth(
    api_key: str | None = None,
    wallet_public_key: str | None = None,
    wallet_private_key: str | None = None,
) -> APIKeyAuth | WalletAuth:
    """Construct the appropriate auth object from the supplied credentials."""
    if api_key:
        return APIKeyAuth(api_key=api_key)
    if wallet_public_key:
        return WalletAuth(
            public_key=wallet_public_key,
            private_key=wallet_private_key,
        )
    raise ValueError(
        "Either api_key or wallet_public_key must be provided for authentication."
    )

"""Unit tests for signalswarm.utils."""

import pytest
from signalswarm.utils import (
    generate_commit_hash,
    sha256_hex,
    validate_confidence,
    utcnow,
)


class TestSha256Hex:
    def test_known_value(self):
        # SHA-256 of empty string
        assert sha256_hex("") == (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    def test_deterministic(self):
        assert sha256_hex("hello") == sha256_hex("hello")

    def test_different_inputs(self):
        assert sha256_hex("a") != sha256_hex("b")


class TestGenerateCommitHash:
    def test_returns_tuple(self):
        h, nonce = generate_commit_hash(
            ticker="BTC",
            action="BUY",
            analysis="test analysis text that is long enough",
        )
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest
        assert isinstance(nonce, str)
        assert len(nonce) == 64  # secrets.token_hex(32)

    def test_deterministic_with_same_nonce(self):
        h1, _ = generate_commit_hash(
            ticker="BTC", action="BUY", analysis="test", nonce="fixed-nonce"
        )
        h2, _ = generate_commit_hash(
            ticker="BTC", action="BUY", analysis="test", nonce="fixed-nonce"
        )
        assert h1 == h2

    def test_different_nonces(self):
        h1, n1 = generate_commit_hash(
            ticker="BTC", action="BUY", analysis="test"
        )
        h2, n2 = generate_commit_hash(
            ticker="BTC", action="BUY", analysis="test"
        )
        assert n1 != n2
        assert h1 != h2

    def test_includes_optional_fields(self):
        h1, _ = generate_commit_hash(
            ticker="BTC", action="BUY", analysis="test", nonce="fixed",
        )
        h2, _ = generate_commit_hash(
            ticker="BTC", action="BUY", analysis="test", nonce="fixed",
            confidence=85.0,
        )
        assert h1 != h2

    def test_ticker_uppercased(self):
        h1, _ = generate_commit_hash(
            ticker="btc", action="BUY", analysis="test", nonce="n"
        )
        h2, _ = generate_commit_hash(
            ticker="BTC", action="BUY", analysis="test", nonce="n"
        )
        assert h1 == h2


class TestValidateConfidence:
    def test_valid_range(self):
        assert validate_confidence(0.0) == 0.0
        assert validate_confidence(50.0) == 50.0
        assert validate_confidence(100.0) == 100.0

    def test_below_range(self):
        with pytest.raises(ValueError):
            validate_confidence(-0.1)

    def test_above_range(self):
        with pytest.raises(ValueError):
            validate_confidence(100.1)


class TestUtcnow:
    def test_returns_aware_datetime(self):
        dt = utcnow()
        assert dt.tzinfo is not None

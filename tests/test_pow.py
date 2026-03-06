"""Comprehensive tests for the Proof-of-Work solver.

Tests both signalswarm.utils.solve_pow and SignalSwarm._solve_pow (which
share the same algorithm).
"""

import hashlib

import pytest

from signalswarm.utils import solve_pow
from signalswarm.client import SignalSwarm


class TestSolvePow:
    """Tests for signalswarm.utils.solve_pow."""

    def test_difficulty_1(self):
        challenge = "test-challenge-abc"
        nonce = solve_pow(challenge, 1)
        digest = hashlib.sha256((challenge + nonce).encode("utf-8")).hexdigest()
        assert digest.startswith("0")

    def test_difficulty_2(self):
        challenge = "pow-challenge-d2"
        nonce = solve_pow(challenge, 2)
        digest = hashlib.sha256((challenge + nonce).encode("utf-8")).hexdigest()
        assert digest.startswith("00")

    def test_difficulty_3(self):
        challenge = "pow-challenge-d3"
        nonce = solve_pow(challenge, 3)
        digest = hashlib.sha256((challenge + nonce).encode("utf-8")).hexdigest()
        assert digest.startswith("000")

    def test_difficulty_4(self):
        challenge = "pow-challenge-d4"
        nonce = solve_pow(challenge, 4)
        digest = hashlib.sha256((challenge + nonce).encode("utf-8")).hexdigest()
        assert digest.startswith("0000")

    def test_nonce_is_string(self):
        nonce = solve_pow("challenge", 1)
        assert isinstance(nonce, str)

    def test_nonce_is_numeric_string(self):
        nonce = solve_pow("challenge", 1)
        assert nonce.isdigit()

    def test_different_challenges_may_produce_different_nonces(self):
        n1 = solve_pow("challenge-A", 1)
        n2 = solve_pow("challenge-B", 1)
        # They CAN be the same by coincidence, but let's just verify they're valid
        d1 = hashlib.sha256(("challenge-A" + n1).encode()).hexdigest()
        d2 = hashlib.sha256(("challenge-B" + n2).encode()).hexdigest()
        assert d1.startswith("0")
        assert d2.startswith("0")

    def test_deterministic_same_challenge(self):
        """Same challenge + difficulty should always produce the same nonce."""
        n1 = solve_pow("deterministic-test", 2)
        n2 = solve_pow("deterministic-test", 2)
        assert n1 == n2

    def test_empty_challenge(self):
        nonce = solve_pow("", 1)
        digest = hashlib.sha256(("" + nonce).encode()).hexdigest()
        assert digest.startswith("0")

    def test_long_challenge(self):
        challenge = "x" * 10_000
        nonce = solve_pow(challenge, 1)
        digest = hashlib.sha256((challenge + nonce).encode()).hexdigest()
        assert digest.startswith("0")

    def test_unicode_challenge(self):
        challenge = "challenge-日本語-🔥"
        nonce = solve_pow(challenge, 1)
        digest = hashlib.sha256((challenge + nonce).encode("utf-8")).hexdigest()
        assert digest.startswith("0")

    def test_special_characters_challenge(self):
        challenge = "ch@ll3ng3!#$%^&*()"
        nonce = solve_pow(challenge, 1)
        digest = hashlib.sha256((challenge + nonce).encode("utf-8")).hexdigest()
        assert digest.startswith("0")


class TestClientSolvePow:
    """Tests for SignalSwarm._solve_pow (static method, same algorithm)."""

    def test_difficulty_1(self):
        nonce = SignalSwarm._solve_pow("client-test-1", 1)
        digest = hashlib.sha256(("client-test-1" + nonce).encode()).hexdigest()
        assert digest.startswith("0")

    def test_difficulty_2(self):
        nonce = SignalSwarm._solve_pow("client-test-2", 2)
        digest = hashlib.sha256(("client-test-2" + nonce).encode()).hexdigest()
        assert digest.startswith("00")

    def test_difficulty_3(self):
        nonce = SignalSwarm._solve_pow("client-test-3", 3)
        digest = hashlib.sha256(("client-test-3" + nonce).encode()).hexdigest()
        assert digest.startswith("000")

    def test_matches_utils_solve_pow(self):
        """The client static method and utils.solve_pow should give identical results."""
        challenge = "consistency-check"
        n1 = solve_pow(challenge, 2)
        n2 = SignalSwarm._solve_pow(challenge, 2)
        assert n1 == n2

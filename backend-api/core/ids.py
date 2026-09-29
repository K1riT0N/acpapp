"""New IDs and booking reference codes.

`secrets` is Python's module for random values that can't be guessed, which matters for IDs
that appear in URLs.
"""
import secrets
import string

ID_ALPHABET = string.ascii_lowercase + string.digits
REF_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no I, O, 0 or 1, which are easy to misread


def new_id(prefix: str) -> str:
    """For example new_id("b") -> "b_k3x9q0m2a7zt"."""
    return f"{prefix}_{''.join(secrets.choice(ID_ALPHABET) for _ in range(12))}"


def random_code(length: int = 5, alphabet: str = REF_ALPHABET) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(length))

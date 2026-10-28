"""Explicit reference-tokenizer setup; no model calls or user-data cache."""

from __future__ import annotations

from collections.abc import Callable

REFERENCE_ENCODING = "cl100k_base"
TokenCounter = Callable[[str], int]


class TokenizerUnavailableError(RuntimeError):
    """Reference encoding could not be initialized; use counter=None to continue."""


def create_token_counter() -> TokenCounter:
    """Initialize vocabulary (may download public data), then count ordinary text."""
    try:
        import requests
        import tiktoken
    except ImportError:
        raise TokenizerUnavailableError(
            "Install project dependencies, then warm cl100k_base "
            "before comparing tokens."
        ) from None
    try:
        encoding = tiktoken.get_encoding(REFERENCE_ENCODING)
    except (OSError, ValueError, requests.exceptions.RequestException):
        raise TokenizerUnavailableError(
            "Cannot initialize cl100k_base. Check network/cache access and run the "
            "README tokenizer warm-up command; comparison can continue without tokens."
        ) from None

    def count(text: str) -> int:
        return len(encoding.encode_ordinary(text))

    return count

"""Domain exceptions: one base (`AppError`) and specific subclasses callers
catch when they want to react to a particular failure mode."""

from __future__ import annotations


class AppError(Exception):
    """Base application error."""


class LLMUnavailableError(AppError):
    """Raised when OpenRouter / the chosen LLM cannot be reached or is unconfigured."""

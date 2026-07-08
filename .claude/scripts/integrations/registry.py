"""
Integration registry.

Detects which platform integrations are configured, by checking for their
required environment variable(s) — without importing the integration
module itself (so checking configuration never requires network access or
optional dependencies to be installed).

The CLI (query.py) and future heartbeat code use this to know what's
available without hardcoding which integrations exist.
"""

from __future__ import annotations

import config

# Maps integration name -> tuple of required env var names.
# An integration is "configured" only if ALL of its required vars are set
# (non-empty). Add new integrations here as they're built (Outlook/GCal/
# Affinity are connector- or export-based, not env-var based, so they are
# intentionally not listed here).
_REQUIRED_ENV_VARS: dict[str, tuple[str, ...]] = {
    "notion": ("NOTION_API_KEY",),
    "nimble": ("NIMBLE_API_KEY",),
}


def is_configured(name: str) -> bool:
    """Return True if the named integration has all required env vars set.

    Returns False (never raises) for an unknown integration name.
    """
    required = _REQUIRED_ENV_VARS.get(name)
    if required is None:
        return False
    return all(bool(getattr(config, var, "")) for var in required)


def list_configured() -> list[str]:
    """Return the names of every integration that is currently configured."""
    return [name for name in _REQUIRED_ENV_VARS if is_configured(name)]


def required_env_vars(name: str) -> tuple[str, ...]:
    """Return the required env var names for an integration (empty tuple if unknown)."""
    return _REQUIRED_ENV_VARS.get(name, ())


def missing_env_vars(name: str) -> tuple[str, ...]:
    """Return which of an integration's required env vars are NOT set."""
    return tuple(
        var for var in _REQUIRED_ENV_VARS.get(name, ()) if not getattr(config, var, "")
    )

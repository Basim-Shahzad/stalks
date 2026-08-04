"""
Legacy compatibility shim.

The production auth lives in features/auth (async). This module re-exports
the async feature-based dependencies so that endpoints still importing
`from dependencies.auth_deps import get_current_active_user` keep resolving
while they are migrated onto the feature layer.
"""

from features.auth.dependencies import get_current_active_user, get_current_user

__all__ = ["get_current_user", "get_current_active_user"]

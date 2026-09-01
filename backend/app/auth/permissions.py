"""Role-Based Access Control (RBAC) & Permissions for PayFilter."""

from __future__ import annotations

from enum import Enum
from typing import Set
from fastapi import HTTPException, status

from backend.app.db.models import AuthenticatedUser


class UserRoleEnum(str, Enum):
    """Supported user roles in PayFilter."""

    ADMIN = "admin"
    ANALYST = "analyst"


ROLE_HIERARCHY: dict[str, Set[str]] = {
    UserRoleEnum.ADMIN.value: {UserRoleEnum.ADMIN.value, UserRoleEnum.ANALYST.value},
    UserRoleEnum.ANALYST.value: {UserRoleEnum.ANALYST.value},
}


def check_role_permission(user: AuthenticatedUser, required_role: str) -> None:
    """Verifies that the authenticated user possesses the required role permission.

    Raises:
        HTTPException: 403 Forbidden if user role is insufficient.
    """
    user_permissions = ROLE_HIERARCHY.get(user.role, set())
    if required_role not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation requires '{required_role}' role privileges. Current role: '{user.role}'.",
        )

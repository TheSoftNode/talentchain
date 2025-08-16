"""
API Dependencies

This module provides FastAPI dependencies for authentication,
authorization, and other common API requirements.
"""

from fastapi import Depends, Request, HTTPException, status
from typing import Optional

from app.utils.auth import (
    get_current_user,
    require_auth,
    require_permission,
    AuthContext
)

async def get_auth_context(request: Request) -> Optional[AuthContext]:
    """Get authentication context if available."""
    return await get_current_user(request)

async def get_authenticated_user(request: Request) -> AuthContext:
    """Require authentication for protected endpoints."""
    return await require_auth(request)

async def get_governance_user(request: Request) -> AuthContext:
    """Require governance permissions."""
    return await require_permission(request, "governance")

async def get_oracle_user(request: Request) -> AuthContext:
    """Require oracle permissions."""
    return await require_permission(request, "oracle")

async def get_skill_user(request: Request) -> AuthContext:
    """Require skill management permissions."""
    return await require_permission(request, "skill")

async def get_pool_user(request: Request) -> AuthContext:
    """Require talent pool permissions."""
    return await require_permission(request, "pool")

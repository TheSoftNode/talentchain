"""
Talent Pool API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
import logging

from app.models.user_schemas import User
from app.utils.auth import get_current_user
from app.services.pool import get_pool_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pools", tags=["talent-pools"])


@router.get("/{pool_id}/metrics")
async def get_pool_metrics(
    pool_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get pool metrics."""
    try:
        pool_service = get_pool_service()
        result = await pool_service.get_pool_metrics(pool_id=pool_id)
        return result
    except Exception as e:
        logger.error(f"Error getting pool metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/global")
async def get_global_stats(
    current_user: User = Depends(get_current_user)
):
    """Get global talent pool statistics."""
    try:
        pool_service = get_pool_service()
        result = await pool_service.get_global_stats()
        return result
    except Exception as e:
        logger.error(f"Error getting global stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/active-count")
async def get_active_pools_count(
    current_user: User = Depends(get_current_user)
):
    """Get active pools count."""
    try:
        pool_service = get_pool_service()
        result = await pool_service.get_active_pools_count()
        return result
    except Exception as e:
        logger.error(f"Error getting active pools count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/total-count")
async def get_total_pools_count(
    current_user: User = Depends(get_current_user)
):
    """Get total pools count."""
    try:
        pool_service = get_pool_service()
        result = await pool_service.get_total_pools_count()
        return result
    except Exception as e:
        logger.error(f"Error getting total pools count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




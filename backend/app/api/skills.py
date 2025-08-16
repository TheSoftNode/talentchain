"""
Enhanced Skills API Router

This module provides comprehensive API endpoints for managing skill tokens,
including creation, updating, querying, and integration with reputation system.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks

from app.models.skills_schemas import (
    SkillTokenCreateRequest,
    SkillTokenUpdateRequest,
    BatchSkillTokenRequest,
    SkillSearchRequest,
    SkillTokenDetailResponse,
    BatchOperationResponse,
    WorkEvaluationRequest,
    WorkEvaluationResponse,
    EndorseSkillTokenRequest,
    RenewSkillTokenRequest,
    RevokeSkillTokenRequest,
    MarkExpiredTokensRequest
)
from app.models.common_schemas import ErrorResponse
from app.services.skill import get_skill_service
from app.services.reputation import get_reputation_service
from app.utils.hedera import validate_hedera_address
from app.models.user import User, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Contract-Aligned API Endpoints - Perfect 1:1 mapping with SkillToken.sol

@router.post(
    "/mint",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def mint_skill_token(
    request: SkillTokenCreateRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Create a new skill token - matches SkillToken.mintSkillToken() exactly.
    
    Contract function: mintSkillToken(address recipient, string category, string subcategory, 
                                   uint8 level, uint64 expiryDate, string metadata, string tokenURIData)
    """
    try:
        skill_service = get_skill_service()
        
        # Call service with exact contract parameters
        result = await skill_service.mint_skill_token(
            recipient=request.recipient_address,
            category=request.category,
            subcategory=request.subcategory,
            level=request.level,
            expiry_date=request.expiry_date,
            metadata=request.metadata,
            token_uri_data=request.uri
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to mint skill token")
            )
        
        # Add background task for reputation update
        background_tasks.add_task(
            update_reputation_for_skill_creation,
            request.recipient_address,
            request.category,
            request.level
        )
        
        logger.info(f"Minted skill token {result['token_id']} for {request.recipient_address}")
        
        return {
            "transaction_id": result.get("transaction_id"),
            "token_id": result["token_id"],
            "contract_address": result.get("contract_address"),
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error minting skill token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mint skill token"
        )


@router.post(
    "/batch-mint",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def batch_mint_skill_tokens(
    request: BatchSkillTokenRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Batch create skill tokens - matches SkillToken.batchMintSkillTokens() exactly.
    
    Contract function: batchMintSkillTokens(address recipient, string[] categories, string[] subcategories,
                                         uint8[] levels, uint64[] expiryDates, string[] metadataArray, string[] tokenURIs)
    """
    try:
        skill_service = get_skill_service()
        
        # Call service with exact contract parameters
        result = await skill_service.batch_mint_skill_tokens(
            recipient=request.recipient_address,
            categories=request.categories,
            subcategories=request.subcategories,
            levels=request.levels,
            expiry_dates=request.expiry_dates,
            metadata_array=request.metadata_array,
            token_uris=request.token_uris
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to batch mint skill tokens")
            )
        
        # Add background task for reputation updates
        background_tasks.add_task(
            update_reputation_for_batch_creation,
            request.recipient_address,
            len(request.categories),
            len(result.get("token_ids", []))
        )
        
        logger.info(f"Batch minted {len(result.get('token_ids', []))} skill tokens for {request.recipient_address}")
        
        return {
            "transaction_id": result.get("transaction_id"),
            "token_ids": result.get("token_ids", []),
            "contract_address": result.get("contract_address"),
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch minting skill tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch mint skill tokens"
        )


@router.post(
    "/",
    response_model=SkillTokenDetailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_skill_token(
    request: SkillTokenCreateRequest,
    background_tasks: BackgroundTasks
) -> SkillTokenDetailResponse:
    """
    Create a new skill token for a user.
    
    Args:
        request: Skill token creation request
        background_tasks: Background task queue
        
    Returns:
        Detailed skill token information
    """
    try:
        skill_service = get_skill_service()
        
        # Create skill token using enhanced service
        result = await skill_service.create_skill_token(
            recipient_address=request.recipient_address,
            skill_name=request.skill_name,
            skill_category=request.skill_category,
            level=request.level,
            description=request.description or "",
            metadata_uri=request.metadata_uri or ""
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create skill token")
            )
        
        # Add background task for reputation update
        background_tasks.add_task(
            update_reputation_for_skill_creation,
            request.recipient_address,
            request.skill_name,
            request.level
        )
        
        logger.info(f"Created skill token {result['token_id']} for {request.recipient_address}")
        
        return SkillTokenDetailResponse(
            token_id=result["token_id"],
            owner_address=request.recipient_address,
            skill_name=request.skill_name,
            skill_category=request.skill_category,
            level=request.level,
            experience_points=0,
            description=request.description,
            metadata_uri=request.metadata_uri,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating skill token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create skill token"
        )


@router.put(
    "/update-level",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Skill token not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_skill_level(
    token_id: int,
    new_level: int,
    evidence: str = "",
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Update skill level - matches SkillToken.updateSkillLevel() exactly.
    
    Contract function: updateSkillLevel(uint256 tokenId, uint8 newLevel, string evidence)
    """
    try:
        skill_service = get_skill_service()
        
        # Get current token data for comparison
        current_result = await skill_service.get_skill_token(str(token_id))
        if not current_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill token not found"
            )
        
        current_data = current_result["data"]
        
        # Call service with exact contract parameters
        result = await skill_service.update_skill_level(
            token_id=token_id,
            new_level=new_level,
            evidence=evidence
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update skill level")
            )
        
        # Add background task for reputation update
        if background_tasks:
            background_tasks.add_task(
                update_reputation_for_level_change,
                current_data["owner_address"],
                str(token_id),
                current_data["level"],
                new_level
            )
        
        logger.info(f"Updated skill token {token_id} level to {new_level}")
        
        return {
            "transaction_id": result.get("transaction_id"),
            "token_id": token_id,
            "old_level": current_data["level"],
            "new_level": new_level,
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating skill level: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update skill level"
        )


@router.post(
    "/endorse",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Skill token not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def endorse_skill_token(
    token_id: int,
    endorsement_data: str,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Endorse a skill token - matches SkillToken.endorseSkillToken() exactly.
    
    Contract function: endorseSkillToken(uint256 tokenId, string endorsementData)
    """
    try:
        skill_service = get_skill_service()
        
        # Call service with exact contract parameters
        result = await skill_service.endorse_skill_token(
            token_id=token_id,
            endorsement_data=endorsement_data
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to endorse skill token")
            )
        
        logger.info(f"Endorsed skill token {token_id}")
        
        return {
            "transaction_id": result.get("transaction_id"),
            "token_id": token_id,
            "endorsement_data": endorsement_data,
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error endorsing skill token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to endorse skill token"
        )


@router.post(
    "/endorse-with-signature",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Skill token not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def endorse_skill_token_with_signature(
    token_id: int,
    endorsement_data: str,
    deadline: int,
    signature: str,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Endorse skill token with signature - matches SkillToken.endorseSkillTokenWithSignature() exactly.
    
    Contract function: endorseSkillTokenWithSignature(uint256 tokenId, string endorsementData, uint256 deadline, bytes signature)
    """
    try:
        skill_service = get_skill_service()
        
        # Call service with exact contract parameters
        result = await skill_service.endorse_skill_token_with_signature(
            token_id=token_id,
            endorsement_data=endorsement_data,
            deadline=deadline,
            signature=signature
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to endorse skill token with signature")
            )
        
        logger.info(f"Endorsed skill token {token_id} with signature")
        
        return {
            "transaction_id": result.get("transaction_id"),
            "token_id": token_id,
            "endorsement_data": endorsement_data,
            "deadline": deadline,
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error endorsing skill token with signature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to endorse skill token with signature"
        )


@router.put(
    "/renew",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Skill token not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def renew_skill_token(
    token_id: int,
    new_expiry_date: int,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Renew skill token expiry - matches SkillToken.renewSkillToken() exactly.
    
    Contract function: renewSkillToken(uint256 tokenId, uint64 newExpiryDate)
    """
    try:
        skill_service = get_skill_service()
        
        # Call service with exact contract parameters
        result = await skill_service.renew_skill_token(
            token_id=token_id,
            new_expiry_date=new_expiry_date
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to renew skill token")
            )
        
        logger.info(f"Renewed skill token {token_id} expiry to {new_expiry_date}")
        
        return {
            "transaction_id": result.get("transaction_id"),
            "token_id": token_id,
            "new_expiry_date": new_expiry_date,
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renewing skill token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to renew skill token"
        )


@router.put(
    "/revoke",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Skill token not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def revoke_skill_token(
    token_id: int,
    reason: str,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Revoke skill token - matches SkillToken.revokeSkillToken() exactly.
    
    Contract function: revokeSkillToken(uint256 tokenId, string reason)
    """
    try:
        skill_service = get_skill_service()
        
        # Call service with exact contract parameters
        result = await skill_service.revoke_skill_token(
            token_id=token_id,
            reason=reason
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to revoke skill token")
            )
        
        logger.info(f"Revoked skill token {token_id} for reason: {reason}")
        
        return {
            "transaction_id": result.get("transaction_id"),
            "token_id": token_id,
            "reason": reason,
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking skill token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke skill token"
        )


@router.post(
    "/batch",
    response_model=BatchOperationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def batch_create_skill_tokens(
    request: BatchSkillTokenRequest,
    background_tasks: BackgroundTasks
) -> BatchOperationResponse:
    """
    Create multiple skill tokens in a batch operation.
    
    Args:
        request: Batch skill token creation request
        background_tasks: Background task queue
        
    Returns:
        Batch operation results
    """
    try:
        skill_service = get_skill_service()
        
        # Batch create skill tokens
        result = await skill_service.batch_create_skill_tokens(
            recipient_address=request.recipient_address,
            skills=request.skills
        )
        
        # Add background task for reputation updates
        background_tasks.add_task(
            update_reputation_for_batch_creation,
            request.recipient_address,
            len(request.skills),
            result.get("successful", 0)
        )
        
        logger.info(f"Batch created {result.get('successful', 0)} skill tokens for {request.recipient_address}")
        
        return BatchOperationResponse(
            success=result["success"],
            total_requested=len(request.skills),
            successful=result.get("successful", 0),
            failed=result.get("failed", 0),
            results=result.get("results", []),
            errors=result.get("errors", [])
        )
    
    except Exception as e:
        logger.error(f"Error in batch skill token creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch create skill tokens"
        )


@router.get(
    "/{token_id}",
    response_model=SkillTokenDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Skill token not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_skill_token(
    token_id: str = Path(..., description="Skill token ID")
) -> SkillTokenDetailResponse:
    """
    Get detailed information about a specific skill token.
    
    Args:
        token_id: Skill token ID
        
    Returns:
        Detailed skill token information
    """
    try:
        skill_service = get_skill_service()
        
        # Get skill token details
        result = await skill_service.get_skill_token(token_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill token not found"
            )
        
        token_data = result["data"]
        
        return SkillTokenDetailResponse(
            token_id=token_id,
            owner_address=token_data["owner_address"],
            skill_name=token_data["skill_name"],
            skill_category=token_data["skill_category"],
            level=token_data["level"],
            experience_points=token_data.get("experience_points", 0),
            description=token_data.get("description"),
            metadata_uri=token_data.get("metadata_uri"),
            is_active=token_data.get("is_active", True),
            created_at=datetime.fromisoformat(token_data.get("created_at", datetime.now(timezone.utc).isoformat())),
            last_updated=datetime.fromisoformat(token_data.get("last_updated", datetime.now(timezone.utc).isoformat()))
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill token {token_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skill token"
        )


@router.put(
    "/{token_id}",
    response_model=SkillTokenDetailResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Skill token not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_skill_token(
    token_id: str = Path(..., description="Skill token ID"),
    request: SkillTokenUpdateRequest = ...,
    background_tasks: BackgroundTasks = ...
) -> SkillTokenDetailResponse:
    """
    Update a skill token's level or experience points.
    
    Args:
        token_id: Skill token ID
        request: Update request
        background_tasks: Background task queue
        
    Returns:
        Updated skill token information
    """
    try:
        skill_service = get_skill_service()
        
        # Get current token data
        current_result = await skill_service.get_skill_token(token_id)
        if not current_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill token not found"
            )
        
        current_data = current_result["data"]
        update_result = None
        
        # Update level if requested
        if request.new_level is not None:
            update_result = await skill_service.update_skill_level(
                token_id=token_id,
                new_level=request.new_level,
                evidence_uri=request.evidence_uri or ""
            )
            
            # Add background task for reputation update
            background_tasks.add_task(
                update_reputation_for_level_change,
                current_data["owner_address"],
                token_id,
                current_data["level"],
                request.new_level
            )
        
        # Add experience points if requested
        if request.experience_points is not None:
            exp_result = await skill_service.add_skill_experience(
                token_id=token_id,
                experience_points=request.experience_points
            )
            
            if update_result is None:
                update_result = exp_result
        
        if update_result and not update_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=update_result.get("error", "Failed to update skill token")
            )
        
        # Get updated token data
        updated_result = await skill_service.get_skill_token(token_id)
        updated_data = updated_result["data"]
        
        logger.info(f"Updated skill token {token_id}")
        
        return SkillTokenDetailResponse(
            token_id=token_id,
            owner_address=updated_data["owner_address"],
            skill_name=updated_data["skill_name"],
            skill_category=updated_data["skill_category"],
            level=updated_data["level"],
            experience_points=updated_data.get("experience_points", 0),
            description=updated_data.get("description"),
            metadata_uri=updated_data.get("metadata_uri"),
            is_active=updated_data.get("is_active", True),
            created_at=datetime.fromisoformat(updated_data.get("created_at", datetime.now(timezone.utc).isoformat())),
            last_updated=datetime.now(timezone.utc)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating skill token {token_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update skill token"
        )


@router.get(
    "/user/{user_address}",
    response_model=List[SkillTokenDetailResponse],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_user_skills(
    user_address: str = Path(..., description="User's Hedera account address"),
    category: Optional[str] = Query(None, description="Filter by skill category"),
    min_level: Optional[int] = Query(None, ge=1, le=10, description="Minimum skill level"),
    active_only: bool = Query(True, description="Only return active skills")
) -> List[SkillTokenDetailResponse]:
    """
    Get all skill tokens owned by a user.
    
    Args:
        user_address: User's Hedera account address
        category: Optional category filter
        min_level: Optional minimum level filter
        active_only: Whether to return only active skills
        
    Returns:
        List of user's skill tokens
    """
    try:
        if not validate_hedera_address(user_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Hedera address format"
            )
        
        skill_service = get_skill_service()
        
        # Get user's skills
        result = await skill_service.get_user_skills(user_address)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user skills"
            )
        
        skills_data = result["skills"]
        
        # Apply filters
        filtered_skills = []
        for skill in skills_data:
            # Category filter
            if category and skill.get("skill_category") != category:
                continue
            
            # Level filter
            if min_level and skill.get("level", 0) < min_level:
                continue
            
            # Active filter
            if active_only and not skill.get("is_active", True):
                continue
            
            filtered_skills.append(SkillTokenDetailResponse(
                token_id=skill["token_id"],
                owner_address=user_address,
                skill_name=skill["skill_name"],
                skill_category=skill["skill_category"],
                level=skill["level"],
                experience_points=skill.get("experience_points", 0),
                description=skill.get("description"),
                metadata_uri=skill.get("metadata_uri"),
                is_active=skill.get("is_active", True),
                created_at=datetime.fromisoformat(skill.get("created_at", datetime.now(timezone.utc).isoformat())),
                last_updated=datetime.fromisoformat(skill.get("last_updated", datetime.now(timezone.utc).isoformat()))
            ))
        
        logger.info(f"Retrieved {len(filtered_skills)} skills for user {user_address}")
        
        return filtered_skills
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user skills"
        )


@router.get(
    "/search",
    response_model=List[SkillTokenDetailResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def search_skills(
    skill_name: Optional[str] = Query(None, description="Skill name to search"),
    skill_category: Optional[str] = Query(None, description="Skill category filter"),
    min_level: Optional[int] = Query(None, ge=1, le=10, description="Minimum skill level"),
    max_level: Optional[int] = Query(None, ge=1, le=10, description="Maximum skill level"),
    owner_address: Optional[str] = Query(None, description="Owner address filter"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return")
) -> List[SkillTokenDetailResponse]:
    """
    Search for skill tokens based on various criteria.
    
    Args:
        skill_name: Skill name to search (partial match)
        skill_category: Skill category filter
        min_level: Minimum skill level
        max_level: Maximum skill level
        owner_address: Owner address filter
        limit: Maximum results to return
        
    Returns:
        List of matching skill tokens
    """
    try:
        skill_service = get_skill_service()
        
        # Build search criteria
        search_criteria = {}
        if skill_name:
            search_criteria["skill_name"] = skill_name
        if skill_category:
            search_criteria["skill_category"] = skill_category
        if min_level:
            search_criteria["min_level"] = min_level
        if max_level:
            search_criteria["max_level"] = max_level
        if owner_address:
            if not validate_hedera_address(owner_address):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid owner address format"
                )
            search_criteria["owner_address"] = owner_address
        
        # Search for skills
        result = await skill_service.search_skills(search_criteria, limit=limit)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search skills"
            )
        
        skills_data = result["skills"]
        
        # Convert to response models
        skills = []
        for skill in skills_data[:limit]:
            skills.append(SkillTokenDetailResponse(
                token_id=skill["token_id"],
                owner_address=skill["owner_address"],
                skill_name=skill["skill_name"],
                skill_category=skill["skill_category"],
                level=skill["level"],
                experience_points=skill.get("experience_points", 0),
                description=skill.get("description"),
                metadata_uri=skill.get("metadata_uri"),
                is_active=skill.get("is_active", True),
                created_at=datetime.fromisoformat(skill.get("created_at", datetime.now(timezone.utc).isoformat())),
                last_updated=datetime.fromisoformat(skill.get("last_updated", datetime.now(timezone.utc).isoformat()))
            ))
        
        logger.info(f"Found {len(skills)} skills matching search criteria")
        
        return skills
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search skills"
        )


@router.get(
    "/categories",
    response_model=Dict[str, Any],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_skill_categories() -> Dict[str, Any]:
    """
    Get available skill categories and their statistics.
    
    Returns:
        List of skill categories with counts and descriptions
    """
    try:
        skill_service = get_skill_service()
        
        # Get categories from service
        result = await skill_service.get_skill_categories()
        
        if not result["success"]:
            return {
                "categories": [
                    {"id": "frontend", "name": "Frontend Development", "count": 0},
                    {"id": "backend", "name": "Backend Development", "count": 0},
                    {"id": "blockchain", "name": "Blockchain Development", "count": 0},
                    {"id": "design", "name": "UI/UX Design", "count": 0},
                    {"id": "data_science", "name": "Data Science", "count": 0},
                    {"id": "devops", "name": "DevOps", "count": 0},
                    {"id": "mobile", "name": "Mobile Development", "count": 0},
                    {"id": "other", "name": "Other", "count": 0}
                ]
            }
        
        return result["categories"]
    
    except Exception as e:
        logger.error(f"Error getting skill categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skill categories"
        )


# Background Task Functions

async def update_reputation_for_skill_creation(user_address: str, skill_name: str, level: int):
    """Background task to update reputation when skill is created."""
    try:
        reputation_service = get_reputation_service()
        
        from app.services.reputation import ReputationEventType
        
        await reputation_service.update_reputation(
            user_address=user_address,
            event_type=ReputationEventType.SKILL_VALIDATION,
            impact_score=level * 2.0,  # Higher level = more impact
            context={
                "skill_name": skill_name,
                "level": level,
                "event": "skill_creation"
            }
        )
        
        logger.info(f"Updated reputation for skill creation: {user_address}")
    
    except Exception as e:
        logger.error(f"Error updating reputation for skill creation: {str(e)}")


async def update_reputation_for_batch_creation(user_address: str, total_requested: int, successful: int):
    """Background task to update reputation for batch skill creation."""
    try:
        reputation_service = get_reputation_service()
        
        from app.services.reputation import ReputationEventType
        
        # Calculate impact based on success rate
        success_rate = successful / total_requested if total_requested > 0 else 0
        impact_score = min(20.0, successful * 2.0 * success_rate)
        
        await reputation_service.update_reputation(
            user_address=user_address,
            event_type=ReputationEventType.PLATFORM_CONTRIBUTION,
            impact_score=impact_score,
            context={
                "total_requested": total_requested,
                "successful": successful,
                "success_rate": success_rate,
                "event": "batch_skill_creation"
            }
        )
        
        logger.info(f"Updated reputation for batch skill creation: {user_address}")
    
    except Exception as e:
        logger.error(f"Error updating reputation for batch creation: {str(e)}")


async def update_reputation_for_level_change(user_address: str, token_id: str, old_level: int, new_level: int):
    """Background task to update reputation when skill level changes."""
    try:
        reputation_service = get_reputation_service()
        
        from app.services.reputation import ReputationEventType
        
        level_change = new_level - old_level
        impact_score = level_change * 3.0  # Can be positive or negative
        
        await reputation_service.update_reputation(
            user_address=user_address,
            event_type=ReputationEventType.SKILL_VALIDATION,
            impact_score=impact_score,
            context={
                "token_id": token_id,
                "old_level": old_level,
                "new_level": new_level,
                "level_change": level_change,
                "event": "skill_level_update"
            }
        )
        
        logger.info(f"Updated reputation for level change: {user_address}")
    
    except Exception as e:
        logger.error(f"Error updating reputation for level change: {str(e)}")

# End of Skills API

@router.post("/endorse")
async def endorse_skill_token(
    request: EndorseSkillTokenRequest,
    current_user: User = Depends(get_current_user)
):
    """Endorse a skill token."""
    try:
        skill_service = get_skill_service()
        result = await skill_service.endorse_skill_token(
            token_id=request.token_id,
            endorsement_data=request.endorsement_data
        )
        return result
    except Exception as e:
        logger.error(f"Error endorsing skill token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/renew")
async def renew_skill_token(
    request: RenewSkillTokenRequest,
    current_user: User = Depends(get_current_user)
):
    """Renew a skill token."""
    try:
        skill_service = get_skill_service()
        result = await skill_service.renew_skill_token(
            token_id=request.token_id,
            new_expiry_date=request.new_expiry_date
        )
        return result
    except Exception as e:
        logger.error(f"Error renewing skill token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revoke")
async def revoke_skill_token(
    request: RevokeSkillTokenRequest,
    current_user: User = Depends(get_current_user)
):
    """Revoke a skill token."""
    try:
        skill_service = get_skill_service()
        result = await skill_service.revoke_skill_token(
            token_id=request.token_id,
            reason=request.reason
        )
        return result
    except Exception as e:
        logger.error(f"Error revoking skill token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{token_id}/endorsements")
async def get_skill_endorsements(
    token_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get endorsements for a skill token."""
    try:
        skill_service = get_skill_service()
        result = await skill_service.get_skill_endorsements(token_id=token_id)
        return result
    except Exception as e:
        logger.error(f"Error getting skill endorsements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-expired")
async def mark_expired_tokens(
    request: MarkExpiredTokensRequest,
    current_user: User = Depends(get_current_user)
):
    """Mark skill tokens as expired."""
    try:
        skill_service = get_skill_service()
        result = await skill_service.mark_expired_tokens(
            token_ids=request.token_ids
        )
        return result
    except Exception as e:
        logger.error(f"Error marking tokens as expired: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category}")
async def get_tokens_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get skill tokens for a specific category."""
    try:
        skill_service = get_skill_service()
        result = await skill_service.get_tokens_by_category(
            category=category,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error getting tokens by category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category}/total")
async def get_total_skills_by_category(
    category: str,
    current_user: User = Depends(get_current_user)
):
    """Get total number of skills in a category."""
    try:
        skill_service = get_skill_service()
        result = await skill_service.get_total_skills_by_category()
        return result
    except Exception as e:
        logger.error(f"Error getting total skills by category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

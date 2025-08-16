"""
Enhanced Reputation API Endpoints

This module provides comprehensive REST API endpoints for reputation management,
oracle registration, work evaluation, consensus mechanisms, and challenge systems.

Perfect 1:1 mapping with ReputationOracle.sol smart contract functions.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Body, status
from fastapi.responses import JSONResponse

from app.models.reputation_schemas import (
    RegisterOracleRequest,
    WorkEvaluationRequest,
    ChallengeEvaluationRequest,
    UpdateReputationRequest,
    OracleResponse,
    EvaluationResponse,
    ChallengeResponse,
    ReputationResponse,
    ContractRegisterOracleRequest,
    ContractSubmitEvaluationRequest
)
from app.models.common_schemas import ErrorResponse, BatchResponse
from app.services.reputation import get_reputation_service, ReputationService, ReputationEventType, ReputationCategory
from app.utils.hedera import validate_hedera_address
from app.models.user_schemas import User
from app.utils.auth import get_current_user
from app.models.reputation_schemas import UpdateOracleStatusRequest

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["reputation"])

# ============ CONTRACT-ALIGNED REPUTATION ENDPOINTS ============

@router.post(
    "/register-oracle",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def register_oracle(
    request: ContractRegisterOracleRequest
) -> Dict[str, Any]:
    """
    Register a new reputation oracle - matches ReputationOracle.registerOracle() exactly.
    
    Contract function: registerOracle(string name, string[] specializations)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.register_oracle(
            name=request.name,
            specializations=request.specializations
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to register oracle")
            )
        
        logger.info(f"Registered oracle: {request.name}")
        return result
        
    except Exception as e:
        logger.error(f"Error registering oracle: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post(
    "/submit-evaluation",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def submit_evaluation(
    request: ContractSubmitEvaluationRequest
) -> Dict[str, Any]:
    """
    Submit work evaluation - matches ReputationOracle.submitWorkEvaluation() exactly.
    
    Contract function: submitWorkEvaluation(address user, uint256[] skillTokenIds,
                                          string workDescription, string workContent,
                                          uint256 overallScore, uint256[] skillScores,
                                          string feedback, string ipfsHash)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.submit_work_evaluation(
            user=request.user,
            skill_token_ids=request.skill_token_ids,
            work_description=request.work_description,
            work_content=request.work_content,
            overall_score=request.overall_score,
            skill_scores=request.skill_scores,
            feedback=request.feedback,
            ipfs_hash=request.ipfs_hash
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to submit evaluation")
            )
        
        logger.info(f"Evaluation submitted for user {request.user}")
        return result
        
    except Exception as e:
        logger.error(f"Error submitting evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post(
    "/update-reputation-score",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_reputation_score(
    user_address: str,
    new_score: int,
    skill_categories: List[int],
    evaluation_id: int
) -> Dict[str, Any]:
    """
    Update reputation score - matches ReputationOracle.updateReputationScore() exactly.
    
    Contract function: updateReputationScore(address user, uint256 newScore, 
                                           uint8[] skillCategories, uint256 evaluationId)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.update_reputation_score(
            user_address=user_address,
            new_score=new_score,
            skill_categories=skill_categories,
            evaluation_id=evaluation_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update reputation score")
            )
        
        logger.info(f"Updated reputation score for {user_address}")
        return result
        
    except Exception as e:
        logger.error(f"Error updating reputation score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post(
    "/challenge-evaluation",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def challenge_evaluation(
    evaluation_id: int,
    challenger: str,
    challenge_reason: str,
    stake_amount: int
) -> Dict[str, Any]:
    """
    Challenge an evaluation - matches ReputationOracle.challengeEvaluation() exactly.
    
    Contract function: challengeEvaluation(uint256 evaluationId, address challenger, 
                                         string challengeReason, uint256 stakeAmount)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.challenge_evaluation(
            evaluation_id=evaluation_id,
            challenger=challenger,
            challenge_reason=challenge_reason,
            stake_amount=stake_amount
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to challenge evaluation")
            )
        
        logger.info(f"Evaluation {evaluation_id} challenged by {challenger}")
        return result
        
    except Exception as e:
        logger.error(f"Error challenging evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post(
    "/resolve-challenge",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def resolve_challenge(
    challenge_id: int,
    resolution: bool,
    resolution_reason: str
) -> Dict[str, Any]:
    """
    Resolve a challenge - matches ReputationOracle.resolveChallenge() exactly.
    
    Contract function: resolveChallenge(uint256 challengeId, bool resolution, 
                                      string resolutionReason)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.resolve_challenge(
            challenge_id=challenge_id,
            resolution=resolution,
            resolution_reason=resolution_reason
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to resolve challenge")
            )
        
        logger.info(f"Challenge {challenge_id} resolved")
        return result
        
    except Exception as e:
        logger.error(f"Error resolving challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get(
    "/is-active-oracle/{oracle_address}",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Oracle status"},
        404: {"model": ErrorResponse, "description": "Oracle not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def is_active_oracle(
    oracle_address: str
) -> Dict[str, Any]:
    """
    Check if oracle is active - matches ReputationOracle.isActiveOracle() exactly.
    
    Contract function: isActiveOracle(address oracle) returns (bool)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.is_active_oracle(
            oracle_address=oracle_address
        )
        
        logger.info(f"Checked oracle status for {oracle_address}")
        return result
        
    except Exception as e:
        logger.error(f"Error checking oracle status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post(
    "/update-oracle-status",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_oracle_status(
    oracle_address: str,
    is_active: bool,
    reason: str = ""
) -> Dict[str, Any]:
    """
    Update oracle status - matches ReputationOracle.updateOracleStatus() exactly.
    
    Contract function: updateOracleStatus(address oracle, bool isActive, string reason)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.update_oracle_status(
            oracle_address=oracle_address,
            is_active=is_active,
            reason=reason
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update oracle status")
            )
        
        logger.info(f"Updated oracle status for {oracle_address}")
        return result
        
    except Exception as e:
        logger.error(f"Error updating oracle status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post(
    "/slash-oracle",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def slash_oracle(
    oracle_address: str,
    slash_amount: int,
    slash_reason: str
) -> Dict[str, Any]:
    """
    Slash oracle stake - matches ReputationOracle.slashOracle() exactly.
    
    Contract function: slashOracle(address oracle, uint256 slashAmount, string slashReason)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.slash_oracle(
            oracle_address=oracle_address,
            slash_amount=slash_amount,
            slash_reason=slash_reason
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to slash oracle")
            )
        
        logger.info(f"Slashed oracle {oracle_address}")
        return result
        
    except Exception as e:
        logger.error(f"Error slashing oracle: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post(
    "/withdraw-oracle-stake",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def withdraw_oracle_stake(
    oracle_address: str,
    withdrawal_amount: int
) -> Dict[str, Any]:
    """
    Withdraw oracle stake - matches ReputationOracle.withdrawOracleStake() exactly.
    
    Contract function: withdrawOracleStake(address oracle, uint256 withdrawalAmount)
    """
    try:
        reputation_service = get_reputation_service()
        
        result = await reputation_service.withdraw_oracle_stake(
            oracle_address=oracle_address,
            withdrawal_amount=withdrawal_amount
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to withdraw oracle stake")
            )
        
        logger.info(f"Withdrew stake for oracle {oracle_address}")
        return result
        
    except Exception as e:
        logger.error(f"Error withdrawing oracle stake: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ============ LEGACY ORACLE MANAGEMENT ENDPOINTS ============

@router.post("/oracles/register", response_model=Dict[str, Any])
async def register_oracle(
    request: RegisterOracleRequest,
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Register a new reputation oracle.
    
    Allows qualified individuals to register as oracles for evaluating work
    and providing reputation scores. Requires stake deposit.
    """
    try:
        result = await reputation_service.register_oracle(
            oracle_address=request.oracle_address,
            name=request.name,
            specializations=request.specializations,
            stake_amount=request.stake_amount
        )
        
        logger.info(f"Oracle registered: {request.oracle_address}")
        return result
    
    except ValueError as e:
        logger.warning(f"Validation error registering oracle: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering oracle: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register oracle")

@router.get("/oracles", response_model=List[Dict[str, Any]])
async def get_active_oracles(
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> List[Dict[str, Any]]:
    """
    Get list of active reputation oracles.
    
    Returns all active oracles with their specializations and statistics.
    """
    try:
        oracles = await reputation_service.get_active_oracles()
        
        # Filter by specialization if provided
        if specialization:
            oracles = [
                oracle for oracle in oracles
                if specialization in oracle.get("specializations", [])
            ]
        
        logger.info(f"Retrieved {len(oracles)} active oracles")
        return oracles
    
    except Exception as e:
        logger.error(f"Error retrieving oracles: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve oracles")

@router.get("/oracles/{oracle_address}", response_model=Dict[str, Any])
async def get_oracle_info(
    oracle_address: str,
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific oracle.
    
    Returns oracle profile, statistics, and performance metrics.
    """
    try:
        if not validate_hedera_address(oracle_address):
            raise HTTPException(status_code=400, detail="Invalid oracle address format")
        
        oracle_info = await reputation_service._get_oracle_info(oracle_address)
        
        if not oracle_info:
            raise HTTPException(status_code=404, detail="Oracle not found")
        
        logger.info(f"Retrieved oracle info for {oracle_address}")
        return oracle_info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving oracle info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve oracle information")

# ============ WORK EVALUATION ENDPOINTS ============

@router.post("/evaluations", response_model=Dict[str, Any])
async def submit_work_evaluation(
    request: WorkEvaluationRequest,
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Submit a work evaluation as an oracle.
    
    Allows registered oracles to evaluate user work and provide scores
    that contribute to reputation calculations.
    """
    try:
        result = await reputation_service.submit_work_evaluation(
            oracle_address=request.oracle_address,
            user_address=request.user_address,
            skill_token_ids=request.skill_token_ids,
            work_description=request.work_description,
            artifacts=request.artifacts,
            overall_score=request.overall_score,
            skill_scores=request.skill_scores,
            feedback=request.feedback,
            ipfs_hash=request.ipfs_hash
        )
        
        logger.info(f"Work evaluation submitted: {result['evaluation_id']}")
        return result
    
    except ValueError as e:
        logger.warning(f"Validation error submitting evaluation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting work evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit work evaluation")

@router.post("/evaluations/batch", response_model=Dict[str, Any])
async def batch_submit_evaluations(
    evaluations: List[WorkEvaluationRequest],
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Submit multiple work evaluations in batch.
    
    Allows oracles to submit multiple evaluations efficiently.
    """
    try:
        if len(evaluations) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 evaluations per batch")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for evaluation in evaluations:
            try:
                result = await reputation_service.submit_work_evaluation(
                    oracle_address=evaluation.oracle_address,
                    user_address=evaluation.user_address,
                    skill_token_ids=evaluation.skill_token_ids,
                    work_description=evaluation.work_description,
                    artifacts=evaluation.artifacts,
                    overall_score=evaluation.overall_score,
                    skill_scores=evaluation.skill_scores,
                    feedback=evaluation.feedback,
                    ipfs_hash=evaluation.ipfs_hash
                )
                results.append(result)
                successful_count += 1
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "evaluation_data": evaluation.dict()
                })
                failed_count += 1
        
        logger.info(f"Batch evaluation completed: {successful_count} successful, {failed_count} failed")
        
        return {
            "success": failed_count == 0,
            "total_requested": len(evaluations),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch evaluation submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process batch evaluations")

@router.get("/evaluations/{evaluation_id}", response_model=Dict[str, Any])
async def get_evaluation(
    evaluation_id: str,
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Get detailed information about a work evaluation.
    
    Returns complete evaluation data including scores and feedback.
    """
    try:
        evaluation = await reputation_service._get_evaluation_details(evaluation_id)
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        logger.info(f"Retrieved evaluation {evaluation_id}")
        return evaluation
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve evaluation")

# ============ CHALLENGE SYSTEM ENDPOINTS ============

@router.post("/evaluations/{evaluation_id}/challenge", response_model=Dict[str, Any])
async def challenge_evaluation(
    evaluation_id: str,
    request: ChallengeEvaluationRequest,
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Challenge a work evaluation.
    
    Allows users to challenge evaluations they believe are unfair or inaccurate.
    Requires stake deposit which is forfeited if challenge is unsuccessful.
    """
    try:
        result = await reputation_service.challenge_evaluation(
            challenger_address=request.challenger_address,
            evaluation_id=evaluation_id,
            reason=request.reason,
            evidence=request.evidence,
            stake_amount=request.stake_amount
        )
        
        logger.info(f"Evaluation challenge submitted: {result['challenge_id']}")
        return result
    
    except ValueError as e:
        logger.warning(f"Validation error challenging evaluation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error challenging evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to challenge evaluation")

@router.post("/challenges/{challenge_id}/resolve")
async def resolve_challenge(
    challenge_id: str,
    upheld: bool = Body(..., description="Whether to uphold the original evaluation"),
    resolution: str = Body(..., description="Resolution explanation"),
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Resolve an evaluation challenge.
    
    Allows authorized resolvers to decide on challenges and distribute stakes.
    """
    try:
        # This would implement challenge resolution logic
        # For now, return a mock response
        
        return {
            "success": True,
            "challenge_id": challenge_id,
            "upheld": upheld,
            "resolution": resolution,
            "resolved_at": datetime.now().isoformat(),
            "stake_distribution": {
                "challenger_refund": 10.0 if upheld else 0.0,
                "oracle_penalty": 5.0 if upheld else 0.0
            }
        }
    
    except Exception as e:
        logger.error(f"Error resolving challenge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resolve challenge")

# ============ REPUTATION SCORE ENDPOINTS ============

@router.get("/users/{user_address}", response_model=Dict[str, Any])
async def get_user_reputation(
    user_address: str,
    category: Optional[str] = Query(None, description="Specific category to retrieve"),
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Get comprehensive reputation information for a user.
    
    Returns overall reputation score and category breakdowns.
    """
    try:
        if not validate_hedera_address(user_address):
            raise HTTPException(status_code=400, detail="Invalid user address format")
        
        if category:
            # Get specific category score
            try:
                category_enum = ReputationCategory(category)
                reputation_data = await reputation_service.calculate_reputation_score(
                    user_address, category_enum
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category")
        else:
            # Get overall reputation
            reputation_data = await reputation_service.calculate_reputation_score(user_address)
        
        logger.info(f"Retrieved reputation for {user_address}")
        return reputation_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving reputation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reputation")

@router.get("/users/{user_address}/evaluations", response_model=List[Dict[str, Any]])
async def get_user_evaluations(
    user_address: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of evaluations"),
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> List[Dict[str, Any]]:
    """
    Get evaluation history for a user.
    
    Returns recent evaluations and their impact on reputation.
    """
    try:
        if not validate_hedera_address(user_address):
            raise HTTPException(status_code=400, detail="Invalid user address format")
        
        evaluations = await reputation_service.get_reputation_history(user_address, limit)
        
        logger.info(f"Retrieved {len(evaluations)} evaluations for {user_address}")
        return evaluations
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user evaluations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user evaluations")

@router.post("/users/{user_address}/update", response_model=Dict[str, Any])
async def update_user_reputation(
    user_address: str,
    request: UpdateReputationRequest,
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Update user reputation based on an event.
    
    Allows authorized systems to update reputation scores.
    """
    try:
        try:
            event_type = ReputationEventType(request.event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid event type")
        
        result = await reputation_service.update_reputation(
            user_address=user_address,
            event_type=event_type,
            impact_score=request.impact_score,
            context=request.context,
            validator_address=request.validator_address,
            blockchain_evidence=request.blockchain_evidence
        )
        
        logger.info(f"Reputation updated for {user_address}: {request.event_type}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reputation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update reputation")

# ============ LEGACY ENDPOINTS FOR BACKWARD COMPATIBILITY ============

@router.post("/evaluate-work", response_model=Dict[str, Any])
async def legacy_evaluate_work(
    user_id: str = Body(..., description="User ID"),
    skill_token_ids: List[str] = Body(..., description="Skill token IDs"),
    work_description: str = Body(..., description="Work description"),
    work_content: str = Body(..., description="Work content"),
    evaluation_criteria: Optional[str] = Body(None, description="Evaluation criteria"),
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Legacy endpoint for work evaluation.
    
    Maintains backward compatibility with existing integrations.
    """
    try:
        result = await reputation_service.evaluate_work(
            user_id=user_id,
            skill_token_ids=skill_token_ids,
            work_description=work_description,
            work_content=work_content,
            evaluation_criteria=evaluation_criteria
        )
        
        logger.info(f"Legacy work evaluation completed for {user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error in legacy work evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to evaluate work")

@router.get("/user/{user_id}/score", response_model=Dict[str, Any])
async def legacy_get_reputation_score(
    user_id: str,
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Legacy endpoint for reputation score retrieval.
    
    Maintains backward compatibility with existing integrations.
    """
    try:
        result = await reputation_service.get_reputation_score(user_id)
        
        logger.info(f"Legacy reputation score retrieved for {user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error retrieving legacy reputation score: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reputation score")

@router.get("/user/{user_id}/history", response_model=List[Dict[str, Any]])
async def legacy_get_reputation_history(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> List[Dict[str, Any]]:
    """
    Legacy endpoint for reputation history.
    
    Maintains backward compatibility with existing integrations.
    """
    try:
        result = await reputation_service.get_reputation_history(user_id, limit)
        
        logger.info(f"Legacy reputation history retrieved for {user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error retrieving legacy reputation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reputation history")

# ============ CONSENSUS SYSTEM ENDPOINTS ============

@router.post("/consensus", response_model=Dict[str, Any])
async def submit_for_consensus(
    evaluation_data: Dict[str, Any] = Body(..., description="Evaluation data for consensus"),
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Submit an evaluation for oracle consensus.
    
    Initiates a consensus process where multiple oracles vote on the evaluation.
    """
    try:
        # This would implement consensus submission logic
        # For now, return a mock response
        
        consensus_id = f"consensus_{hash(str(evaluation_data)) % 100000}"
        
        return {
            "success": True,
            "consensus_id": consensus_id,
            "status": "pending",
            "selected_oracles": 3,
            "voting_deadline": (datetime.now() + timedelta(days=3)).isoformat(),
            "submitted_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error submitting for consensus: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit for consensus")

@router.post("/consensus/{consensus_id}/vote", response_model=Dict[str, Any])
async def vote_on_consensus(
    consensus_id: str,
    oracle_address: str = Body(..., description="Oracle casting the vote"),
    approve: bool = Body(..., description="Whether to approve the evaluation"),
    score: int = Body(..., ge=0, le=100, description="Oracle's score"),
    feedback: str = Body("", description="Optional feedback"),
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Vote on a consensus evaluation.
    
    Allows selected oracles to vote on evaluations requiring consensus.
    """
    try:
        if not validate_hedera_address(oracle_address):
            raise HTTPException(status_code=400, detail="Invalid oracle address format")
        
        # This would implement consensus voting logic
        # For now, return a mock response
        
        return {
            "success": True,
            "consensus_id": consensus_id,
            "oracle_address": oracle_address,
            "vote": "approve" if approve else "reject",
            "score": score,
            "feedback": feedback,
            "cast_at": datetime.now().isoformat(),
            "remaining_votes": 2
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error casting consensus vote: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cast consensus vote")

@router.post("/consensus/{consensus_id}/finalize", response_model=Dict[str, Any])
async def finalize_consensus(
    consensus_id: str,
    reputation_service: ReputationService = Depends(get_reputation_service)
) -> Dict[str, Any]:
    """
    Finalize a consensus evaluation.
    
    Calculates final score and distributes oracle rewards.
    """
    try:
        # This would implement consensus finalization logic
        # For now, return a mock response
        
        return {
            "success": True,
            "consensus_id": consensus_id,
            "final_score": 78,
            "consensus_reached": True,
            "participating_oracles": 3,
            "oracle_rewards": {
                "0.0.1001": 2.5,
                "0.0.1002": 2.5,
                "0.0.1003": 2.5
            },
            "finalized_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error finalizing consensus: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to finalize consensus")

@router.get("/category/{user_address}/{category}")
async def get_category_score(
    user_address: str,
    category: str,
    current_user: User = Depends(get_current_user)
):
    """Get category-specific reputation score."""
    try:
        reputation_service = get_reputation_service()
        result = await reputation_service.get_category_score(
            user_address=user_address,
            category=category
        )
        return result
    except Exception as e:
        logger.error(f"Error getting category score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluation/{evaluation_id}")
async def get_work_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get work evaluation details."""
    try:
        reputation_service = get_reputation_service()
        result = await reputation_service.get_work_evaluation(
            evaluation_id=evaluation_id
        )
        return result
    except Exception as e:
        logger.error(f"Error getting work evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_address}/evaluations")
async def get_user_evaluations(
    user_address: str,
    current_user: User = Depends(get_current_user)
):
    """Get all evaluations for a user."""
    try:
        reputation_service = get_reputation_service()
        result = await reputation_service.get_user_evaluations(
            user_address=user_address
        )
        return result
    except Exception as e:
        logger.error(f"Error getting user evaluations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/global")
async def get_global_stats(
    current_user: User = Depends(get_current_user)
):
    """Get global reputation statistics."""
    try:
        reputation_service = get_reputation_service()
        result = await reputation_service.get_global_stats()
        return result
    except Exception as e:
        logger.error(f"Error getting global stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/oracle/{oracle_address}/status")
async def update_oracle_status(
    oracle_address: str,
    request: UpdateOracleStatusRequest,
    current_user: User = Depends(get_current_user)
):
    """Update oracle status."""
    try:
        reputation_service = get_reputation_service()
        result = await reputation_service.update_oracle_status(
            oracle_address=oracle_address,
            is_active=request.is_active,
            reason=request.reason
        )
        return result
    except Exception as e:
        logger.error(f"Error updating oracle status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

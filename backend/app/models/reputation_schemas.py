"""
Reputation API Request/Response Models

This module defines Pydantic models for reputation-related API endpoints.
Perfect 1:1 mapping with ReputationOracle.sol smart contract functions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.utils.hedera import validate_hedera_address


# ============ CONTRACT-ALIGNED REQUEST MODELS ============

class ContractRegisterOracleRequest(BaseModel):
    """Request model for registering oracle - matches ReputationOracle.registerOracle() exactly."""
    name: str = Field(..., description="Oracle name")
    specializations: List[str] = Field(..., description="Oracle specializations")
    # ❌ oracle_address removed (should be msg.sender in contract)
    # ❌ stake_amount removed (should be msg.value in contract)

class ContractSubmitEvaluationRequest(BaseModel):
    """Request model for submitting evaluation - matches ReputationOracle.submitWorkEvaluation() exactly."""
    user: str = Field(..., description="User address")
    skill_token_ids: List[int] = Field(..., description="Skill token IDs")
    work_description: str = Field(..., description="Work description")
    work_content: str = Field(..., description="Work content")
    overall_score: int = Field(..., description="Overall evaluation score")
    skill_scores: List[int] = Field(..., description="Individual skill scores")
    feedback: str = Field(..., description="Evaluation feedback")
    ipfs_hash: str = Field(..., description="IPFS hash")
    # ❌ oracle_address removed (should be msg.sender in contract)
    # ❌ work_id removed (not in contract)
    # ❌ evaluation_type removed (not in contract)

class ContractUpdateReputationScoreRequest(BaseModel):
    """Request model for updating reputation score - matches ReputationOracle.updateReputationScore() exactly."""
    user: str = Field(..., description="User address")
    category: str = Field(..., description="Skill category")
    new_score: int = Field(..., description="New reputation score")
    evidence: str = Field(..., description="Evidence for score update")

class ContractChallengeEvaluationRequest(BaseModel):
    """Request model for challenging evaluation - matches ReputationOracle.challengeEvaluation() exactly."""
    evaluation_id: int = Field(..., description="Evaluation ID")
    challenger: str = Field(..., description="Challenger address")
    challenge_reason: str = Field(..., description="Challenge reason")
    stake_amount: int = Field(..., description="Stake amount")

class ContractResolveChallengeRequest(BaseModel):
    """Request model for resolving challenge - matches ReputationOracle.resolveChallenge() exactly."""
    challenge_id: int = Field(..., description="Challenge ID")
    resolution: bool = Field(..., description="Challenge resolution")
    resolution_reason: str = Field(..., description="Resolution reason")

class ContractUpdateOracleStatusRequest(BaseModel):
    """Request model for updating oracle status - matches ReputationOracle.updateOracleStatus() exactly."""
    oracle_address: str = Field(..., description="Oracle address")
    is_active: bool = Field(..., description="Is oracle active")
    reason: str = Field("", description="Status change reason")

class ContractSlashOracleRequest(BaseModel):
    """Request model for slashing oracle - matches ReputationOracle.slashOracle() exactly."""
    oracle_address: str = Field(..., description="Oracle address")
    slash_amount: int = Field(..., description="Slash amount")
    slash_reason: str = Field(..., description="Slash reason")

class ContractWithdrawOracleStakeRequest(BaseModel):
    """Request model for withdrawing oracle stake - matches ReputationOracle.withdrawOracleStake() exactly."""
    oracle_address: str = Field(..., description="Oracle address")
    withdrawal_amount: int = Field(..., description="Withdrawal amount")

# ============ LEGACY REQUEST MODELS (DEPRECATED) ============

class RegisterOracleRequest(BaseModel):
    """Legacy request model - DEPRECATED: Use ContractRegisterOracleRequest instead."""
    name: str = Field(..., min_length=1, description="Oracle name")
    specializations: List[str] = Field(..., min_items=1, description="Oracle specializations")
    # ❌ stake_amount removed (should be msg.value in contract)
    # ❌ oracle_address removed (should be msg.sender in contract)
    
    @validator('specializations')
    def validate_specializations(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one specialization is required')
        return v

class SubmitWorkEvaluationRequest(BaseModel):
    """Legacy request model - DEPRECATED: Use ContractSubmitEvaluationRequest instead."""
    user_address: str = Field(..., description="User being evaluated")
    skill_token_ids: List[int] = Field(..., min_items=1, description="Skill token IDs")
    work_description: str = Field(..., min_length=1, description="Work description")
    work_content: str = Field(..., min_length=1, description="Work content")
    overall_score: int = Field(..., ge=0, le=10000, description="Overall score 0-10000")
    skill_scores: List[int] = Field(..., min_items=1, description="Individual skill scores")
    feedback: str = Field(..., description="Evaluation feedback")
    ipfs_hash: str = Field(..., min_length=1, description="IPFS hash for evaluation data")
    # ❌ oracle_address removed (should be msg.sender in contract)
    
    @validator('user_address')
    def validate_user_address(cls, v):
        if not validate_hedera_address(v):
            raise ValueError('Invalid user address format')
        return v
    
    @validator('skill_scores')
    def validate_skill_scores(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one skill score is required')
        for score in v:
            if not 0 <= score <= 10000:
                raise ValueError('Skill scores must be between 0 and 10000')
        return v
    
    @validator('overall_score')
    def validate_overall_score(cls, v):
        if not 0 <= v <= 10000:
            raise ValueError('Overall score must be between 0 and 10000')
        return v

class UpdateReputationScoreRequest(BaseModel):
    """Legacy request model - DEPRECATED: Use ContractUpdateReputationScoreRequest instead."""
    user_address: str = Field(..., description="User address")
    category: str = Field(..., min_length=1, description="Skill category")
    new_score: int = Field(..., ge=0, le=10000, description="New reputation score")
    evidence: str = Field(..., min_length=1, description="Evidence for score update")
    
    @validator('user_address')
    def validate_user_address(cls, v):
        if not validate_hedera_address(v):
            raise ValueError('Invalid user address format')
        return v
    
    @validator('new_score')
    def validate_new_score(cls, v):
        if not 0 <= v <= 10000:
            raise ValueError('New score must be between 0 and 10000')
        return v

class ChallengeEvaluationRequest(BaseModel):
    """Legacy request model - DEPRECATED: Use ContractChallengeEvaluationRequest instead."""
    evaluation_id: int = Field(..., ge=0, description="Evaluation ID to challenge")
    challenger_address: str = Field(..., description="Challenger address")
    challenge_reason: str = Field(..., min_length=10, description="Detailed reason for challenge")
    stake_amount: int = Field(..., gt=0, description="Stake amount for challenge")
    
    @validator('challenger_address')
    def validate_challenger_address(cls, v):
        if not validate_hedera_address(v):
            raise ValueError('Invalid challenger address format')
        return v
    
    @validator('stake_amount')
    def validate_stake_amount(cls, v):
        if v <= 0:
            raise ValueError('Stake amount must be greater than 0')
        return v

class ResolveChallengeRequest(BaseModel):
    """Legacy request model - DEPRECATED: Use ContractResolveChallengeRequest instead."""
    challenge_id: int = Field(..., ge=0, description="Challenge ID to resolve")
    resolution: bool = Field(..., description="Challenge resolution (true=uphold, false=overturn)")
    resolution_reason: str = Field(..., min_length=10, description="Detailed reason for resolution")
    resolver_address: str = Field(..., description="Address of the resolver")
    
    @validator('resolver_address')
    def validate_resolver_address(cls, v):
        if not validate_hedera_address(v):
            raise ValueError('Invalid resolver address format')
        return v

class UpdateOracleStatusRequest(BaseModel):
    """Request model for updating oracle status."""
    is_active: bool = Field(..., description="Whether the oracle should be active")
    reason: str = Field(..., description="Reason for status change")

# ============ RESPONSE MODELS ============

class OracleRegistrationResponse(BaseModel):
    """Response model for oracle registration."""
    success: bool
    oracle_address: str
    transaction_id: Optional[str]
    message: str
    timestamp: datetime

class WorkEvaluationResponse(BaseModel):
    """Response model for work evaluation submission."""
    success: bool
    evaluation_id: int
    transaction_id: Optional[str]
    message: str
    timestamp: datetime

class ReputationScoreResponse(BaseModel):
    """Response model for reputation score updates."""
    success: bool
    user_address: str
    category: str
    old_score: int
    new_score: int
    transaction_id: Optional[str]
    message: str
    timestamp: datetime

class ChallengeResponse(BaseModel):
    """Response model for evaluation challenges."""
    success: bool
    challenge_id: int
    evaluation_id: int
    challenger_address: str
    transaction_id: Optional[str]
    message: str
    timestamp: datetime

class ChallengeResolutionResponse(BaseModel):
    """Response model for challenge resolutions."""
    success: bool
    challenge_id: int
    resolution: bool
    resolution_reason: str
    resolver_address: str
    transaction_id: Optional[str]
    message: str
    timestamp: datetime

class OracleInfoResponse(BaseModel):
    """Response model for oracle information."""
    oracle_address: str
    name: str
    specializations: List[str]
    is_active: bool
    stake_amount: int
    evaluations_completed: int
    average_score: float
    registered_at: datetime
    last_activity: datetime

class ReputationScoreInfoResponse(BaseModel):
    """Response model for reputation score information."""
    user_address: str
    overall_score: int
    category_scores: Dict[str, int]
    total_evaluations: int
    last_updated: datetime
    is_active: bool

class EvaluationHistoryResponse(BaseModel):
    """Response model for evaluation history."""
    user_address: str
    evaluations: List[Dict[str, Any]]
    total_count: int
    average_score: float
    last_evaluation: Optional[datetime]

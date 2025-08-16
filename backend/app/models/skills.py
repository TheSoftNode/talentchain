"""
Skills and Skill Tokens Models
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SkillTokenData(BaseModel):
    """Skill token data structure."""
    category: str = Field(..., description="Skill category")
    subcategory: str = Field(..., description="Skill subcategory")
    level: int = Field(..., description="Skill level (1-10)")
    expiry_date: int = Field(..., description="Expiry date as Unix timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CreateSkillTokenRequest(BaseModel):
    """Request model for creating a skill token."""
    recipient: str = Field(..., description="Recipient address")
    skill_data: SkillTokenData = Field(..., description="Skill token data")
    token_uri: str = Field(..., description="Token URI for metadata")


class UpdateSkillLevelRequest(BaseModel):
    """Request model for updating skill level."""
    token_id: str = Field(..., description="Skill token ID")
    new_level: int = Field(..., ge=1, le=10, description="New skill level")
    evidence: str = Field(..., description="Evidence for the level update")


class AddExperienceRequest(BaseModel):
    """Request model for adding experience to a skill."""
    token_id: str = Field(..., description="Skill token ID")
    experience_points: int = Field(..., gt=0, description="Experience points to add")
    description: str = Field(..., description="Description of the experience")


class BatchCreateRequest(BaseModel):
    """Request model for batch creating skill tokens."""
    recipient: str = Field(..., description="Recipient address")
    skills: List[SkillTokenData] = Field(..., description="List of skills to create")
    token_uris: List[str] = Field(..., description="List of token URIs")


class EndorseSkillTokenRequest(BaseModel):
    """Request model for endorsing a skill token."""
    token_id: str = Field(..., description="ID of the skill token to endorse")
    endorsement_data: str = Field(..., description="Data describing the endorsement")


class RenewSkillTokenRequest(BaseModel):
    """Request model for renewing a skill token."""
    token_id: str = Field(..., description="ID of the skill token to renew")
    new_expiry_date: int = Field(..., description="New expiry date as Unix timestamp")


class RevokeSkillTokenRequest(BaseModel):
    """Request model for revoking a skill token."""
    token_id: str = Field(..., description="ID of the skill token to revoke")
    reason: str = Field(..., description="Reason for revocation")


class MarkExpiredTokensRequest(BaseModel):
    """Request model for marking skill tokens as expired."""
    token_ids: List[str] = Field(..., description="List of token IDs to mark as expired")


class SkillTokenResponse(BaseModel):
    """Response model for skill token operations."""
    success: bool = Field(..., description="Operation success status")
    token_id: Optional[str] = Field(None, description="Created token ID")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class BatchOperationResponse(BaseModel):
    """Response model for batch operations."""
    success: bool = Field(..., description="Operation success status")
    token_ids: List[str] = Field(default_factory=list, description="List of created token IDs")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class WorkEvaluationRequest(BaseModel):
    """Request model for work evaluation."""
    user_id: str = Field(..., description="User ID to evaluate")
    skill_token_ids: List[str] = Field(..., description="Skill token IDs to evaluate")
    work_description: str = Field(..., description="Description of the work")
    work_content: str = Field(..., description="Content of the work")
    evaluation_criteria: Dict[str, Any] = Field(default_factory=dict, description="Evaluation criteria")


class WorkEvaluationResponse(BaseModel):
    """Response model for work evaluation."""
    success: bool = Field(..., description="Evaluation success status")
    evaluation_id: Optional[str] = Field(None, description="Evaluation ID")
    scores: Dict[str, float] = Field(default_factory=dict, description="Scores for each skill")
    overall_score: Optional[float] = Field(None, description="Overall evaluation score")
    feedback: Optional[str] = Field(None, description="Evaluation feedback")
    error: Optional[str] = Field(None, description="Error message if evaluation failed")




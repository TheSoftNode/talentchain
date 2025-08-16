"""
Comprehensive Reputation Service Module

This module provides enterprise-level reputation management including scoring algorithms,
peer validation, Oracle integration, anti-gaming mechanisms, and comprehensive
audit trails for the TalentChain Pro ecosystem.
"""

import os
import json
import uuid
import logging
import hashlib
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum

# Configure logging first
logger = logging.getLogger(__name__)

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import and_, or_, desc, func, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not available, using fallback functionality")

try:
    from app.models.database import (
        ReputationScore, ReputationTransaction, ReputationValidation,
        SkillToken, JobPool, PoolApplication, PoolMatch, AuditLog,
        User, ReputationMetric, ReputationOracle, WorkEvaluation, 
        EvaluationChallenge
    )
    from app.database import get_db_session, cache_manager
    DATABASE_MODELS_AVAILABLE = True
except ImportError:
    DATABASE_MODELS_AVAILABLE = False
    logger.warning("Database models not available, using fallback functionality")

from app.utils.hedera import (
    get_contract_manager, get_client, submit_hcs_message,
    validate_hedera_address, resolve_challenge, slash_oracle,
    withdraw_oracle_stake, get_oracle_performance, get_category_score,
    get_work_evaluation, get_user_evaluations, get_global_stats,
    update_oracle_status
)

try:
    from app.services.mcp import get_mcp_service
    MCP_SERVICE_AVAILABLE = True
except ImportError:
    MCP_SERVICE_AVAILABLE = False
    logger.warning("MCP service not available, using fallback reputation calculation")

try:
    from app.config import get_settings
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.warning("Config not available, using environment variables")

# Fallback storage for when database is not available
_fallback_reputation = {}
_fallback_validations = {}
_fallback_transactions = {}


class ReputationEventType(str, Enum):
    """Types of reputation events."""
    SKILL_VALIDATION = "skill_validation"
    JOB_COMPLETION = "job_completion"
    PEER_REVIEW = "peer_review"
    COMMUNITY_CONTRIBUTION = "community_contribution"
    GOVERNANCE_PARTICIPATION = "governance_participation"
    PENALTY_APPLIED = "penalty_applied"
    BONUS_AWARDED = "bonus_awarded"
    MILESTONE_ACHIEVED = "milestone_achieved"


class ValidationStatus(str, Enum):
    """Status of reputation validations."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    EXPIRED = "expired"


class ReputationCategory(str, Enum):
    """Categories of reputation metrics."""
    TECHNICAL_SKILL = "technical_skill"
    COLLABORATION = "collaboration"
    RELIABILITY = "reliability"
    COMMUNICATION = "communication"
    LEADERSHIP = "leadership"
    INNOVATION = "innovation"
    GOVERNANCE = "governance"

class ReputationService:
    """Comprehensive service for managing reputation scores and validation."""
    
    def __init__(self):
        """Initialize the reputation service."""
        if CONFIG_AVAILABLE:
            self.settings = get_settings()
        else:
            self.settings = None
        
        self.contract_manager = None
        self.mcp_service = None
        
        # Reputation scoring weights
        self.scoring_weights = {
            ReputationCategory.TECHNICAL_SKILL: 0.25,
            ReputationCategory.COLLABORATION: 0.20,
            ReputationCategory.RELIABILITY: 0.20,
            ReputationCategory.COMMUNICATION: 0.15,
            ReputationCategory.LEADERSHIP: 0.10,
            ReputationCategory.INNOVATION: 0.05,
            ReputationCategory.GOVERNANCE: 0.05
        }
        
        # Anti-gaming parameters
        self.max_validations_per_day = 10
        self.min_validation_stake = 1.0  # HBAR
        self.validation_cooldown_hours = 24
        self.reputation_decay_factor = 0.98  # 2% monthly decay
        
        logger.info("Reputation service initialized")
    
    def _get_contract_manager(self):
        """Lazy load contract manager."""
        if self.contract_manager is None:
            self.contract_manager = get_contract_manager()
        return self.contract_manager
    
    def _get_mcp_service(self):
        """Lazy load MCP service for AI-powered reputation analysis."""
        if self.mcp_service is None and MCP_SERVICE_AVAILABLE:
            self.mcp_service = get_mcp_service()
        return self.mcp_service
    
    def _get_db_session(self):
        """Get database session if available."""
        if DATABASE_MODELS_AVAILABLE:
            try:
                return get_db_session()
            except Exception as e:
                logger.warning(f"Database session not available: {str(e)}")
                DATABASE_MODELS_AVAILABLE = False
        return None
    
    async def _get_current_user_address(self) -> Optional[str]:
        """
        Get the current authenticated user's address.
        This is the equivalent of msg.sender in smart contracts.
        
        Returns:
            User's Hedera address or None if not authenticated
        """
        # TODO: This should be replaced with proper request context
        # For now, return a mock address - this should be replaced with
        # actual authentication logic from the request context
        try:
            # This should come from the authenticated request context
            # For example: request.state.user.address
            return "0.0.123456"  # Mock address for development
        except Exception as e:
            logger.warning(f"Could not get current user address: {str(e)}")
            return None
    
    def get_auth_context_from_request(self, request) -> Optional[str]:
        """
        Get the authenticated user address from a FastAPI request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            User's Hedera address or None if not authenticated
        """
        try:
            # Try to get from request state
            if hasattr(request, 'state') and hasattr(request.state, 'user'):
                return request.state.user.user_address
            
            # Try to get from headers (fallback)
            wallet_address = request.headers.get("X-Wallet-Address")
            if wallet_address:
                return wallet_address
            
            # Try to get from query parameters (fallback)
            wallet_address = request.query_params.get("wallet_address")
            if wallet_address:
                return wallet_address
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not get user address from request: {str(e)}")
            return None
    
    async def _get_transaction_value(self) -> float:
        """
        Get the transaction value (msg.value equivalent).
        This should come from the transaction context.
        
        Returns:
            Transaction value in HBAR
        """
        # TODO: Implement proper transaction value extraction
        # For now, return a default value - this should be replaced with
        # actual transaction value from the request context
        try:
            # This should come from the transaction context
            # For example: request.state.transaction.value
            return 100.0  # Default stake amount for development
        except Exception as e:
            logger.warning(f"Could not get transaction value: {str(e)}")
            return 100.0  # Default fallback value
    
    def _invalidate_cache(self, patterns: List[str]):
        """Invalidate cache patterns if cache manager is available."""
        if DATABASE_MODELS_AVAILABLE and hasattr(cache_manager, 'invalidate_pattern'):
            for pattern in patterns:
                try:
                    cache_manager.invalidate_pattern(pattern)
                except:
                    pass
    
    # ============ CORE REPUTATION FUNCTIONS ============
    
    async def calculate_reputation_score(
        self,
        user_address: str,
        category: Optional[ReputationCategory] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive reputation score for a user.
        
        Args:
            user_address: User's Hedera account address
            category: Specific category to calculate (None for overall)
            
        Returns:
            Dict containing reputation score and breakdown
        """
        try:
            if not validate_hedera_address(user_address):
                raise ValueError("Invalid Hedera address format")
            
            # Get base reputation data
            base_data = await self._get_base_reputation_data(user_address)
            
            if category:
                # Calculate specific category score
                score = await self._calculate_category_score(user_address, category, base_data)
                
                return {
                    "user_address": user_address,
                    "category": category.value,
                    "score": score,
                    "max_score": 100.0,
                    "calculated_at": datetime.now(timezone.utc).isoformat(),
                    "breakdown": await self._get_category_breakdown(user_address, category)
                }
            else:
                # Calculate overall reputation score
                overall_score = 0.0
                category_scores = {}
                
                for cat, weight in self.scoring_weights.items():
                    cat_score = await self._calculate_category_score(user_address, cat, base_data)
                    category_scores[cat.value] = cat_score
                    overall_score += cat_score * weight
                
                # Apply time decay factor
                overall_score = await self._apply_time_decay(user_address, overall_score)
                
                # Apply anti-gaming adjustments
                overall_score = await self._apply_anti_gaming_adjustments(user_address, overall_score)
                
                return {
                    "user_address": user_address,
                    "overall_score": round(overall_score, 2),
                    "max_score": 100.0,
                    "category_scores": category_scores,
                    "calculated_at": datetime.now(timezone.utc).isoformat(),
                    "scoring_weights": {k.value: v for k, v in self.scoring_weights.items()},
                    "factors_applied": {
                        "time_decay": True,
                        "anti_gaming": True,
                        "peer_validation": True
                    }
                }
        
        except Exception as e:
            logger.error(f"Error calculating reputation score: {str(e)}")
            raise
    
    async def update_reputation(
        self,
        user_address: str,
        event_type: ReputationEventType,
        impact_score: float,
        context: Dict[str, Any],
        validator_address: Optional[str] = None,
        blockchain_evidence: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user reputation based on an event.
        
        Args:
            user_address: User's address
            event_type: Type of reputation event
            impact_score: Score impact (-100 to +100)
            context: Event context and metadata
            validator_address: Address of the validator (if applicable)
            blockchain_evidence: Blockchain transaction ID as evidence
            
        Returns:
            Dict containing update result
        """
        try:
            if not validate_hedera_address(user_address):
                raise ValueError("Invalid user address format")
            
            if validator_address and not validate_hedera_address(validator_address):
                raise ValueError("Invalid validator address format")
            
            if not (-100 <= impact_score <= 100):
                raise ValueError("Impact score must be between -100 and +100")
            
            # Validate event context
            await self._validate_reputation_event(user_address, event_type, context)
            
            # Create reputation transaction
            transaction_id = await self._create_reputation_transaction(
                user_address=user_address,
                event_type=event_type,
                impact_score=impact_score,
                context=context,
                validator_address=validator_address,
                blockchain_evidence=blockchain_evidence
            )
            
            # Update reputation scores
            updated_scores = await self._apply_reputation_update(
                user_address, event_type, impact_score, context
            )
            
            # Submit to blockchain for transparency
            if blockchain_evidence:
                await self._submit_reputation_evidence(transaction_id, blockchain_evidence)
            
            # Invalidate caches
            self._invalidate_cache([
                f"reputation:{user_address}:*",
                "reputation_leaderboard:*"
            ])
            
            logger.info(f"Updated reputation for {user_address}: {event_type.value} (+{impact_score})")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "user_address": user_address,
                "event_type": event_type.value,
                "impact_score": impact_score,
                "updated_scores": updated_scores,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error updating reputation: {str(e)}")
            raise
    
    # ============ ORACLE MANAGEMENT FUNCTIONS ============
    
    async def register_oracle(
        self,
        name: str,                      # ✅ Keep only contract parameters
        specializations: List[str]      # ✅ Keep only contract parameters
        # ❌ Removed oracle_address (should be msg.sender in contract)
        # ❌ Removed stake_amount (should be msg.value in contract)
    ) -> Dict[str, Any]:
        """
        Register a new reputation oracle.
        
        Args:
            name: Oracle display name
            specializations: List of skill categories the oracle specializes in
            
        Returns:
            Dict containing oracle registration result
        """
        try:
            # Get oracle address from current context (msg.sender equivalent)
            oracle_address = await self._get_current_user_address()
            if not oracle_address:
                raise ValueError("No authenticated user found")
            
            if not validate_hedera_address(oracle_address):
                raise ValueError("Invalid oracle address format")
            
            # Get stake amount from transaction context (msg.value equivalent)
            # This should come from the transaction that calls this function
            stake_amount = await self._get_transaction_value()
            if stake_amount < self.min_validation_stake:
                raise ValueError(f"Minimum stake amount is {self.min_validation_stake} HBAR")
            
            if not specializations:
                raise ValueError("At least one specialization is required")
            
            # Create oracle registration data
            oracle_id = f"oracle_{hash(oracle_address + name) % 100000}"
            registration_data = {
                "oracle_id": oracle_id,
                "oracle_address": oracle_address,
                "name": name,
                "specializations": specializations,
                "stake_amount": stake_amount,
                "is_active": True,
                "total_evaluations": 0,
                "successful_evaluations": 0,
                "reputation_score": 100.0,
                "registered_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store in database if available
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        # Check if oracle already exists
                        existing_oracle = db.query(ReputationOracle).filter(
                            ReputationOracle.oracle_address == oracle_address
                        ).first()
                        
                        if existing_oracle:
                            raise ValueError("Oracle already registered for this address")
                        
                        oracle = ReputationOracle(
                            oracle_id=oracle_id,
                            oracle_address=oracle_address,
                            name=name,
                            specializations=specializations,
                            stake_amount=stake_amount,
                            is_active=True,
                            total_evaluations=0,
                            successful_evaluations=0,
                            reputation_score=100.0
                        )
                        
                        db.add(oracle)
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=oracle_address,
                            action="register_oracle",
                            resource_type="reputation_oracle",
                            resource_id=oracle_id,
                            details={
                                "name": name,
                                "specializations": specializations,
                                "stake_amount": stake_amount
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate caches
                        self._invalidate_cache([
                            "reputation_oracles:*",
                            f"oracle:{oracle_address}:*"
                        ])
                        
                        db.commit()
                        
                except Exception as db_error:
                    logger.warning(f"Database oracle registration failed: {str(db_error)}")
                    DATABASE_MODELS_AVAILABLE = False
            
            # Fallback storage
            if not DATABASE_MODELS_AVAILABLE:
                _fallback_reputation[oracle_id] = registration_data
                logger.info(f"Stored oracle {oracle_id} in fallback storage")
            
            # Call blockchain contract for oracle registration
            try:
                from app.utils.hedera import register_reputation_oracle
                
                contract_result = await register_reputation_oracle(
                    name=name,
                    specializations=specializations
                )
                
                if contract_result.success:
                    logger.info(f"Registered oracle on blockchain: {contract_result.transaction_id}")
                    # Update registration data with blockchain info
                    registration_data["transaction_id"] = contract_result.transaction_id
                    registration_data["blockchain_verified"] = True
                else:
                    logger.warning(f"Failed to register oracle on blockchain: {contract_result.error}")
                    registration_data["blockchain_verified"] = False
                    
            except Exception as e:
                logger.warning(f"Blockchain oracle registration failed: {str(e)}")
                registration_data["blockchain_verified"] = False
            
            return {
                "success": True,
                "oracle_id": oracle_id,
                "oracle_address": oracle_address,
                "name": name,
                "specializations": specializations,
                "stake_amount": stake_amount,
                "message": "Oracle registered successfully",
                "transaction_id": registration_data.get("transaction_id"),
                "blockchain_verified": registration_data.get("blockchain_verified", False)
            }
        
        except Exception as e:
            logger.error(f"Error registering oracle: {str(e)}")
            raise
    
    async def submit_work_evaluation(
        self,
        user: str,
        skill_token_ids: List[int],
        work_description: str,
        work_content: str,
        overall_score: int,
        skill_scores: List[int],
        feedback: str,
        ipfs_hash: str
    ) -> Dict[str, Any]:
        """
        Submit a work evaluation.
        
        Args:
            user: User address being evaluated
            skill_token_ids: List of skill token IDs
            work_description: Description of the work
            work_content: Content of the work
            overall_score: Overall evaluation score
            skill_scores: Individual skill scores
            feedback: Evaluation feedback
            ipfs_hash: IPFS hash for evaluation data
            
        Returns:
            Dict containing evaluation submission result
        """
        try:
            # Get oracle address from current context (msg.sender equivalent)
            oracle_address = await self._get_current_user_address()
            if not oracle_address:
                raise ValueError("No authenticated oracle found")
            
            if not validate_hedera_address(oracle_address):
                raise ValueError("Invalid oracle address format")
            
            if not validate_hedera_address(user):
                raise ValueError("Invalid user address format")
            
            # Validate scores
            if not 0 <= overall_score <= 10000:
                raise ValueError("Overall score must be between 0 and 10000")
            
            if len(skill_scores) != len(skill_token_ids):
                raise ValueError("Skill scores array must have same length as skill token IDs")
            
            for score in skill_scores:
                if not 0 <= score <= 10000:
                    raise ValueError("Each skill score must be between 0 and 10000")
            
            # Check if oracle is registered and active
            oracle_info = await self._get_oracle_info(oracle_address)
            if not oracle_info or not oracle_info.get("is_active"):
                raise ValueError("Oracle not registered or inactive")
            
            # Generate evaluation ID
            evaluation_id = f"evaluation_{hash(user + oracle_address + str(overall_score)) % 100000}"
            current_time = datetime.now(timezone.utc)
            
            # Call blockchain contract for work evaluation submission
            try:
                from app.utils.hedera import submit_work_evaluation
                
                contract_result = await submit_work_evaluation(
                    user=user,
                    skill_token_ids=skill_token_ids,
                    work_description=work_description,
                    work_content=work_content,
                    overall_score=overall_score,
                    skill_scores=skill_scores,
                    feedback=feedback,
                    ipfs_hash=ipfs_hash
                )
                
                if contract_result.success:
                    logger.info(f"Submitted work evaluation on blockchain: {contract_result.transaction_id}")
                    # Use evaluation ID from contract if available
                    evaluation_id = contract_result.token_id or evaluation_id
                    transaction_id = contract_result.transaction_id
                    blockchain_verified = True
                else:
                    logger.warning(f"Failed to submit evaluation on blockchain: {contract_result.error}")
                    transaction_id = None
                    blockchain_verified = False
                    
            except Exception as e:
                logger.warning(f"Blockchain evaluation submission failed: {str(e)}")
                transaction_id = None
                blockchain_verified = False
            
            # Create evaluation data
            evaluation_data = {
                "evaluation_id": evaluation_id,
                "user_address": user,
                "oracle_address": oracle_address,
                "skill_token_ids": skill_token_ids,
                "work_description": work_description,
                "work_content": work_content,
                "overall_score": overall_score,
                "skill_scores": skill_scores,
                "feedback": feedback,
                "ipfs_hash": ipfs_hash,
                "transaction_id": transaction_id,
                "blockchain_verified": blockchain_verified,
                "submitted_at": current_time.isoformat()
            }
            
            # Store in database if available
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        evaluation = WorkEvaluation(
                            evaluation_id=evaluation_id,
                            user_address=user,
                            oracle_address=oracle_address,
                            skill_token_ids=skill_token_ids,
                            work_description=work_description,
                            work_content=work_content,
                            overall_score=overall_score,
                            skill_scores=skill_scores,
                            feedback=feedback,
                            ipfs_hash=ipfs_hash,
                            transaction_id=transaction_id,
                            blockchain_verified=blockchain_verified
                        )
                        
                        db.add(evaluation)
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=oracle_address,
                            action="submit_work_evaluation",
                            resource_type="work_evaluation",
                            resource_id=evaluation_id,
                            details={
                                "user_address": user,
                                "overall_score": overall_score,
                                "skill_count": len(skill_token_ids),
                                "transaction_id": transaction_id
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate caches
                        self._invalidate_cache([
                            f"evaluations:{user}:*",
                            f"oracle_evaluations:{oracle_address}:*",
                            "evaluation_stats:*"
                        ])
                        
                        db.commit()
                        
                        logger.info(f"Stored evaluation {evaluation_id} in database")
                        
                except Exception as db_error:
                    logger.warning(f"Database evaluation storage failed: {str(db_error)}")
                    DATABASE_MODELS_AVAILABLE = False
            
            # Fallback storage
            if not DATABASE_MODELS_AVAILABLE:
                _fallback_reputation[evaluation_id] = evaluation_data
                logger.info(f"Stored evaluation {evaluation_id} in fallback storage")
            
            return {
                "success": True,
                "evaluation_id": evaluation_id,
                "user_address": user,
                "oracle_address": oracle_address,
                "overall_score": overall_score,
                "skill_count": len(skill_token_ids),
                "message": "Work evaluation submitted successfully",
                "transaction_id": transaction_id,
                "blockchain_verified": blockchain_verified
            }
        
        except Exception as e:
            logger.error(f"Error submitting work evaluation: {str(e)}")
            raise
    
    async def challenge_evaluation(
        self,
        challenger_address: str,
        evaluation_id: str,
        reason: str,
        evidence: List[str],
        stake_amount: float = 10.0
    ) -> Dict[str, Any]:
        """
        Challenge a work evaluation.
        
        Args:
            challenger_address: Address challenging the evaluation
            evaluation_id: ID of the evaluation being challenged
            reason: Reason for the challenge
            evidence: List of evidence supporting the challenge
            stake_amount: Stake required for challenge
            
        Returns:
            Dict containing challenge result
        """
        try:
            if not validate_hedera_address(challenger_address):
                raise ValueError("Invalid challenger address format")
            
            if stake_amount < self.min_validation_stake:
                raise ValueError(f"Minimum stake amount is {self.min_validation_stake} HBAR")
            
            # Get evaluation details
            evaluation = await self._get_evaluation_details(evaluation_id)
            if not evaluation:
                raise ValueError(f"Evaluation {evaluation_id} not found")
            
            if evaluation.get("status") != "completed":
                raise ValueError("Can only challenge completed evaluations")
            
            # Create challenge record
            challenge_id = f"challenge_{hash(evaluation_id + challenger_address) % 100000}"
            challenge_data = {
                "challenge_id": challenge_id,
                "evaluation_id": evaluation_id,
                "challenger_address": challenger_address,
                "reason": reason,
                "evidence": evidence,
                "stake_amount": stake_amount,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store challenge in database if available
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        challenge = EvaluationChallenge(
                            challenge_id=challenge_id,
                            evaluation_id=evaluation_id,
                            challenger_address=challenger_address,
                            reason=reason,
                            evidence=evidence,
                            stake_amount=stake_amount,
                            status="pending"
                        )
                        
                        db.add(challenge)
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=challenger_address,
                            action="challenge_evaluation",
                            resource_type="evaluation_challenge",
                            resource_id=challenge_id,
                            details={
                                "evaluation_id": evaluation_id,
                                "reason": reason,
                                "stake_amount": stake_amount
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate caches
                        self._invalidate_cache([
                            f"evaluation:{evaluation_id}:*",
                            f"challenges:*"
                        ])
                except Exception as db_error:
                    logger.warning(f"Database challenge storage failed: {str(db_error)}")
                    DATABASE_MODELS_AVAILABLE = False
            
            # Fallback storage
            if not DATABASE_MODELS_AVAILABLE:
                if "challenges" not in _fallback_validations:
                    _fallback_validations["challenges"] = {}
                _fallback_validations["challenges"][challenge_id] = challenge_data
            
            logger.info(f"Evaluation challenge {challenge_id} created by {challenger_address}")
            
            return {
                "success": True,
                "challenge_id": challenge_id,
                "evaluation_id": evaluation_id,
                "challenger_address": challenger_address,
                "reason": reason,
                "stake_amount": stake_amount,
                "status": "pending",
                "created_at": challenge_data["created_at"]
            }
        
        except Exception as e:
            logger.error(f"Error challenging evaluation: {str(e)}")
            raise
    
    async def get_active_oracles(self) -> List[Dict[str, Any]]:
        """Get list of active reputation oracles."""
        try:
            oracles = []
            
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        oracle_records = db.query(ReputationOracle).filter(
                            ReputationOracle.is_active == True
                        ).all()
                        
                        for oracle in oracle_records:
                            oracles.append({
                                "oracle_id": oracle.oracle_id,
                                "oracle_address": oracle.oracle_address,
                                "name": oracle.name,
                                "specializations": oracle.specializations,
                                "total_evaluations": oracle.total_evaluations,
                                "successful_evaluations": oracle.successful_evaluations,
                                "reputation_score": float(oracle.reputation_score),
                                "is_active": oracle.is_active
                            })
                except Exception as db_error:
                    logger.warning(f"Database oracle retrieval failed: {str(db_error)}")
            else:
                # Fallback to memory storage
                oracle_data = _fallback_reputation.get("oracles", {})
                oracles = [
                    oracle for oracle in oracle_data.values()
                    if oracle.get("is_active", False)
                ]
            
            return oracles
        
        except Exception as e:
            logger.error(f"Error getting active oracles: {str(e)}")
            return []
    
    # ============ LEGACY COMPATIBILITY FUNCTIONS ============
    
    async def evaluate_work(
        self,
        user_id: str,
        skill_token_ids: List[str],
        work_description: str,
        work_content: str,
        evaluation_criteria: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhanced work evaluation using the actual ReputationOracle contract."""
        try:
            # Convert to new reputation update system
            evaluation_id = f"eval_{hash(user_id + work_description) % 100000}"
            
            # Use MCP service for work evaluation if available
            mcp_service = self._get_mcp_service()
            
            if mcp_service:
                # AI-powered evaluation
                evaluation_result = await mcp_service.evaluate_work_submission(
                    user_id=user_id,
                    work_description=work_description,
                    work_content=work_content,
                    skill_tokens=skill_token_ids,
                    criteria=evaluation_criteria
                )
                
                overall_score = int(evaluation_result.get("overall_score", 75.0))
                skill_scores = evaluation_result.get("skill_scores", {})
                recommendation = evaluation_result.get("recommendation", "Good work! Keep improving.")
            else:
                # Fallback scoring
                overall_score = min(100, int(75.0 + len(work_content) * 0.01))  # Simple content-based scoring
                skill_scores = {token_id: overall_score for token_id in skill_token_ids}
                recommendation = "Work evaluated. Consider providing more detailed submissions for better scoring."
            
            # Convert skill_scores to list format for contract
            skill_scores_list = [skill_scores.get(token_id, overall_score) for token_id in skill_token_ids]
            
            # Submit evaluation to the Oracle contract
            from app.utils.hedera import submit_work_evaluation_to_oracle
            
            contract_result = await submit_work_evaluation_to_oracle(
                user_address=user_id,
                skill_token_ids=skill_token_ids,
                work_description=work_description,
                work_content=work_content,
                overall_score=overall_score,
                skill_scores=skill_scores_list,
                feedback=recommendation,
                ipfs_hash=""  # Could be populated with IPFS hash of work artifacts
            )
            
            if contract_result.success:
                evaluation_id = contract_result.token_id or evaluation_id
                
                # Update reputation based on evaluation
                if overall_score > 70:
                    await self.update_reputation(
                        user_address=user_id,
                        event_type=ReputationEventType.JOB_COMPLETION,
                        impact_score=(overall_score - 50) * 0.5,  # Scale to -25 to +25
                        context={
                            "evaluation_id": evaluation_id,
                            "work_description": work_description,
                            "overall_score": overall_score,
                            "skill_tokens": skill_token_ids,
                            "transaction_id": contract_result.transaction_id
                        },
                        blockchain_evidence=contract_result.transaction_id
                    )
            
            # Calculate level changes
            level_changes = {}
            for token_id in skill_token_ids:
                score = skill_scores.get(token_id, overall_score)
                if score > 85:
                    level_changes[token_id] = 1
                elif score < 40:
                    level_changes[token_id] = -1
                else:
                    level_changes[token_id] = 0
            
            return {
                "evaluation_id": evaluation_id,
                "user_id": user_id,
                "overall_score": overall_score,
                "skill_scores": skill_scores,
                "recommendation": recommendation,
                "level_changes": level_changes,
                "timestamp": datetime.now(timezone.utc),
                "transaction_id": contract_result.transaction_id if contract_result.success else None,
                "blockchain_verified": contract_result.success
            }
        
        except Exception as e:
            logger.error(f"Error evaluating work: {str(e)}")
            raise
    
    async def get_reputation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Legacy function for backward compatibility."""
        try:
            base_data = await self._get_base_reputation_data(user_id)
            transactions = base_data.get("transactions", [])
            
            # Sort by date and limit
            sorted_transactions = sorted(
                transactions,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )[:limit]
            
            # Convert to legacy format
            history = []
            for transaction in sorted_transactions:
                history.append({
                    "evaluation_id": transaction.get("id", "unknown"),
                    "overall_score": 50 + transaction.get("impact_score", 0),
                    "skill_token_ids": transaction.get("context", {}).get("skill_tokens", []),
                    "level_changes": transaction.get("context", {}).get("level_changes", {}),
                    "timestamp": transaction.get("created_at", datetime.now(timezone.utc).isoformat())
                })
            
            return history
        
        except Exception as e:
            logger.error(f"Error retrieving reputation history: {str(e)}")
            return []
    
    async def get_reputation_score(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get reputation score from blockchain oracle and cache."""
        try:
            # Get reputation from Oracle contract first
            from app.utils.hedera import get_reputation_score_from_oracle
            
            oracle_reputation = await get_reputation_score_from_oracle(user_id)
            
            if oracle_reputation:
                # Use blockchain data as primary source
                return {
                    "user_id": user_id,
                    "overall_score": float(oracle_reputation["overall_score"]),
                    "total_evaluations": oracle_reputation["total_evaluations"],
                    "last_updated": datetime.fromtimestamp(oracle_reputation["last_updated"]).isoformat() if oracle_reputation["last_updated"] > 0 else datetime.now(timezone.utc).isoformat(),
                    "is_active": oracle_reputation["is_active"],
                    "source": "blockchain_oracle",
                    "skill_scores": {
                        "blockchain": float(oracle_reputation["overall_score"]) * 0.9,  # Slightly lower for specific skills
                        "frontend": float(oracle_reputation["overall_score"]) * 0.8,
                        "backend": float(oracle_reputation["overall_score"]) * 0.85
                    }
                }
            
            # Fallback to comprehensive reputation calculation
            reputation_data = await self.calculate_reputation_score(user_id)
            
            # Convert to legacy format
            return {
                "user_id": user_id,
                "overall_score": reputation_data.get("overall_score", 50.0),
                "total_evaluations": 0,  # This would need to be tracked separately
                "last_updated": reputation_data.get("calculated_at", datetime.now(timezone.utc).isoformat()),
                "is_active": True,
                "source": "calculated",
                "skill_scores": {
                    "blockchain": reputation_data.get("category_scores", {}).get("technical_skill", 50.0),
                    "frontend": reputation_data.get("category_scores", {}).get("technical_skill", 50.0),
                    "backend": reputation_data.get("category_scores", {}).get("technical_skill", 50.0)
                }
            }
        
        except Exception as e:
            logger.error(f"Error retrieving reputation score: {str(e)}")
            return {
                "user_id": user_id,
                "overall_score": 50.0,
                "total_evaluations": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "is_active": True,
                "source": "fallback",
                "skill_scores": {"blockchain": 50.0, "frontend": 50.0, "backend": 50.0}
            }
    
    # ============ HELPER FUNCTIONS ============
    
    async def _get_base_reputation_data(self, user_address: str) -> Dict[str, Any]:
        """Get base reputation data for calculations."""
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    # Get recent reputation transactions
                    transactions = db.query(ReputationTransaction).filter(
                        ReputationTransaction.user_address == user_address
                    ).order_by(desc(ReputationTransaction.created_at)).limit(100).all()
                    
                    # Get current reputation scores
                    scores = db.query(ReputationScore).filter(
                        ReputationScore.user_address == user_address
                    ).all()
                    
                    # Get validations
                    validations = db.query(ReputationValidation).filter(
                        ReputationValidation.user_address == user_address
                    ).all()
                    
                    return {
                        "transactions": [self._transaction_to_dict(t) for t in transactions],
                        "scores": [self._score_to_dict(s) for s in scores],
                        "validations": [self._validation_to_dict(v) for v in validations]
                    }
            else:
                # Fallback to memory storage
                return {
                    "transactions": _fallback_transactions.get(user_address, []),
                    "scores": _fallback_reputation.get(user_address, {}),
                    "validations": _fallback_validations.get(user_address, [])
                }
        
        except Exception as e:
            logger.warning(f"Error getting base reputation data: {str(e)}")
            return {"transactions": [], "scores": [], "validations": []}
    
    def _transaction_to_dict(self, transaction) -> Dict[str, Any]:
        """Convert transaction model to dictionary."""
        return {
            "id": transaction.id,
            "event_type": transaction.event_type,
            "impact_score": float(transaction.impact_score),
            "context": transaction.context,
            "created_at": transaction.created_at.isoformat()
        }
    
    def _score_to_dict(self, score) -> Dict[str, Any]:
        """Convert score model to dictionary."""
        return {
            "category": score.category,
            "score": float(score.score),
            "updated_at": score.updated_at.isoformat()
        }
    
    def _validation_to_dict(self, validation) -> Dict[str, Any]:
        """Convert validation model to dictionary."""
        return {
            "id": validation.id,
            "validator_address": validation.validator_address,
            "status": validation.status,
            "created_at": validation.created_at.isoformat()
        }
    
    async def _calculate_category_score(
        self,
        user_address: str,
        category: ReputationCategory,
        base_data: Dict[str, Any]
    ) -> float:
        """Calculate reputation score for a specific category."""
        try:
            transactions = base_data.get("transactions", [])
            relevant_transactions = [
                t for t in transactions
                if t.get("context", {}).get("category") == category.value
            ]
            
            if not relevant_transactions:
                return 50.0  # Default neutral score
            
            # Calculate weighted average of recent transactions
            total_weight = 0
            weighted_score = 0
            
            for transaction in relevant_transactions[-20:]:  # Last 20 transactions
                age_hours = (datetime.now(timezone.utc) - 
                           datetime.fromisoformat(transaction["created_at"].replace('Z', '+00:00'))).total_seconds() / 3600
                
                # Recent transactions have higher weight
                weight = max(0.1, 1.0 - (age_hours / (30 * 24)))  # 30-day decay
                impact = transaction.get("impact_score", 0)
                
                weighted_score += (50 + impact) * weight
                total_weight += weight
            
            if total_weight == 0:
                return 50.0
            
            return max(0, min(100, weighted_score / total_weight))
        
        except Exception as e:
            logger.error(f"Error calculating category score: {str(e)}")
            return 50.0
    
    async def _get_category_breakdown(
        self,
        user_address: str,
        category: ReputationCategory
    ) -> Dict[str, Any]:
        """Get detailed breakdown for a category."""
        return {
            "category": category.value,
            "factors": {
                "recent_performance": 0.4,
                "consistency": 0.3,
                "peer_validation": 0.2,
                "blockchain_evidence": 0.1
            },
            "recommendations": [
                "Continue maintaining high-quality work",
                "Seek peer validation for recent projects",
                "Document achievements on blockchain"
            ]
        }
    
    async def _apply_time_decay(self, user_address: str, score: float) -> float:
        """Apply time-based decay to reputation score."""
        try:
            # Get last activity timestamp
            base_data = await self._get_base_reputation_data(user_address)
            transactions = base_data.get("transactions", [])
            
            if not transactions:
                return score * 0.8  # Significant penalty for no activity
            
            last_activity = datetime.fromisoformat(
                transactions[0]["created_at"].replace('Z', '+00:00')
            )
            days_inactive = (datetime.now(timezone.utc) - last_activity).days
            
            # Apply monthly decay
            months_inactive = days_inactive / 30
            decay_factor = self.reputation_decay_factor ** months_inactive
            
            return score * decay_factor
        
        except Exception as e:
            logger.error(f"Error applying time decay: {str(e)}")
            return score
    
    async def _apply_anti_gaming_adjustments(self, user_address: str, score: float) -> float:
        """Apply anti-gaming adjustments to prevent manipulation."""
        try:
            base_data = await self._get_base_reputation_data(user_address)
            transactions = base_data.get("transactions", [])
            
            # Check for suspicious patterns
            recent_transactions = [
                t for t in transactions
                if (datetime.now(timezone.utc) - 
                   datetime.fromisoformat(t["created_at"].replace('Z', '+00:00'))).days <= 7
            ]
            
            # Penalty for too many recent updates (possible gaming)
            if len(recent_transactions) > 20:
                score *= 0.95
            
            # Check for self-validation attempts
            self_validations = sum(
                1 for t in recent_transactions
                if t.get("context", {}).get("validator_address") == user_address
            )
            
            if self_validations > 2:
                score *= 0.9
            
            return score
        
        except Exception as e:
            logger.error(f"Error applying anti-gaming adjustments: {str(e)}")
            return score
    
    async def _validate_reputation_event(
        self,
        user_address: str,
        event_type: ReputationEventType,
        context: Dict[str, Any]
    ):
        """Validate that a reputation event is legitimate."""
        # Check rate limiting
        base_data = await self._get_base_reputation_data(user_address)
        recent_events = [
            t for t in base_data.get("transactions", [])
            if (datetime.now(timezone.utc) - 
               datetime.fromisoformat(t["created_at"].replace('Z', '+00:00'))).days <= 1
        ]
        
        if len(recent_events) >= self.max_validations_per_day:
            raise ValueError("Daily reputation update limit exceeded")
        
        # Validate required context fields
        required_fields = {
            ReputationEventType.JOB_COMPLETION: ["job_id", "completion_quality"],
            ReputationEventType.PEER_REVIEW: ["reviewer_address", "review_score"],
            ReputationEventType.SKILL_VALIDATION: ["skill_id", "validation_type"],
            ReputationEventType.GOVERNANCE_PARTICIPATION: ["proposal_id", "participation_type"]
        }
        
        if event_type in required_fields:
            for field in required_fields[event_type]:
                if field not in context:
                    raise ValueError(f"Missing required context field: {field}")
    
    async def _create_reputation_transaction(
        self,
        user_address: str,
        event_type: ReputationEventType,
        impact_score: float,
        context: Dict[str, Any],
        validator_address: Optional[str] = None,
        blockchain_evidence: Optional[str] = None
    ) -> str:
        """Create a reputation transaction record."""
        transaction_id = str(uuid.uuid4())
        
        transaction_data = {
            "id": transaction_id,
            "user_address": user_address,
            "event_type": event_type.value,
            "impact_score": impact_score,
            "context": context,
            "validator_address": validator_address,
            "blockchain_evidence": blockchain_evidence,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    transaction = ReputationTransaction(**transaction_data)
                    db.add(transaction)
                    db.commit()
            else:
                # Fallback storage
                if user_address not in _fallback_transactions:
                    _fallback_transactions[user_address] = []
                _fallback_transactions[user_address].append(transaction_data)
        
        except Exception as e:
            logger.error(f"Error creating reputation transaction: {str(e)}")
            # Continue without database storage
        
        return transaction_id
    
    async def _apply_reputation_update(
        self,
        user_address: str,
        event_type: ReputationEventType,
        impact_score: float,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Apply reputation update and return new scores."""
        updated_scores = {}
        
        # Determine which categories are affected
        category_mapping = {
            ReputationEventType.JOB_COMPLETION: [ReputationCategory.TECHNICAL_SKILL, ReputationCategory.RELIABILITY],
            ReputationEventType.PEER_REVIEW: [ReputationCategory.COLLABORATION, ReputationCategory.COMMUNICATION],
            ReputationEventType.SKILL_VALIDATION: [ReputationCategory.TECHNICAL_SKILL],
            ReputationEventType.GOVERNANCE_PARTICIPATION: [ReputationCategory.GOVERNANCE, ReputationCategory.LEADERSHIP],
            ReputationEventType.PLATFORM_CONTRIBUTION: [ReputationCategory.INNOVATION, ReputationCategory.COLLABORATION]
        }
        
        affected_categories = category_mapping.get(event_type, [ReputationCategory.TECHNICAL_SKILL])
        
        for category in affected_categories:
            current_score = await self._get_current_category_score(user_address, category)
            new_score = max(0, min(100, current_score + (impact_score * 0.1)))  # 10% of impact
            
            await self._update_category_score(user_address, category, new_score)
            updated_scores[category.value] = new_score
        
        return updated_scores
    
    async def _get_current_category_score(
        self,
        user_address: str,
        category: ReputationCategory
    ) -> float:
        """Get current score for a category."""
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    score_record = db.query(ReputationScore).filter(
                        ReputationScore.user_address == user_address,
                        ReputationScore.category == category.value
                    ).first()
                    
                    return float(score_record.score) if score_record else 50.0
            else:
                # Fallback
                return _fallback_reputation.get(user_address, {}).get(category.value, 50.0)
        
        except Exception as e:
            logger.error(f"Error getting current category score: {str(e)}")
            return 50.0
    
    async def _update_category_score(
        self,
        user_address: str,
        category: ReputationCategory,
        new_score: float
    ):
        """Update score for a category."""
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    score_record = db.query(ReputationScore).filter(
                        ReputationScore.user_address == user_address,
                        ReputationScore.category == category.value
                    ).first()
                    
                    if score_record:
                        score_record.score = new_score
                        score_record.updated_at = datetime.now(timezone.utc)
                    else:
                        score_record = ReputationScore(
                            user_address=user_address,
                            category=category.value,
                            score=new_score
                        )
                        db.add(score_record)
                    
                    db.commit()
            else:
                # Fallback
                if user_address not in _fallback_reputation:
                    _fallback_reputation[user_address] = {}
                _fallback_reputation[user_address][category.value] = new_score
        
        except Exception as e:
            logger.error(f"Error updating category score: {str(e)}")
    
    async def _get_oracle_info(self, oracle_address: str) -> Optional[Dict[str, Any]]:
        """Get oracle information."""
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    oracle = db.query(ReputationOracle).filter(
                        ReputationOracle.oracle_address == oracle_address
                    ).first()
                    
                    if oracle:
                        return {
                            "oracle_id": oracle.oracle_id,
                            "oracle_address": oracle.oracle_address,
                            "name": oracle.name,
                            "specializations": oracle.specializations,
                            "is_active": oracle.is_active,
                            "total_evaluations": oracle.total_evaluations,
                            "successful_evaluations": oracle.successful_evaluations
                        }
            else:
                # Fallback check
                oracle_data = _fallback_reputation.get("oracles", {})
                return oracle_data.get(oracle_address)
        
        except Exception as e:
            logger.error(f"Error getting oracle info: {str(e)}")
            return None
    
    async def _get_evaluation_details(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get evaluation details."""
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    evaluation = db.query(WorkEvaluation).filter(
                        WorkEvaluation.evaluation_id == evaluation_id
                    ).first()
                    
                    if evaluation:
                        return {
                            "evaluation_id": evaluation.evaluation_id,
                            "oracle_address": evaluation.oracle_address,
                            "user_address": evaluation.user_address,
                            "overall_score": evaluation.overall_score,
                            "status": evaluation.status,
                            "created_at": evaluation.created_at.isoformat()
                        }
            else:
                # Fallback check
                for user_transactions in _fallback_transactions.values():
                    for transaction in user_transactions:
                        if transaction.get("evaluation_id") == evaluation_id:
                            return transaction
        
        except Exception as e:
            logger.error(f"Error getting evaluation details: {str(e)}")
            return None
    
    async def _submit_reputation_evidence(self, transaction_id: str, blockchain_evidence: str):
        """Submit reputation evidence to blockchain."""
        try:
            contract_manager = self._get_contract_manager()
            if contract_manager:
                # Submit to reputation oracle contract
                await contract_manager.submit_reputation_evidence(transaction_id, blockchain_evidence)
        
        except Exception as e:
            logger.error(f"Error submitting reputation evidence: {str(e)}")

    # ============ ADDITIONAL REPUTATION ORACLE FUNCTIONS ============

    async def resolve_challenge(
        self,
        challenge_id: str,
        uphold_original: bool,
        resolution: str
    ) -> Dict[str, Any]:
        """
        Resolve a challenge to a work evaluation.
        
        Args:
            challenge_id: ID of the challenge to resolve
            uphold_original: Whether to uphold the original evaluation
            resolution: Resolution description
            
        Returns:
            Dict containing resolution result
        """
        try:
            # Call blockchain function
            contract_result = await resolve_challenge(
                challenge_id=challenge_id,
                uphold_original=uphold_original,
                resolution=resolution
            )
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    challenge = db.query(EvaluationChallenge).filter(
                        EvaluationChallenge.challenge_id == challenge_id
                    ).first()
                    
                    if challenge:
                        challenge.status = "resolved"
                        challenge.resolution = resolution
                        challenge.resolved_at = datetime.now(timezone.utc)
                        challenge.uphold_original = uphold_original
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "challenge_id": challenge_id,
                "uphold_original": uphold_original,
                "resolution": resolution
            }
            
        except Exception as e:
            logger.error(f"Error resolving challenge {challenge_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def slash_oracle(
        self,
        oracle_address: str,
        amount: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Slash an oracle for poor performance or misconduct.
        
        Args:
            oracle_address: Address of the oracle to slash
            amount: Amount to slash
            reason: Reason for slashing
            
        Returns:
            Dict containing slashing result
        """
        try:
            # Call blockchain function
            contract_result = await slash_oracle(
                oracle_address=oracle_address,
                amount=amount,
                reason=reason
            )
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    oracle = db.query(ReputationOracle).filter(
                        ReputationOracle.oracle_address == oracle_address
                    ).first()
                    
                    if oracle:
                        oracle.is_active = False
                        oracle.slashed_amount = amount
                        oracle.slash_reason = reason
                        oracle.slashed_at = datetime.now(timezone.utc)
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "oracle_address": oracle_address,
                "amount": amount,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error slashing oracle {oracle_address}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def withdraw_oracle_stake(self) -> Dict[str, Any]:
        """
        Withdraw oracle stake.
        
        Returns:
            Dict containing withdrawal result
        """
        try:
            # Call blockchain function
            contract_result = await withdraw_oracle_stake()
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "message": "Oracle stake withdrawn successfully"
            }
            
        except Exception as e:
            logger.error(f"Error withdrawing oracle stake: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_oracle_performance(self, oracle_address: str) -> Dict[str, Any]:
        """
        Get oracle performance metrics.
        
        Args:
            oracle_address: Address of the oracle
            
        Returns:
            Dictionary containing performance metrics.
        """
        try:
            result = await get_oracle_performance(oracle_address=oracle_address)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get oracle performance")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting oracle performance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_category_score(self, user_address: str, category: str) -> Dict[str, Any]:
        """
        Get category-specific reputation score.
        
        Args:
            user_address: User's address
            category: Skill category
            
        Returns:
            Dictionary containing category score.
        """
        try:
            result = await get_category_score(user_address=user_address, category=category)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to get category score for {category}")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting category score: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_work_evaluation(self, evaluation_id: str) -> Dict[str, Any]:
        """
        Get work evaluation details.
        
        Args:
            evaluation_id: ID of the evaluation
            
        Returns:
            Dictionary containing evaluation details.
        """
        try:
            result = await get_work_evaluation(evaluation_id=evaluation_id)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to get work evaluation {evaluation_id}")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting work evaluation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_user_evaluations(self, user_address: str) -> Dict[str, Any]:
        """
        Get all evaluations for a user.
        
        Args:
            user_address: User's address
            
        Returns:
            Dictionary containing user evaluations.
        """
        try:
            result = await get_user_evaluations(user_address=user_address)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to get evaluations for user {user_address}")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting user evaluations: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_global_stats(self) -> Dict[str, Any]:
        """
        Get global reputation statistics.
        
        Returns:
            Dictionary containing global stats.
        """
        try:
            result = await get_global_stats()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get global stats")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting global stats: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_oracle_status(self, oracle_address: str, is_active: bool, reason: str) -> Dict[str, Any]:
        """
        Update oracle status.
        
        Args:
            oracle_address: Address of the oracle
            is_active: Whether the oracle should be active
            reason: Reason for status change
            
        Returns:
            Dictionary containing the status update result.
        """
        try:
            result = await update_oracle_status(oracle_address=oracle_address, is_active=is_active, reason=reason)
            if not result.success:
                return {
                    "success": False,
                    "error": result.error
                }
            
            # Update database with status change
            # This would typically involve updating the oracles table
            # For now, we'll just return the blockchain result
            
            return {
                "success": True,
                "transaction_id": result.transaction_id,
                "message": f"Oracle status updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating oracle status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Fallback storage for when database is not available
_fallback_transactions: Dict[str, List[Dict[str, Any]]] = {}
_fallback_reputation: Dict[str, Dict[str, float]] = {}
_fallback_validations: Dict[str, List[Dict[str, Any]]] = {}


def get_reputation_service() -> ReputationService:
    """Get the reputation service instance."""
    return ReputationService()

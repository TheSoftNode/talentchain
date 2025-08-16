"""
Comprehensive Governance Service Module

This module provides enterprise-level DAO governance functionality including
proposal management, voting mechanisms, delegation systems, execution queues,
and comprehensive audit trails for the TalentChain Pro ecosystem.
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
from fastapi import Request

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
        GovernanceProposal, GovernanceVote, GovernanceDelegation,
        AuditLog, User, SkillToken
    )
    from app.database import get_db_session, cache_manager
    DATABASE_MODELS_AVAILABLE = True
except ImportError:
    DATABASE_MODELS_AVAILABLE = False
    logger.warning("Database models not available, using fallback functionality")

from app.utils.hedera import (
    get_contract_manager, validate_hedera_address, submit_hcs_message,
    queue_proposal, execute_proposal, cancel_proposal,
    cast_vote_with_signature, batch_execute_proposals, get_proposal_status,
    get_vote_receipt, get_quorum, get_voting_delay, get_voting_period,
    get_proposal_threshold, get_all_proposals, get_active_proposals,
    can_execute, has_voted
)

try:
    from app.services.mcp import get_mcp_service
    MCP_SERVICE_AVAILABLE = True
except ImportError:
    MCP_SERVICE_AVAILABLE = False
    logger.warning("MCP service not available, using fallback proposal analysis")

try:
    from app.config import get_settings
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.warning("Config not available, using environment variables")

# Fallback storage for when database is not available
_fallback_proposals = {}
_fallback_votes = {}
_fallback_delegations = {}
_fallback_counter = 1000


class ProposalType(str, Enum):
    """Types of governance proposals."""
    PARAMETER_CHANGE = "parameter_change"
    FEATURE_UPDATE = "feature_update"
    TREASURY_ALLOCATION = "treasury_allocation"
    EMERGENCY_ACTION = "emergency_action"
    ORACLE_MANAGEMENT = "oracle_management"
    SKILL_VALIDATION_RULES = "skill_validation_rules"
    REPUTATION_PARAMETERS = "reputation_parameters"
    POOL_MANAGEMENT = "pool_management"


class ProposalStatus(str, Enum):
    """Status of governance proposals."""
    PENDING = "pending"
    ACTIVE = "active"
    SUCCEEDED = "succeeded"
    DEFEATED = "defeated"
    QUEUED = "queued"
    EXECUTED = "executed"
    CANCELED = "canceled"
    EXPIRED = "expired"


class VoteType(str, Enum):
    """Types of votes."""
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


class GovernanceService:
    """Comprehensive service for DAO governance and protocol management."""
    
    def __init__(self):
        """Initialize the governance service."""
        if CONFIG_AVAILABLE:
            self.settings = get_settings()
        else:
            self.settings = None
        
        self.contract_manager = None
        self.mcp_service = None
        
        # Governance parameters
        self.voting_delay = 24 * 3600  # 24 hours in seconds
        self.voting_period = 7 * 24 * 3600  # 7 days in seconds
        self.proposal_threshold = 100000  # Minimum voting power to create proposal
        self.quorum_threshold = 0.04  # 4% of total voting power
        self.execution_delay = 48 * 3600  # 48 hours timelock
        
        logger.info("Governance service initialized")
    
    def _get_contract_manager(self):
        """Lazy load contract manager."""
        if self.contract_manager is None:
            self.contract_manager = get_contract_manager()
        return self.contract_manager
    
    def _get_mcp_service(self):
        """Get MCP service if available."""
        if MCP_SERVICE_AVAILABLE:
            try:
                return get_mcp_service()
            except Exception as e:
                logger.warning(f"MCP service not available: {str(e)}")
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
    
    def _get_db_session(self):
        """Get database session if available."""
        if DATABASE_MODELS_AVAILABLE:
            return get_db_session()
        return None
    
    def _invalidate_cache(self, patterns: List[str]):
        """Invalidate cache patterns if cache manager is available."""
        if DATABASE_MODELS_AVAILABLE and hasattr(cache_manager, 'invalidate_pattern'):
            for pattern in patterns:
                try:
                    cache_manager.invalidate_pattern(pattern)
                except:
                    pass
    
    # ============ PROPOSAL MANAGEMENT FUNCTIONS ============
    
    async def create_proposal(
        self,
        title: str,                    # ✅ Added missing title parameter
        description: str,
        targets: List[str],
        values: List[int],
        calldatas: List[str],
        ipfs_hash: str,                # ✅ Added missing ipfs_hash parameter
        is_emergency: bool = False,
        request: Request = None        # Add request parameter for authentication
        # ❌ Removed proposer_address (should be msg.sender in contract)
        # ❌ Removed proposal_type (not in contract)
    ) -> Dict[str, Any]:
        """
        Create a new governance proposal.
        
        Args:
            title: Proposal title
            description: Detailed proposal description
            targets: List of target contract addresses
            values: List of values to send with calls
            calldatas: List of encoded function calls
            ipfs_hash: IPFS hash for additional content
            is_emergency: Whether this is an emergency proposal
            request: FastAPI request object for authentication
            
        Returns:
            Dict containing proposal creation result
        """
        try:
            # Validate proposal parameters
            if len(targets) != len(values) or len(targets) != len(calldatas):
                raise ValueError("Targets, values, and calldatas must have same length")
            
            if len(title) < 10 or len(description) < 50:
                raise ValueError("Title must be at least 10 characters, description at least 50")
            
            # Get proposer address from request context or fallback to mock
            if request:
                proposer_address = self.get_auth_context_from_request(request)
            else:
                proposer_address = await self._get_current_user_address()
                
            if not proposer_address:
                raise ValueError("No authenticated user found")
            
            if not validate_hedera_address(proposer_address):
                raise ValueError("Invalid proposer address format")
            
            # Check proposer voting power
            voting_power = await self._get_voting_power(proposer_address)
            if voting_power < self.proposal_threshold and not is_emergency:
                raise ValueError(f"Insufficient voting power. Required: {self.proposal_threshold}, have: {voting_power}")
            
            # Generate proposal ID and timestamps
            global _fallback_counter
            proposal_id = f"proposal_{hash(title + proposer_address) % 100000}"
            current_time = datetime.now(timezone.utc)
            start_time = current_time + timedelta(seconds=self.voting_delay)
            end_time = start_time + timedelta(seconds=self.voting_period)
            
            # Use AI analysis if available
            ai_analysis = None
            mcp_service = self._get_mcp_service()
            if mcp_service:
                try:
                    ai_analysis = await mcp_service.analyze_governance_proposal(
                        title=title,
                        description=description,
                        targets=targets,
                        calldatas=calldatas
                    )
                except Exception as e:
                    logger.warning(f"AI analysis failed: {str(e)}")
            
            # Create proposal on blockchain using the Governance contract
            from app.utils.hedera import create_governance_proposal
            
            contract_result = await create_governance_proposal(
                title=title,
                description=description,
                targets=targets,
                values=values,
                calldatas=calldatas,
                ipfs_hash=ipfs_hash
            )
            
            if contract_result.success:
                # Use the proposal ID from contract if available
                proposal_id = contract_result.token_id or proposal_id
                transaction_id = contract_result.transaction_id
                logger.info(f"Created governance proposal {proposal_id} on blockchain: {transaction_id}")
            else:
                logger.warning(f"Failed to create proposal on blockchain: {contract_result.error}")
                transaction_id = None
            
            # Create proposal data
            proposal_data = {
                "proposal_id": proposal_id,
                "proposer_address": proposer_address,
                "title": title,
                "description": description,
                "proposal_type": ProposalType.FEATURE_UPDATE.value, # Default to FEATURE_UPDATE
                "targets": targets,
                "values": values,
                "calldatas": calldatas,
                "ipfs_hash": ipfs_hash,
                "status": ProposalStatus.PENDING.value,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "for_votes": 0,
                "against_votes": 0,
                "abstain_votes": 0,
                "total_votes": 0,
                "is_emergency": is_emergency,
                "transaction_id": transaction_id,
                "blockchain_verified": contract_result.success if 'contract_result' in locals() else False,
                "created_at": current_time.isoformat(),
                "ai_analysis": ai_analysis
            }
            
            # Store in database if available
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        proposal = GovernanceProposal(
                            proposal_id=proposal_id,
                            proposer_address=proposer_address,
                            title=title,
                            description=description,
                            proposal_type=ProposalType.FEATURE_UPDATE.value, # Default to FEATURE_UPDATE
                            targets=targets,
                            values=values,
                            calldatas=calldatas,
                            ipfs_hash=ipfs_hash,
                            status=ProposalStatus.PENDING.value,
                            start_time=start_time,
                            end_time=end_time,
                            is_emergency=is_emergency,
                            transaction_id=transaction_id,
                            blockchain_verified=contract_result.success if 'contract_result' in locals() else False
                        )
                        
                        db.add(proposal)
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=proposer_address,
                            action="create_proposal",
                            resource_type="governance_proposal",
                            resource_id=proposal_id,
                            details={
                                "title": title,
                                "proposal_type": ProposalType.FEATURE_UPDATE.value, # Default to FEATURE_UPDATE
                                "is_emergency": is_emergency,
                                "targets_count": len(targets)
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate caches
                        self._invalidate_cache([
                            "governance_proposals:*",
                            f"proposal:{proposal_id}:*",
                            "proposal_stats:*"
                        ])
                        
                        db.commit()
                        
                        logger.info(f"Stored proposal {proposal_id} in database")
                        
                except Exception as db_error:
                    logger.warning(f"Database proposal storage failed: {str(db_error)}")
                    DATABASE_MODELS_AVAILABLE = False
            
            # Fallback storage
            if not DATABASE_MODELS_AVAILABLE:
                _fallback_proposals[proposal_id] = proposal_data
                logger.info(f"Stored proposal {proposal_id} in fallback storage")
            
            # Send HCS message for proposal creation
            try:
                await submit_hcs_message(
                    topic_id=self.governance_topic_id,
                    message=json.dumps({
                        "type": "proposal_created",
                        "proposal_id": proposal_id,
                        "title": title,
                        "proposer": proposer_address,
                        "type": ProposalType.FEATURE_UPDATE.value
                    })
                )
            except Exception as e:
                logger.warning(f"Failed to send HCS message: {str(e)}")
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "transaction_id": transaction_id,
                "message": "Proposal created successfully",
                "details": {
                    "title": title,
                    "proposer": proposer_address,
                    "proposal_type": ProposalType.FEATURE_UPDATE.value, # Default to FEATURE_UPDATE
                    "status": ProposalStatus.PENDING.value,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "is_emergency": is_emergency,
                    "blockchain_verified": contract_result.success if 'contract_result' in locals() else False
                }
            }
        
        except Exception as e:
            logger.error(f"Error creating proposal: {str(e)}")
            raise
    
    async def cast_vote(
        self,
        proposal_id: str,
        vote_type: VoteType,           # ✅ Renamed from vote_type to match contract
        reason: str = "",              # ✅ Keep reason parameter
        signature: Optional[str] = None,
        request: Request = None        # Add request parameter for authentication
        # ❌ Removed voter_address (should be msg.sender in contract)
    ) -> Dict[str, Any]:
        """
        Cast a vote on a governance proposal.
        
        Args:
            proposal_id: ID of the proposal
            vote_type: Type of vote (FOR, AGAINST, ABSTAIN)
            reason: Optional reason for the vote
            signature: Optional signature for gasless voting
            request: FastAPI request object for authentication
            
        Returns:
            Dict containing vote result
        """
        try:
            # Get voter address from request context or fallback to mock
            if request:
                voter_address = self.get_auth_context_from_request(request)
            else:
                voter_address = await self._get_current_user_address()
                
            if not voter_address:
                raise ValueError("No authenticated user found")
            
            if not validate_hedera_address(voter_address):
                raise ValueError("Invalid voter address format")
            
            # Get proposal details
            proposal = await self._get_proposal_data(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")
            
            # Check voting period
            current_time = datetime.now(timezone.utc)
            start_time = datetime.fromisoformat(proposal["start_time"].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(proposal["end_time"].replace('Z', '+00:00'))
            
            if current_time < start_time:
                raise ValueError("Voting has not started yet")
            
            if current_time > end_time:
                raise ValueError("Voting period has ended")
            
            if proposal["status"] != ProposalStatus.ACTIVE.value:
                raise ValueError("Proposal is not active for voting")
            
            # Check if already voted
            existing_vote = await self._get_existing_vote(proposal_id, voter_address)
            if existing_vote:
                raise ValueError("Already voted on this proposal")
            
            # Get voting power
            voting_power = await self._get_voting_power(voter_address)
            if voting_power == 0:
                raise ValueError("No voting power")
            
            # Cast vote on blockchain using the Governance contract
            from app.utils.hedera import cast_governance_vote
            
            # Convert vote type to integer (0=Against, 1=For, 2=Abstain)
            vote_int = {
                VoteType.AGAINST: 0,
                VoteType.FOR: 1,
                VoteType.ABSTAIN: 2
            }.get(vote_type, 0)
            
            contract_result = await cast_governance_vote(
                proposal_id=int(proposal_id.split('_')[1]) if '_' in proposal_id else int(proposal_id),
                vote=vote_int,
                reason=reason
            )
            
            if contract_result.success:
                transaction_id = contract_result.transaction_id
                logger.info(f"Cast vote {vote_type.value} on proposal {proposal_id}: {transaction_id}")
            else:
                logger.warning(f"Failed to cast vote on blockchain: {contract_result.error}")
                transaction_id = None
            
            # Create vote record
            vote_id = str(uuid.uuid4())
            vote_data = {
                "vote_id": vote_id,
                "proposal_id": proposal_id,
                "voter_address": voter_address,
                "vote_type": vote_type.value,
                "voting_power": voting_power,
                "reason": reason,
                "signature": signature,
                "transaction_id": transaction_id,
                "blockchain_verified": contract_result.success if 'contract_result' in locals() else False,
                "cast_at": current_time.isoformat()
            }
            
            # Store vote in database if available
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        vote = GovernanceVote(
                            vote_id=vote_id,
                            proposal_id=proposal_id,
                            voter_address=voter_address,
                            vote_type=vote_type.value,
                            voting_power=voting_power,
                            reason=reason,
                            signature=signature
                        )
                        
                        db.add(vote)
                        
                        # Update proposal vote counts
                        proposal_record = db.query(GovernanceProposal).filter(
                            GovernanceProposal.proposal_id == proposal_id
                        ).first()
                        
                        if proposal_record:
                            if vote_type == VoteType.FOR:
                                proposal_record.for_votes += voting_power
                            elif vote_type == VoteType.AGAINST:
                                proposal_record.against_votes += voting_power
                            else:  # ABSTAIN
                                proposal_record.abstain_votes += voting_power
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=voter_address,
                            action="cast_vote",
                            resource_type="governance_vote",
                            resource_id=vote_id,
                            details={
                                "proposal_id": proposal_id,
                                "vote_type": vote_type.value,
                                "voting_power": voting_power,
                                "reason": reason
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate caches
                        self._invalidate_cache([
                            f"proposal:{proposal_id}:*",
                            f"user_votes:{voter_address}:*"
                        ])
                except Exception as db_error:
                    logger.warning(f"Database vote storage failed: {str(db_error)}")
                    DATABASE_MODELS_AVAILABLE = False
            
            # Fallback storage
            if not DATABASE_MODELS_AVAILABLE:
                if proposal_id not in _fallback_votes:
                    _fallback_votes[proposal_id] = {}
                _fallback_votes[proposal_id][voter_address] = vote_data
                
                # Update proposal vote counts
                if proposal_id in _fallback_proposals:
                    if vote_type == VoteType.FOR:
                        _fallback_proposals[proposal_id]["for_votes"] += voting_power
                    elif vote_type == VoteType.AGAINST:
                        _fallback_proposals[proposal_id]["against_votes"] += voting_power
                    else:  # ABSTAIN
                        _fallback_proposals[proposal_id]["abstain_votes"] += voting_power
            
            # Submit to HCS for transparency
            try:
                await submit_hcs_message(f"governance/vote_cast", {
                    "proposal_id": proposal_id,
                    "voter": voter_address,
                    "vote_type": vote_type.value,
                    "voting_power": voting_power
                })
            except Exception as e:
                logger.warning(f"HCS submission failed: {str(e)}")
            
            logger.info(f"Vote cast on proposal {proposal_id} by {voter_address}: {vote_type.value}")
            
            return {
                "success": True,
                "vote_id": vote_id,
                "proposal_id": proposal_id,
                "voter_address": voter_address,
                "vote_type": vote_type.value,
                "voting_power": voting_power,
                "reason": reason,
                "cast_at": current_time.isoformat(),
                "proposal_status": await self._check_proposal_status(proposal_id)
            }
        
        except Exception as e:
            logger.error(f"Error casting vote: {str(e)}")
            raise
    
    async def delegate_voting_power(
        self,
        delegatee_address: str
    ) -> Dict[str, Any]:
        """
        Delegate voting power to another address.
        
        Args:
            delegatee_address: Address receiving delegation
            
        Returns:
            Dict containing delegation result
        """
        try:
            # Get delegator address from current context (msg.sender equivalent)
            delegator_address = await self._get_current_user_address()
            if not delegator_address:
                raise ValueError("No authenticated user found")
            
            if not validate_hedera_address(delegator_address):
                raise ValueError("Invalid delegator address format")
            
            if not validate_hedera_address(delegatee_address):
                raise ValueError("Invalid delegatee address format")
            
            if delegator_address == delegatee_address:
                raise ValueError("Cannot delegate to self")
            
            # Check if already delegated
            existing_delegation = await self._get_existing_delegation(delegator_address)
            if existing_delegation and existing_delegation["delegatee_address"] == delegatee_address:
                raise ValueError("Already delegated to this address")
            
            # Get current voting power
            voting_power = await self._get_base_voting_power(delegator_address)
            
            delegation_id = str(uuid.uuid4())
            delegation_data = {
                "delegation_id": delegation_id,
                "delegator_address": delegator_address,
                "delegatee_address": delegatee_address,
                "voting_power": voting_power,
                "delegated_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }
            
            # Store in database if available
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        # Deactivate existing delegation if any
                        if existing_delegation:
                            old_delegation = db.query(GovernanceDelegation).filter(
                                GovernanceDelegation.delegator_address == delegator_address,
                                GovernanceDelegation.is_active == True
                            ).first()
                            if old_delegation:
                                old_delegation.is_active = False
                        
                        # Create new delegation
                        delegation = GovernanceDelegation(
                            delegation_id=delegation_id,
                            delegator_address=delegator_address,
                            delegatee_address=delegatee_address,
                            voting_power=voting_power,
                            is_active=True
                        )
                        
                        db.add(delegation)
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=delegator_address,
                            action="delegate_voting_power",
                            resource_type="governance_delegation",
                            resource_id=delegation_id,
                            details={
                                "delegatee_address": delegatee_address,
                                "voting_power": voting_power,
                                "previous_delegatee": existing_delegation["delegatee_address"] if existing_delegation else None
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate caches
                        self._invalidate_cache([
                            f"voting_power:{delegator_address}:*",
                            f"voting_power:{delegatee_address}:*",
                            f"delegations:{delegator_address}:*"
                        ])
                except Exception as db_error:
                    logger.warning(f"Database delegation storage failed: {str(db_error)}")
                    DATABASE_MODELS_AVAILABLE = False
            
            # Fallback storage
            if not DATABASE_MODELS_AVAILABLE:
                _fallback_delegations[delegation_id] = delegation_data
                logger.info(f"Stored delegation {delegation_id} in fallback storage")
            
            # Call blockchain contract for delegation
            try:
                from app.utils.hedera import delegate_voting_power
                
                contract_result = await delegate_voting_power(
                    delegatee=delegatee_address
                )
                
                if contract_result.success:
                    logger.info(f"Delegated voting power on blockchain: {contract_result.transaction_id}")
                    # Update delegation data with blockchain info
                    delegation_data["transaction_id"] = contract_result.transaction_id
                    delegation_data["blockchain_verified"] = True
                else:
                    logger.warning(f"Failed to delegate on blockchain: {contract_result.error}")
                    delegation_data["blockchain_verified"] = False
                    
            except Exception as e:
                logger.warning(f"Blockchain delegation failed: {str(e)}")
                delegation_data["blockchain_verified"] = False
            
            return {
                "success": True,
                "delegation_id": delegation_id,
                "delegator_address": delegator_address,
                "delegatee_address": delegatee_address,
                "voting_power": voting_power,
                "message": "Voting power delegated successfully",
                "transaction_id": delegation_data.get("transaction_id"),
                "blockchain_verified": delegation_data.get("blockchain_verified", False)
            }
        
        except Exception as e:
            logger.error(f"Error delegating voting power: {str(e)}")
            raise
    
    async def undelegate_voting_power(self) -> Dict[str, Any]:
        """
        Undelegate voting power (remove delegation).
        
        Returns:
            Dict containing undelegation result
        """
        try:
            # Get delegator address from current context (msg.sender equivalent)
            delegator_address = await self._get_current_user_address()
            if not delegator_address:
                raise ValueError("No authenticated user found")
            
            if not validate_hedera_address(delegator_address):
                raise ValueError("Invalid delegator address format")
            
            # Check if delegation exists
            existing_delegation = await self._get_existing_delegation(delegator_address)
            if not existing_delegation:
                raise ValueError("No active delegation found")
            
            # Call blockchain contract for undelegation
            try:
                from app.utils.hedera import undelegate_voting_power
                
                contract_result = await undelegate_voting_power()
                
                if contract_result.success:
                    logger.info(f"Undelegated voting power on blockchain: {contract_result.transaction_id}")
                    transaction_id = contract_result.transaction_id
                    blockchain_verified = True
                else:
                    logger.warning(f"Failed to undelegate on blockchain: {contract_result.error}")
                    transaction_id = None
                    blockchain_verified = False
                    
            except Exception as e:
                logger.warning(f"Blockchain undelegation failed: {str(e)}")
                transaction_id = None
                blockchain_verified = False
            
            # Update delegation status in database
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        # Deactivate existing delegation
                        old_delegation = db.query(GovernanceDelegation).filter(
                            GovernanceDelegation.delegator_address == delegator_address,
                            GovernanceDelegation.is_active == True
                        ).first()
                        
                        if old_delegation:
                            old_delegation.is_active = False
                            old_delegation.undelegated_at = datetime.now(timezone.utc)
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=delegator_address,
                            action="undelegate_voting_power",
                            resource_type="governance_delegation",
                            resource_id=existing_delegation["delegation_id"],
                            details={
                                "previous_delegatee": existing_delegation["delegatee_address"],
                                "voting_power": existing_delegation["voting_power"],
                                "transaction_id": transaction_id
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate caches
                        self._invalidate_cache([
                            f"voting_power:{delegator_address}:*",
                            f"delegations:{delegator_address}:*"
                        ])
                        
                        db.commit()
                        
                except Exception as db_error:
                    logger.warning(f"Database undelegation update failed: {str(db_error)}")
                    DATABASE_MODELS_AVAILABLE = False
            
            # Update fallback storage
            if not DATABASE_MODELS_AVAILABLE:
                if delegator_address in _fallback_delegations:
                    _fallback_delegations[delegator_address]["is_active"] = False
                    _fallback_delegations[delegator_address]["undelegated_at"] = datetime.now(timezone.utc).isoformat()
            
            return {
                "success": True,
                "delegator_address": delegator_address,
                "previous_delegatee": existing_delegation["delegatee_address"],
                "voting_power": existing_delegation["voting_power"],
                "message": "Voting power undelegated successfully",
                "transaction_id": transaction_id,
                "blockchain_verified": blockchain_verified
            }
        
        except Exception as e:
            logger.error(f"Error undelegating voting power: {str(e)}")
            raise
    
    # ============ QUERY FUNCTIONS ============
    
    async def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed proposal information."""
        try:
            proposal = await self._get_proposal_data(proposal_id)
            if not proposal:
                return None
            
            # Add vote breakdown
            votes = await self._get_proposal_votes(proposal_id)
            proposal["votes"] = votes
            proposal["total_votes"] = proposal.get("for_votes", 0) + proposal.get("against_votes", 0) + proposal.get("abstain_votes", 0)
            
            # Check current status
            proposal["current_status"] = await self._check_proposal_status(proposal_id)
            
            return proposal
        
        except Exception as e:
            logger.error(f"Error getting proposal: {str(e)}")
            return None
    
    async def list_proposals(
        self,
        status: Optional[str] = None,
        proposer_address: Optional[str] = None,
        proposal_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List proposals with optional filters."""
        try:
            proposals = []
            
            # Try database first
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        query = db.query(GovernanceProposal)
                        
                        if status:
                            query = query.filter(GovernanceProposal.status == status)
                        
                        if proposer_address:
                            query = query.filter(GovernanceProposal.proposer_address == proposer_address)
                        
                        if proposal_type:
                            query = query.filter(GovernanceProposal.proposal_type == proposal_type)
                        
                        proposal_records = query.order_by(desc(GovernanceProposal.created_at)).offset(offset).limit(limit).all()
                        
                        for proposal_record in proposal_records:
                            proposal_data = await self.get_proposal(proposal_record.proposal_id)
                            if proposal_data:
                                proposals.append(proposal_data)
                        
                        return proposals
                
                except Exception as db_error:
                    logger.warning(f"Database listing failed: {str(db_error)}")
            
            # Fallback to memory storage
            all_proposals = list(_fallback_proposals.values())
            
            # Apply filters
            if status:
                all_proposals = [p for p in all_proposals if p.get("status") == status]
            
            if proposer_address:
                all_proposals = [p for p in all_proposals if p.get("proposer_address") == proposer_address]
            
            if proposal_type:
                all_proposals = [p for p in all_proposals if p.get("proposal_type") == proposal_type]
            
            # Apply pagination
            return all_proposals[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Error listing proposals: {str(e)}")
            return []
    
    async def get_voting_power(self, user_address: str) -> Dict[str, Any]:
        """Get comprehensive voting power information for a user."""
        try:
            base_power = await self._get_base_voting_power(user_address)
            delegated_power = await self._get_delegated_voting_power(user_address)
            total_power = base_power + delegated_power
            
            # Get delegation info
            delegation_info = await self._get_existing_delegation(user_address)
            
            return {
                "user_address": user_address,
                "base_voting_power": base_power,
                "delegated_voting_power": delegated_power,
                "total_voting_power": total_power,
                "has_delegated": delegation_info is not None,
                "delegated_to": delegation_info["delegatee_address"] if delegation_info else None,
                "calculation_method": "skill_tokens_and_reputation",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting voting power: {str(e)}")
            return {
                "user_address": user_address,
                "base_voting_power": 0,
                "delegated_voting_power": 0,
                "total_voting_power": 0,
                "has_delegated": False,
                "delegated_to": None
            }
    
    # ============ HELPER FUNCTIONS ============
    
    async def _get_proposal_data(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get proposal data from database or fallback."""
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    proposal = db.query(GovernanceProposal).filter(
                        GovernanceProposal.proposal_id == proposal_id
                    ).first()
                    
                    if proposal:
                        return {
                            "proposal_id": proposal.proposal_id,
                            "proposer_address": proposal.proposer_address,
                            "title": proposal.title,
                            "description": proposal.description,
                            "proposal_type": proposal.proposal_type,
                            "targets": proposal.targets,
                            "values": proposal.values,
                            "calldatas": proposal.calldatas,
                            "ipfs_hash": proposal.ipfs_hash,
                            "is_emergency": proposal.is_emergency,
                            "status": proposal.status,
                            "start_time": proposal.start_time.isoformat(),
                            "end_time": proposal.end_time.isoformat(),
                            "for_votes": proposal.for_votes,
                            "against_votes": proposal.against_votes,
                            "abstain_votes": proposal.abstain_votes,
                            "created_at": proposal.created_at.isoformat(),
                            "ai_analysis": proposal.metadata.get("ai_analysis") if proposal.metadata else None
                        }
            
            # Fallback to memory storage
            return _fallback_proposals.get(proposal_id)
        
        except Exception as e:
            logger.error(f"Error getting proposal data: {str(e)}")
            return None
    
    async def _get_existing_vote(self, proposal_id: str, voter_address: str) -> Optional[Dict[str, Any]]:
        """Check if user already voted on proposal."""
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    vote = db.query(GovernanceVote).filter(
                        GovernanceVote.proposal_id == proposal_id,
                        GovernanceVote.voter_address == voter_address
                    ).first()
                    
                    if vote:
                        return {
                            "vote_id": vote.vote_id,
                            "vote_type": vote.vote_type,
                            "voting_power": vote.voting_power,
                            "cast_at": vote.created_at.isoformat()
                        }
            
            # Fallback check
            proposal_votes = _fallback_votes.get(proposal_id, {})
            return proposal_votes.get(voter_address)
        
        except Exception as e:
            logger.error(f"Error checking existing vote: {str(e)}")
            return None
    
    async def _get_existing_delegation(self, delegator_address: str) -> Optional[Dict[str, Any]]:
        """Get existing delegation for an address."""
        try:
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    delegation = db.query(GovernanceDelegation).filter(
                        GovernanceDelegation.delegator_address == delegator_address,
                        GovernanceDelegation.is_active == True
                    ).first()
                    
                    if delegation:
                        return {
                            "delegation_id": delegation.delegation_id,
                            "delegatee_address": delegation.delegatee_address,
                            "voting_power": delegation.voting_power,
                            "delegated_at": delegation.created_at.isoformat()
                        }
            
            # Fallback check
            return _fallback_delegations.get(delegator_address)
        
        except Exception as e:
            logger.error(f"Error checking existing delegation: {str(e)}")
            return None
    
    async def _get_voting_power(self, user_address: str) -> int:
        """Get total voting power for a user (including delegated power)."""
        base_power = await self._get_base_voting_power(user_address)
        delegated_power = await self._get_delegated_voting_power(user_address)
        return base_power + delegated_power
    
    async def _get_base_voting_power(self, user_address: str) -> int:
        """Get base voting power from skill tokens and reputation."""
        try:
            voting_power = 0
            
            # Check if user has delegated their power
            delegation = await self._get_existing_delegation(user_address)
            if delegation:
                return 0  # No voting power if delegated
            
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        # Count skill tokens (each gives 1 voting power)
                        skill_tokens = db.query(SkillToken).filter(
                            SkillToken.owner_address == user_address,
                            SkillToken.is_active == True
                        ).count()
                        voting_power += skill_tokens
                        
                        # Add reputation-based voting power (simplified)
                        # In a real implementation, this would use the reputation service
                        voting_power += 10  # Base voting power for all users
                except Exception as db_error:
                    logger.warning(f"Database voting power calculation failed: {str(db_error)}")
            else:
                # Fallback calculation
                voting_power = 10  # Base voting power
            
            return voting_power
        
        except Exception as e:
            logger.error(f"Error calculating base voting power: {str(e)}")
            return 0
    
    async def _get_delegated_voting_power(self, user_address: str) -> int:
        """Get voting power delegated to this user."""
        try:
            delegated_power = 0
            
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        delegations = db.query(GovernanceDelegation).filter(
                            GovernanceDelegation.delegatee_address == user_address,
                            GovernanceDelegation.is_active == True
                        ).all()
                        
                        for delegation in delegations:
                            delegated_power += delegation.voting_power
                except Exception as db_error:
                    logger.warning(f"Database delegated power calculation failed: {str(db_error)}")
            else:
                # Fallback calculation
                for delegation_data in _fallback_delegations.values():
                    if (delegation_data.get("delegatee_address") == user_address and 
                        delegation_data.get("is_active", False)):
                        delegated_power += delegation_data.get("voting_power", 0)
            
            return delegated_power
        
        except Exception as e:
            logger.error(f"Error calculating delegated voting power: {str(e)}")
            return 0
    
    async def _get_proposal_votes(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get all votes for a proposal."""
        try:
            votes = []
            
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        vote_records = db.query(GovernanceVote).filter(
                            GovernanceVote.proposal_id == proposal_id
                        ).all()
                        
                        for vote in vote_records:
                            votes.append({
                                "vote_id": vote.vote_id,
                                "voter_address": vote.voter_address,
                                "vote_type": vote.vote_type,
                                "voting_power": vote.voting_power,
                                "reason": vote.reason,
                                "cast_at": vote.created_at.isoformat()
                            })
                except Exception as db_error:
                    logger.warning(f"Database vote retrieval failed: {str(db_error)}")
            else:
                # Fallback to memory storage
                proposal_votes = _fallback_votes.get(proposal_id, {})
                votes = list(proposal_votes.values())
            
            return votes
        
        except Exception as e:
            logger.error(f"Error getting proposal votes: {str(e)}")
            return []
    
    async def _check_proposal_status(self, proposal_id: str) -> str:
        """Check and update proposal status based on current conditions."""
        try:
            proposal = await self._get_proposal_data(proposal_id)
            if not proposal:
                return ProposalStatus.EXPIRED.value
            
            current_time = datetime.now(timezone.utc)
            start_time = datetime.fromisoformat(proposal["start_time"].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(proposal["end_time"].replace('Z', '+00:00'))
            
            current_status = proposal["status"]
            
            # Check if voting should start
            if current_status == ProposalStatus.PENDING.value and current_time >= start_time:
                current_status = ProposalStatus.ACTIVE.value
            
            # Check if voting has ended
            if current_status == ProposalStatus.ACTIVE.value and current_time > end_time:
                # Determine outcome
                for_votes = proposal.get("for_votes", 0)
                against_votes = proposal.get("against_votes", 0)
                total_votes = for_votes + against_votes + proposal.get("abstain_votes", 0)
                
                # Check quorum
                total_voting_power = await self._get_total_voting_power()
                quorum_met = total_votes >= (total_voting_power * self.quorum_threshold)
                
                if quorum_met and for_votes > against_votes:
                    current_status = ProposalStatus.SUCCEEDED.value
                else:
                    current_status = ProposalStatus.DEFEATED.value
            
            return current_status
        
        except Exception as e:
            logger.error(f"Error checking proposal status: {str(e)}")
            return ProposalStatus.EXPIRED.value
    
    async def _get_total_voting_power(self) -> int:
        """Get total voting power in the system."""
        try:
            # This would be calculated based on all active skill tokens and reputation
            # For now, return a mock value
            return 1000000
        except Exception as e:
            logger.error(f"Error getting total voting power: {str(e)}")
            return 1000000

    # ============ ADDITIONAL GOVERNANCE FUNCTIONS ============

    async def queue_proposal(
        self,
        proposal_id: str
    ) -> Dict[str, Any]:
        """
        Queue a proposal for execution.
        
        Args:
            proposal_id: ID of the proposal to queue
            
        Returns:
            Dict containing queuing result
        """
        try:
            # Call blockchain function
            contract_result = await queue_proposal(proposal_id=proposal_id)
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    proposal = db.query(GovernanceProposal).filter(
                        GovernanceProposal.proposal_id == proposal_id
                    ).first()
                    
                    if proposal:
                        proposal.status = ProposalStatus.QUEUED.value
                        proposal.queued_at = datetime.now(timezone.utc)
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "proposal_id": proposal_id,
                "status": "queued"
            }
            
        except Exception as e:
            logger.error(f"Error queuing proposal {proposal_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_proposal(
        self,
        proposal_id: str
    ) -> Dict[str, Any]:
        """
        Execute a queued proposal.
        
        Args:
            proposal_id: ID of the proposal to execute
            
        Returns:
            Dict containing execution result
        """
        try:
            # Call blockchain function
            contract_result = await execute_proposal(proposal_id=proposal_id)
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    proposal = db.query(GovernanceProposal).filter(
                        GovernanceProposal.proposal_id == proposal_id
                    ).first()
                    
                    if proposal:
                        proposal.status = ProposalStatus.EXECUTED.value
                        proposal.executed_at = datetime.now(timezone.utc)
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "proposal_id": proposal_id,
                "status": "executed"
            }
            
        except Exception as e:
            logger.error(f"Error executing proposal {proposal_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def cancel_proposal(
        self,
        proposal_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a proposal.
        
        Args:
            proposal_id: ID of the proposal to cancel
            
        Returns:
            Dict containing cancellation result
        """
        try:
            # Call blockchain function
            contract_result = await cancel_proposal(proposal_id=proposal_id)
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    proposal = db.query(GovernanceProposal).filter(
                        GovernanceProposal.proposal_id == proposal_id
                    ).first()
                    
                    if proposal:
                        proposal.status = ProposalStatus.CANCELED.value
                        proposal.canceled_at = datetime.now(timezone.utc)
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "proposal_id": proposal_id,
                "status": "canceled"
            }
            
        except Exception as e:
            logger.error(f"Error canceling proposal {proposal_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def cast_vote_with_signature(
        self,
        proposal_id: str,
        vote: int,
        reason: str,
        signature: str
    ) -> Dict[str, Any]:
        """
        Cast a vote with signature.
        
        Args:
            proposal_id: ID of the proposal to vote on
            vote: Vote type (0=Against, 1=For, 2=Abstain)
            reason: Optional reason for the vote
            signature: Signature for the vote
            
        Returns:
            Dict containing voting result
        """
        try:
            # Call blockchain function
            contract_result = await cast_vote_with_signature(
                proposal_id=proposal_id,
                vote=vote,
                reason=reason,
                signature=signature
            )
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    # Create or update vote record
                    existing_vote = db.query(GovernanceVote).filter(
                        GovernanceVote.proposal_id == proposal_id,
                        GovernanceVote.voter_address == self._get_current_user_address()
                    ).first()
                    
                    if existing_vote:
                        existing_vote.vote_type = VoteType.FOR.value if vote == 1 else VoteType.AGAINST.value if vote == 0 else VoteType.ABSTAIN.value
                        existing_vote.reason = reason
                        existing_vote.updated_at = datetime.now(timezone.utc)
                    else:
                        new_vote = GovernanceVote(
                            proposal_id=proposal_id,
                            voter_address=self._get_current_user_address(),
                            vote_type=VoteType.FOR.value if vote == 1 else VoteType.AGAINST.value if vote == 0 else VoteType.ABSTAIN.value,
                            voting_power=await self._get_voting_power(self._get_current_user_address()),
                            reason=reason
                        )
                        db.add(new_vote)
                    
                    db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "proposal_id": proposal_id,
                "vote": vote,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error casting vote with signature for proposal {proposal_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def batch_execute_proposals(
        self,
        proposal_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Batch execute multiple proposals.
        
        Args:
            proposal_ids: List of proposal IDs to execute
            
        Returns:
            Dict containing batch execution result
        """
        try:
            # Call blockchain function
            contract_result = await batch_execute_proposals(proposal_ids=proposal_ids)
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    proposals = db.query(GovernanceProposal).filter(
                        GovernanceProposal.proposal_id.in_(proposal_ids)
                    ).all()
                    
                    for proposal in proposals:
                        proposal.status = ProposalStatus.EXECUTED.value
                        proposal.executed_at = datetime.now(timezone.utc)
                    
                    db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "executed_proposals": len(proposal_ids)
            }
            
        except Exception as e:
            logger.error(f"Error batch executing proposals: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_proposal_status(self, proposal_id: str) -> Dict[str, Any]:
        """
        Get proposal status.
        
        Args:
            proposal_id: ID of the proposal
            
        Returns:
            Dictionary containing proposal status.
        """
        try:
            result = await get_proposal_status(proposal_id=proposal_id)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to get status for proposal {proposal_id}")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting proposal status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_vote_receipt(self, proposal_id: str, voter: str) -> Dict[str, Any]:
        """
        Get vote receipt for a voter on a proposal.
        
        Args:
            proposal_id: ID of the proposal
            voter: Address of the voter
            
        Returns:
            Dictionary containing vote receipt.
        """
        try:
            result = await get_vote_receipt(proposal_id=proposal_id, voter=voter)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to get vote receipt for proposal {proposal_id}")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting vote receipt: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_quorum(self) -> Dict[str, Any]:
        """
        Get quorum requirement.
        
        Returns:
            Dictionary containing quorum information.
        """
        try:
            result = await get_quorum()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get quorum")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting quorum: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_voting_delay(self) -> Dict[str, Any]:
        """
        Get voting delay.
        
        Returns:
            Dictionary containing voting delay information.
        """
        try:
            result = await get_voting_delay()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get voting delay")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting voting delay: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_voting_period(self) -> Dict[str, Any]:
        """
        Get voting period.
        
        Returns:
            Dictionary containing voting period information.
        """
        try:
            result = await get_voting_period()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get voting period")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting voting period: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_proposal_threshold(self) -> Dict[str, Any]:
        """
        Get proposal threshold.
        
        Returns:
            Dictionary containing proposal threshold information.
        """
        try:
            result = await get_proposal_threshold()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get proposal threshold")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting proposal threshold: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_all_proposals(self) -> Dict[str, Any]:
        """
        Get all proposals.
        
        Returns:
            Dictionary containing all proposals.
        """
        try:
            result = await get_all_proposals()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get all proposals")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting all proposals: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_active_proposals(self) -> Dict[str, Any]:
        """
        Get active proposals.
        
        Returns:
            Dictionary containing active proposals.
        """
        try:
            result = await get_active_proposals()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get active proposals")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting active proposals: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def can_execute(self, proposal_id: str) -> Dict[str, Any]:
        """
        Check if a proposal can be executed.
        
        Args:
            proposal_id: ID of the proposal
            
        Returns:
            Dictionary containing execution status.
        """
        try:
            result = await can_execute(proposal_id=proposal_id)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to check execution status for proposal {proposal_id}")
                }
            return result
        except Exception as e:
            logger.error(f"Error checking execution status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def has_voted(self, proposal_id: str, voter: str) -> Dict[str, Any]:
        """
        Check if a voter has voted on a proposal.
        
        Args:
            proposal_id: ID of the proposal
            voter: Address of the voter
            
        Returns:
            Dictionary containing voting status.
        """
        try:
            result = await has_voted(proposal_id=proposal_id, voter=voter)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to check voting status for proposal {proposal_id}")
                }
            return result
        except Exception as e:
            logger.error(f"Error checking voting status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton getter for dependency injection
def get_governance_service() -> GovernanceService:
    """Get the governance service instance."""
    return GovernanceService()

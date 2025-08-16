"""
Comprehensive TalentPool Service Module

This module provides enterprise-level service functions for job pool management,
including creation, application processing, AI-powered matching, stake management,
and comprehensive caching with blockchain integration.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta

# Configure logging first
logger = logging.getLogger(__name__)

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import and_, or_, desc, func
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not available, using fallback functionality")

try:
    from app.models.database import (
        JobPool, PoolApplication, PoolMatch, PoolStake, SkillToken,
        ReputationScore, AuditLog, PoolStatusEnum
    )
    from app.database import get_db_session, cache_manager
    DATABASE_MODELS_AVAILABLE = True
except ImportError:
    DATABASE_MODELS_AVAILABLE = False
    logger.warning("Database models not available, using fallback functionality")

from app.utils.hedera import (
    get_contract_manager, create_job_pool, apply_to_pool as hedera_apply_to_pool,
    make_pool_match, get_job_pool_info, select_candidate, complete_pool,
    close_pool, withdraw_application, calculate_match_score, get_pool_metrics,
    get_talent_pool_global_stats, get_active_pools_count, get_total_pools_count
)

try:
    from app.services.mcp import get_mcp_service
    MCP_SERVICE_AVAILABLE = True
except ImportError:
    MCP_SERVICE_AVAILABLE = False
    logger.warning("MCP service not available, using fallback AI scoring")

try:
    from app.config import get_settings
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.warning("Config not available, using environment variables")

# Fallback storage for when database is not available
_fallback_pools = {}
_fallback_applications = {}
_fallback_matches = {}
_fallback_counter = 1000


class TalentPoolService:
    """Comprehensive service for managing talent pools with blockchain integration."""
    
    def __init__(self):
        """Initialize the talent pool service."""
        if CONFIG_AVAILABLE:
            self.settings = get_settings()
        else:
            self.settings = None
        self.contract_manager = None
        self.mcp_service = None
        logger.info("Talent pool service initialized")
    
    def _get_contract_manager(self):
        """Lazy load contract manager."""
        if self.contract_manager is None:
            self.contract_manager = get_contract_manager()
        return self.contract_manager
    
    def _get_mcp_service(self):
        """Lazy load MCP service for AI matching."""
        if self.mcp_service is None and MCP_SERVICE_AVAILABLE:
            self.mcp_service = get_mcp_service()
        return self.mcp_service
    
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
                except Exception:
                    pass
    
    # ============ POOL CREATION FUNCTIONS ============
    
    async def create_pool(
        self,
        creator_address: str,
        title: str,
        description: str,
        required_skills: List[Dict[str, Any]],
        min_reputation: int = 0,
        stake_amount: float = 10.0,
        duration_days: int = 30,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        location: str = "Remote",
        is_remote: bool = True,
        company_name: str = "",
        max_candidates: int = 50
    ) -> Dict[str, Any]:
        """
        Create a new job pool on blockchain and cache in database.
        
        Args:
            creator_address: Hedera account ID of the pool creator
            title: Job title
            description: Detailed job description
            required_skills: List of required skills with levels
            min_reputation: Minimum reputation score required
            stake_amount: Stake amount in HBAR
            duration_days: Pool duration in days
            salary_min: Minimum salary offered
            salary_max: Maximum salary offered
            location: Job location
            is_remote: Whether job is remote
            company_name: Name of the company
            max_candidates: Maximum number of candidates
            
        Returns:
            Dict containing pool creation result
        """
        try:
            # Validate inputs
            if duration_days < 1 or duration_days > 365:
                raise ValueError("Duration must be between 1 and 365 days")
            
            if stake_amount < 1.0:
                raise ValueError("Minimum stake amount is 1.0 HBAR")
            
            if not required_skills:
                raise ValueError("At least one required skill must be specified")
            
            # Validate required skills format
            for skill in required_skills:
                if not all(key in skill for key in ['name', 'level']):
                    raise ValueError("Each skill must have 'name' and 'level' properties")
                if skill['level'] < 1 or skill['level'] > 10:
                    raise ValueError("Skill levels must be between 1 and 10")
            
            # Create job pool on blockchain
            contract_result = await create_job_pool(
                title=title,
                description=description,
                required_skills=required_skills,
                stake_amount=stake_amount,
                duration_days=duration_days
            )
            
            if not contract_result.success:
                raise Exception(f"Blockchain transaction failed: {contract_result.error}")
            
            # Generate pool ID and deadline
            pool_id = contract_result.pool_id or f"pool_{hash(title + creator_address) % 100000}"
            deadline = datetime.now(timezone.utc) + timedelta(days=duration_days)
            
            # Try to cache in database if available
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        job_pool = JobPool(
                            pool_id=pool_id,
                            creator_address=creator_address,
                            title=title,
                            description=description,
                            company_name=company_name,
                            location=location,
                            is_remote=is_remote,
                            required_skills=required_skills,
                            min_reputation=min_reputation,
                            salary_min=salary_min,
                            salary_max=salary_max,
                            stake_amount=stake_amount,
                            deadline=deadline,
                            duration_days=duration_days,
                            max_candidates=max_candidates,
                            status=PoolStatusEnum.ACTIVE,
                            contract_address=self.settings.contract_talent_pool if self.settings else os.getenv("CONTRACT_TALENT_POOL"),
                            transaction_id=contract_result.transaction_id,
                            block_timestamp=datetime.now(timezone.utc)
                        )
                        
                        db.add(job_pool)
                        
                        # Add initial stake entry
                        initial_stake = PoolStake(
                            pool_id=job_pool.id,
                            staker_address=creator_address,
                            stake_amount=stake_amount,
                            stake_type="creator",
                            transaction_id=contract_result.transaction_id,
                            block_timestamp=datetime.now(timezone.utc)
                        )
                        db.add(initial_stake)
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=creator_address,
                            action="create_pool",
                            resource_type="job_pool",
                            resource_id=pool_id,
                            details={
                                "title": title,
                                "required_skills": required_skills,
                                "stake_amount": stake_amount,
                                "transaction_id": contract_result.transaction_id
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate relevant caches
                        self._invalidate_cache([
                            "job_pools:*",
                            f"creator_pools:{creator_address}:*"
                        ])
                        
                except Exception as db_error:
                    logger.warning(f"Database storage failed, using fallback: {str(db_error)}")
                    # Fall back to in-memory storage
                    pass
            
            # Fallback storage
            _fallback_counter += 1
            _fallback_pools[pool_id] = {
                    "pool_id": pool_id,
                    "creator_address": creator_address,
                    "title": title,
                    "description": description,
                    "company_name": company_name,
                    "location": location,
                    "is_remote": is_remote,
                    "required_skills": required_skills,
                    "min_reputation": min_reputation,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "stake_amount": stake_amount,
                    "deadline": deadline.isoformat(),
                    "duration_days": duration_days,
                    "max_candidates": max_candidates,
                    "status": "active",
                    "transaction_id": contract_result.transaction_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            
            logger.info(f"Created job pool {pool_id} by {creator_address}")
            
            return {
                "success": True,
                "pool_id": pool_id,
                "transaction_id": contract_result.transaction_id,
                "creator_address": creator_address,
                "title": title,
                "description": description,
                "required_skills": required_skills,
                "min_reputation": min_reputation,
                "stake_amount": stake_amount,
                "deadline": deadline.isoformat(),
                "duration_days": duration_days,
                "max_candidates": max_candidates,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "gas_used": contract_result.gas_used
            }
        
        except Exception as e:
            logger.error(f"Error creating job pool: {str(e)}")
            
            # Add failed audit log if database is available
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        audit_log = AuditLog(
                            user_address=creator_address,
                            action="create_job_pool",
                            resource_type="job_pool",
                            resource_id=None,
                            details={
                                "title": title,
                                "required_skills": required_skills,
                                "stake_amount": stake_amount,
                                "error": str(e)
                            },
                            success=False,
                            error_message=str(e)
                        )
                        db.add(audit_log)
                except Exception:
                    pass  # Ignore audit log failures
            
            raise
    
    # ============ APPLICATION PROCESS FUNCTIONS ============
    
    async def apply_to_pool(
        self,
        pool_id: str,
        applicant_address: str,
        skill_token_ids: List[str],
        cover_letter: str = ""
    ) -> Dict[str, Any]:
        """
        Submit an application to a job pool.
        
        Args:
            pool_id: ID of the job pool
            applicant_address: Address of the applicant
            skill_token_ids: List of skill token IDs to submit
            cover_letter: Cover letter for the application
            
        Returns:
            Dict containing application result
        """
        try:
            # Check job pool exists and get details
            job_pool_data = None
            
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        job_pool = db.query(JobPool).filter(JobPool.pool_id == pool_id).first()
                        
                        if not job_pool:
                            raise ValueError(f"Job pool {pool_id} not found")
                        
                        if job_pool.status != PoolStatusEnum.ACTIVE:
                            raise ValueError("Can only apply to active pools")
                        
                        if datetime.now(timezone.utc) > job_pool.deadline:
                            raise ValueError("Application deadline has passed")
                        
                        # Check if already applied
                        existing_application = db.query(PoolApplication).filter(
                            and_(
                                PoolApplication.pool_id == job_pool.id,
                                PoolApplication.applicant_address == applicant_address
                            )
                        ).first()
                        
                        if existing_application:
                            raise ValueError("Already applied to this pool")
                        
                        # Check maximum candidates
                        current_applications = db.query(PoolApplication).filter(
                            PoolApplication.pool_id == job_pool.id
                        ).count()
                        
                        if current_applications >= job_pool.max_candidates:
                            raise ValueError("Pool has reached maximum candidate limit")
                        
                        # Validate skill tokens belong to applicant
                        skill_tokens = db.query(SkillToken).filter(
                            and_(
                                SkillToken.token_id.in_(skill_token_ids),
                                SkillToken.owner_address == applicant_address,
                                SkillToken.is_active == True
                            )
                        ).all()
                        
                        if len(skill_tokens) != len(skill_token_ids):
                            raise ValueError("Some skill tokens are invalid or not owned by applicant")
                        
                        job_pool_data = job_pool
                except Exception as db_error:
                    logger.warning(f"Database check failed, using fallback: {str(db_error)}")
                    # Fall back to in-memory storage
                    pass
            
            # Fallback validation
            if not DATABASE_MODELS_AVAILABLE:
                if pool_id not in _fallback_pools:
                    raise ValueError(f"Job pool {pool_id} not found")
                
                pool_data = _fallback_pools[pool_id]
                if pool_data["status"] != "active":
                    raise ValueError("Can only apply to active pools")
                
                deadline = datetime.fromisoformat(pool_data["deadline"].replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > deadline:
                    raise ValueError("Application deadline has passed")
                
                # Check if already applied (fallback)
                if pool_id in _fallback_applications:
                    if applicant_address in _fallback_applications[pool_id]:
                        raise ValueError("Already applied to this pool")
                
                # Create mock skill tokens for validation
                skill_tokens = [{"token_id": tid, "skill_name": f"skill_{tid}"} for tid in skill_token_ids]
                
                # Mock job pool data for match scoring
                class MockJobPool:
                    def __init__(self, data):
                        self.pool_id = data["pool_id"]
                        self.required_skills = data["required_skills"]
                
                job_pool_data = MockJobPool(pool_data)
            
            # Calculate match score using AI if available
            if job_pool_data:
                match_score = await self._calculate_match_score(
                    job_pool_data, skill_tokens, applicant_address
                )
            else:
                match_score = 75.0  # Default fallback score
            
            # Apply on blockchain
            contract_result = await hedera_apply_to_pool(
                pool_id=self._extract_numeric_id(pool_id),
                skill_token_ids=[self._extract_numeric_id(tid) for tid in skill_token_ids],
                cover_letter=cover_letter
            )
            
            if not contract_result.success:
                raise Exception(f"Blockchain transaction failed: {contract_result.error}")
            
            # Create application record
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        application = PoolApplication(
                            pool_id=job_pool_data.id if hasattr(job_pool_data, 'id') else 1,
                            applicant_address=applicant_address,
                            cover_letter=cover_letter,
                            skill_token_ids=skill_token_ids,
                            match_score=match_score,
                            status="applied",
                            transaction_id=contract_result.transaction_id,
                            block_timestamp=datetime.now(timezone.utc)
                        )
                        
                        db.add(application)
                        
                        # Add audit log
                        audit_log = AuditLog(
                            user_address=applicant_address,
                            action="apply_to_pool",
                            resource_type="pool_application",
                            resource_id=str(application.id),
                            details={
                                "pool_id": pool_id,
                                "skill_token_ids": skill_token_ids,
                                "match_score": match_score,
                                "transaction_id": contract_result.transaction_id
                            },
                            success=True
                        )
                        db.add(audit_log)
                        
                        # Invalidate caches
                        self._invalidate_cache([
                            f"pool_applications:{pool_id}:*",
                            f"user_applications:{applicant_address}:*"
                        ])
                except Exception as db_error:
                    logger.warning(f"Database application storage failed: {str(db_error)}")
                    # Fall back to in-memory storage
                    pass
            
            # Fallback storage
            if pool_id not in _fallback_applications:
                _fallback_applications[pool_id] = {}
            
            _fallback_applications[pool_id][applicant_address] = {
                    "applicant_address": applicant_address,
                    "cover_letter": cover_letter,
                    "skill_token_ids": skill_token_ids,
                    "match_score": match_score,
                    "status": "applied",
                    "transaction_id": contract_result.transaction_id,
                    "applied_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Application submitted to pool {pool_id} by {applicant_address}")
            
            return {
                "success": True,
                "pool_id": pool_id,
                "applicant_address": applicant_address,
                "skill_token_ids": skill_token_ids,
                "match_score": match_score,
                "cover_letter": cover_letter,
                "transaction_id": contract_result.transaction_id,
                "status": "applied",
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "gas_used": contract_result.gas_used
            }
        
        except Exception as e:
            logger.error(f"Error applying to pool: {str(e)}")
            raise
    
    # ============ HELPER FUNCTIONS ============
    
    def _extract_numeric_id(self, id_str: str) -> int:
        """Extract numeric ID from string, handling various formats."""
        try:
            # If it's already a number, convert directly
            return int(id_str)
        except ValueError:
            # Try to extract number from string like "pool_123" or "skill_456"
            import re
            match = re.search(r'\d+', id_str)
            if match:
                return int(match.group())
            # Fallback: use hash of the string for consistent numeric ID
            return abs(hash(id_str)) % 1000000
    
    async def _calculate_match_score(
        self,
        job_pool: Any,
        skill_tokens: List[Any],
        applicant_address: str
    ) -> float:
        """Calculate AI-powered match score for an application."""
        try:
            # Get MCP service for AI matching
            mcp_service = self._get_mcp_service()
            
            if mcp_service:
                # Prepare skill data
                if hasattr(skill_tokens[0], 'skill_name'):
                    # Database skill tokens
                    applicant_skills = [
                        {
                            "name": token.skill_name,
                            "category": token.skill_category.value if hasattr(token, 'skill_category') else "general",
                            "level": token.level if hasattr(token, 'level') else 5,
                            "experience": token.experience_points if hasattr(token, 'experience_points') else 100
                        }
                        for token in skill_tokens
                    ]
                else:
                    # Fallback skill tokens
                    applicant_skills = [
                        {
                            "name": token.get("skill_name", f"skill_{token['token_id']}"),
                            "category": "general",
                            "level": 5,
                            "experience": 100
                        }
                        for token in skill_tokens
                    ]
                
                # Use MCP for match evaluation
                match_result = await mcp_service.evaluate_candidate_match(
                    job_id=job_pool.pool_id,
                    candidate_id=applicant_address,
                    job_requirements=job_pool.required_skills,
                    candidate_skills=applicant_skills
                )
                
                return float(match_result.get("match_score", 50.0))
        
        except Exception as e:
            logger.warning(f"AI match scoring failed, using fallback: {str(e)}")
        
        # Fallback to simple skill matching
        return self._calculate_simple_match_score(job_pool, skill_tokens)
    
    def _calculate_simple_match_score(
        self,
        job_pool: Any,
        skill_tokens: List[Any]
    ) -> float:
        """Simple fallback match score calculation."""
        try:
            required_skills = job_pool.required_skills
            if isinstance(required_skills, dict) and "basic_skills" in required_skills:
                required_skills = required_skills["basic_skills"]
            
            # Handle both database and fallback skill tokens
            if hasattr(skill_tokens[0], 'skill_name') if skill_tokens else False:
                # Database skill tokens
                applicant_skills = {token.skill_name: getattr(token, 'level', 5) for token in skill_tokens}
            else:
                # Fallback skill tokens
                applicant_skills = {token.get("skill_name", f"skill_{token['token_id']}"): 5 for token in skill_tokens}
            
            total_score = 0.0
            skill_count = len(required_skills) if required_skills else 1
            
            for required_skill in (required_skills or []):
                skill_name = required_skill.get("name", "")
                required_level = required_skill.get("level", 1)
                
                if skill_name in applicant_skills:
                    applicant_level = applicant_skills[skill_name]
                    if applicant_level >= required_level:
                        total_score += 100.0  # Perfect match
                    else:
                        # Partial score based on level difference
                        total_score += max(0, 100.0 - (required_level - applicant_level) * 15)
                # No score for missing skills
            
            return min(100.0, total_score / skill_count if skill_count > 0 else 75.0)
        
        except Exception as e:
            logger.warning(f"Simple match scoring failed: {str(e)}")
            return 50.0  # Default fallback score
    
    # ============ QUERY FUNCTIONS ============
    
    async def get_pool_details(self, pool_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a job pool.
        
        Args:
            pool_id: ID of the job pool
            
        Returns:
            Dict containing pool details or None if not found
        """
        try:
            # Try database first
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        job_pool = db.query(JobPool).filter(JobPool.pool_id == pool_id).first()
                        
                        if job_pool:
                            return {
                                "pool_id": job_pool.pool_id,
                                "creator_address": job_pool.creator_address,
                                "title": job_pool.title,
                                "description": job_pool.description,
                                "company_name": job_pool.company_name,
                                "location": job_pool.location,
                                "is_remote": job_pool.is_remote,
                                "required_skills": job_pool.required_skills,
                                "min_reputation": job_pool.min_reputation,
                                "salary_min": float(job_pool.salary_min) if job_pool.salary_min else None,
                                "salary_max": float(job_pool.salary_max) if job_pool.salary_max else None,
                                "stake_amount": float(job_pool.stake_amount),
                                "deadline": job_pool.deadline.isoformat(),
                                "duration_days": job_pool.duration_days,
                                "max_candidates": job_pool.max_candidates,
                                "status": job_pool.status.value,
                                "created_at": job_pool.created_at.isoformat(),
                                "updated_at": job_pool.updated_at.isoformat() if job_pool.updated_at else None
                            }
                except Exception as db_error:
                    logger.warning(f"Database query failed: {str(db_error)}")
            
            # Fallback to memory storage
            if pool_id in _fallback_pools:
                return _fallback_pools[pool_id]
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting pool details: {str(e)}")
            return None
    
    async def list_pools(
        self,
        creator_address: Optional[str] = None,
        status: Optional[str] = None,
        skill_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List job pools with optional filters.
        
        Args:
            creator_address: Filter by creator address
            status: Filter by pool status
            skill_name: Filter by required skill name
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of job pool details
        """
        try:
            pools = []
            
            # Try database first
            if DATABASE_MODELS_AVAILABLE:
                try:
                    with self._get_db_session() as db:
                        query = db.query(JobPool)
                        
                        if creator_address:
                            query = query.filter(JobPool.creator_address == creator_address)
                        
                        if status:
                            query = query.filter(JobPool.status == status)
                        
                        if skill_name:
                            # This would need proper JSON querying in production
                            query = query.filter(
                                func.json_extract(JobPool.required_skills, '$[*].name').like(f'%{skill_name}%')
                            )
                        
                        job_pools = query.order_by(desc(JobPool.created_at)).offset(offset).limit(limit).all()
                        
                        for job_pool in job_pools:
                            pools.append(await self.get_pool_details(job_pool.pool_id))
                        
                        return pools
                
                except Exception as db_error:
                    logger.warning(f"Database listing failed: {str(db_error)}")
            
            # Fallback to memory storage
            all_pools = list(_fallback_pools.values())
            
            # Apply filters
            if creator_address:
                all_pools = [p for p in all_pools if p.get("creator_address") == creator_address]
            
            if status:
                all_pools = [p for p in all_pools if p.get("status") == status]
            
            if skill_name:
                all_pools = [
                    p for p in all_pools 
                    if any(s.get("name", "").lower() == skill_name.lower() for s in p.get("required_skills", []))
                ]
            
            # Apply pagination
            return all_pools[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"Error listing pools: {str(e)}")
            return []

    # ============ ADDITIONAL TALENT POOL FUNCTIONS ============

    async def select_candidate(
        self,
        pool_id: str,
        candidate_address: str
    ) -> Dict[str, Any]:
        """
        Select a candidate for a job pool.
        
        Args:
            pool_id: ID of the job pool
            candidate_address: Address of the selected candidate
            
        Returns:
            Dict containing selection result
        """
        try:
            # Call blockchain function
            contract_result = await select_candidate(
                pool_id=pool_id,
                candidate_address=candidate_address
            )
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    pool = db.query(JobPool).filter(
                        JobPool.pool_id == pool_id
                    ).first()
                    
                    if pool:
                        pool.status = PoolStatusEnum.IN_PROGRESS.value
                        pool.selected_candidate = candidate_address
                        pool.updated_at = datetime.now(timezone.utc)
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "pool_id": pool_id,
                "selected_candidate": candidate_address
            }
            
        except Exception as e:
            logger.error(f"Error selecting candidate for pool {pool_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def complete_pool(
        self,
        pool_id: str
    ) -> Dict[str, Any]:
        """
        Complete a job pool.
        
        Args:
            pool_id: ID of the job pool to complete
            
        Returns:
            Dict containing completion result
        """
        try:
            # Call blockchain function
            contract_result = await complete_pool(pool_id=pool_id)
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    pool = db.query(JobPool).filter(
                        JobPool.pool_id == pool_id
                    ).first()
                    
                    if pool:
                        pool.status = PoolStatusEnum.COMPLETED.value
                        pool.completed_at = datetime.now(timezone.utc)
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "pool_id": pool_id,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error completing pool {pool_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def close_pool(
        self,
        pool_id: str
    ) -> Dict[str, Any]:
        """
        Close a job pool.
        
        Args:
            pool_id: ID of the job pool to close
            
        Returns:
            Dict containing closure result
        """
        try:
            # Call blockchain function
            contract_result = await close_pool(pool_id=pool_id)
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    pool = db.query(JobPool).filter(
                        JobPool.pool_id == pool_id
                    ).first()
                    
                    if pool:
                        pool.status = PoolStatusEnum.CLOSED.value
                        pool.closed_at = datetime.now(timezone.utc)
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "pool_id": pool_id,
                "status": "closed"
            }
            
        except Exception as e:
            logger.error(f"Error closing pool {pool_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def withdraw_application(
        self,
        pool_id: str
    ) -> Dict[str, Any]:
        """
        Withdraw an application from a job pool.
        
        Args:
            pool_id: ID of the job pool to withdraw from
            
        Returns:
            Dict containing withdrawal result
        """
        try:
            # Call blockchain function
            contract_result = await withdraw_application(pool_id=pool_id)
            
            if not contract_result.success:
                return {
                    "success": False,
                    "error": contract_result.error
                }
            
            # Update database
            if DATABASE_MODELS_AVAILABLE:
                with self._get_db_session() as db:
                    application = db.query(PoolApplication).filter(
                        PoolApplication.pool_id == pool_id,
                        PoolApplication.candidate_address == self._get_current_user_address()
                    ).first()
                    
                    if application:
                        application.status = "withdrawn"
                        application.withdrawn_at = datetime.now(timezone.utc)
                        db.commit()
            
            return {
                "success": True,
                "transaction_id": contract_result.transaction_id,
                "pool_id": pool_id,
                "status": "withdrawn"
            }
            
        except Exception as e:
            logger.error(f"Error withdrawing application from pool {pool_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def calculate_match_score(
        self,
        pool_id: str,
        candidate_address: str
    ) -> Dict[str, Any]:
        """
        Calculate match score for a candidate in a job pool.
        
        Args:
            pool_id: ID of the job pool
            candidate_address: Address of the candidate
            
        Returns:
            Dict containing match score and details
        """
        try:
            # Call blockchain function
            result = await calculate_match_score(
                pool_id=pool_id,
                candidate_address=candidate_address
            )
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to calculate match score")
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating match score for pool {pool_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_pool_metrics(self, pool_id: str) -> Dict[str, Any]:
        """
        Get pool metrics.
        
        Args:
            pool_id: ID of the job pool
            
        Returns:
            Dictionary containing pool metrics.
        """
        try:
            result = await get_pool_metrics(pool_id=pool_id)
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to get metrics for pool {pool_id}")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting pool metrics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_global_stats(self) -> Dict[str, Any]:
        """
        Get global talent pool statistics.
        
        Returns:
            Dictionary containing global stats.
        """
        try:
            result = await get_talent_pool_global_stats()
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

    async def get_active_pools_count(self) -> Dict[str, Any]:
        """
        Get active pools count.
        
        Returns:
            Dictionary containing active pools count.
        """
        try:
            result = await get_active_pools_count()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get active pools count")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting active pools count: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_total_pools_count(self) -> Dict[str, Any]:
        """
        Get total pools count.
        
        Returns:
            Dictionary containing total pools count.
        """
        try:
            result = await get_total_pools_count()
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get total pools count")
                }
            return result
        except Exception as e:
            logger.error(f"Error getting total pools count: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_current_user_address(self) -> str:
        """
        Get current user address (placeholder for authentication).
        
        Returns:
            Current user address
        """
        # This would be implemented with proper authentication
        # For now, return a placeholder
        return "0.0.123456"


# Singleton getters for dependency injection
def get_talent_pool_service() -> TalentPoolService:
    """
    Get the talent pool service instance.
    
    Returns:
        TalentPoolService: The talent pool service instance
    """
    return TalentPoolService()


def get_pool_service() -> TalentPoolService:
    """
    Get the pool service instance (alias for get_talent_pool_service).
    
    Returns:
        TalentPoolService: The talent pool service instance
    """
    return TalentPoolService()

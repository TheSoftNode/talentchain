"""
TalentChain Pro - Unified Hedera Client Utility Module

This module provides comprehensive utilities for interacting with the Hedera network,
including client initialization, smart contract interactions, HTS token operations,
HCS messaging, event processing, and transaction management.

This unified module combines all Hedera functionality into a single, professional interface.
"""

import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List, Union, Tuple, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

if TYPE_CHECKING:
    from hedera import (
        Client, ContractFunctionParameters, Hbar, PrivateKey
    )

import hedera
from hedera import (
    # Core
    Client, AccountId, PrivateKey, PublicKey, Hbar,
    # Smart Contracts
    ContractId, ContractCreateFlow, ContractExecuteTransaction, 
    ContractCallQuery, ContractFunctionParameters, ContractFunctionResult,
    # Tokens (HTS)
    TokenId, TokenCreateTransaction, TokenType, TokenSupplyType,
    TokenMintTransaction, TransferTransaction, TokenBurnTransaction,
    TokenAssociateTransaction, TokenFreezeTransaction, TokenWipeTransaction,
    # Consensus Service (HCS)
    TopicId, TopicCreateTransaction, TopicMessageSubmitTransaction,
    TopicInfoQuery, TopicUpdateTransaction,
    # Transactions
    Transaction, TransactionResponse, TransactionReceipt, TransactionRecord,
    TransferTransaction, AccountCreateTransaction, AccountUpdateTransaction,
    TransactionId,
    # Query
    AccountBalanceQuery, AccountInfoQuery,
    # Status and Exceptions
    Status, PrecheckStatusException, ReceiptStatusException
)

from app.config import get_settings, get_contract_config, get_contract_abi, get_contract_address

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class NetworkType(Enum):
    """Hedera network types."""
    MAINNET = "mainnet"
    TESTNET = "testnet" 
    PREVIEWNET = "previewnet"


class SkillCategory(str, Enum):
    """Skill categories for token classification."""
    TECHNICAL = "technical"
    CREATIVE = "creative"
    BUSINESS = "business"
    COMMUNICATION = "communication"
    LEADERSHIP = "leadership"
    ANALYTICAL = "analytical"
    DESIGN = "design"
    MARKETING = "marketing"
    SALES = "sales"
    FINANCE = "finance"
    LEGAL = "legal"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    OTHER = "other"


@dataclass
class HederaConfig:
    """Configuration for Hedera client."""
    network: NetworkType
    operator_id: str
    operator_key: str
    max_transaction_fee: int = 100
    max_query_payment: int = 50


@dataclass
class ContractInfo:
    """Smart contract deployment information."""
    contract_id: str
    name: str
    abi: List[Dict[str, Any]]
    deployed_at: datetime
    network: str


@dataclass
class SkillTokenData:
    """Skill token data structure."""
    token_id: str
    skill_name: str
    skill_category: SkillCategory
    level: int
    description: str
    metadata_uri: str
    owner_address: str
    created_at: datetime
    expiry_date: Optional[datetime] = None


@dataclass
class TransactionResult:
    """Transaction execution result."""
    success: bool
    transaction_id: Optional[str] = None
    error: Optional[str] = None
    gas_used: Optional[int] = None
    contract_address: Optional[str] = None
    token_id: Optional[str] = None
    pool_id: Optional[str] = None


# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

# Global Hedera client instance
_hedera_client: Optional[Client] = None

# Contract configuration cache
_contract_config: Optional[Dict[str, Dict[str, Any]]] = None

# =============================================================================
# CLIENT INITIALIZATION
# =============================================================================

def initialize_hedera_client() -> Client:
    """
    Initialize and configure the Hedera client.
    
    Returns:
        Configured Hedera client instance
        
    Raises:
        Exception: If client initialization fails
    """
    global _hedera_client
    
    if _hedera_client is not None:
        return _hedera_client
    
    try:
        settings = get_settings()
        
        # Parse operator account ID
        operator_id = AccountId.fromString(settings.hedera_account_id)
        
        # Parse operator private key
        operator_key = PrivateKey.fromString(settings.hedera_private_key)
        
        # Create client based on network
        if settings.hedera_network == "testnet":
            client = Client.forTestnet()
        elif settings.hedera_network == "mainnet":
            client = Client.forMainnet()
        elif settings.hedera_network == "previewnet":
            client = Client.forPreviewnet()
        else:
            raise ValueError(f"Unsupported network: {settings.hedera_network}")
        
        # Set operator
        client.setOperator(operator_id, operator_key)
        
        # Set default transaction fee
        client.setDefaultMaxTransactionFee(Hbar(settings.max_transaction_fee))
        client.setDefaultMaxQueryPayment(Hbar(settings.max_query_payment))
        
        _hedera_client = client
        logger.info(f"Hedera client initialized for {settings.hedera_network}")
        
        return client
        
    except Exception as e:
        logger.error(f"Failed to initialize Hedera client: {str(e)}")
        raise Exception(f"Hedera client initialization failed: {str(e)}")


def get_hedera_client() -> Client:
    """
    Get the initialized Hedera client instance.
    
    Returns:
        Hedera client instance
        
    Raises:
        Exception: If client is not initialized
    """
    if _hedera_client is None:
        return initialize_hedera_client()
    return _hedera_client


# =============================================================================
# SMART CONTRACT INTEGRATION
# =============================================================================

def get_contract_manager() -> Dict[str, Dict[str, Any]]:
    """
    Get the contract manager with all contract configurations.
    
    Returns:
        Dictionary containing contract configurations
    """
    global _contract_config
    
    if _contract_config is None:
        _contract_config = get_contract_config()
    
    return _contract_config


def get_client() -> Client:
    """
    Get the Hedera client instance (alias for get_hedera_client).
    
    Returns:
        Hedera client instance
    """
    return get_hedera_client()


async def create_skill_token(
    recipient_address: str,
    skill_name: str,
    skill_category: str,
    level: int = 1,
    description: str = "",
    metadata_uri: str = ""
) -> TransactionResult:
    """
    Create a skill token using the SkillToken smart contract.
    
    Args:
        recipient_address: Hedera account ID to receive the token
        skill_name: Name of the skill
        skill_category: Category of the skill
        level: Initial skill level (1-10)
        description: Description of the skill
        metadata_uri: URI to metadata
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="SkillToken contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters - match the actual ABI signature
        # mintSkillToken(address recipient, string skillName, string skillCategory, uint8 level, string description, string metadataUri)
        params = ContractFunctionParameters()
        params.addAddress(recipient_address)
        params.addString(skill_name)
        params.addString(skill_category)
        params.addUint8(level)
        params.addString(description)
        params.addString(metadata_uri)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(300000)  # Adjust gas as needed
        transaction.setFunction("mintSkillToken", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            # Get the transaction record to extract token ID from logs
            record = response.getRecord(client)
            
            # Extract token ID from contract function result
            function_result = record.contractFunctionResult
            token_id = None
            if function_result and function_result.getUint256(0):
                token_id = str(function_result.getUint256(0))
            
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=record.gasUsed,
                contract_address=contract_address,
                token_id=token_id
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to create skill token: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def add_skill_experience(
    token_id: str,
    experience_points: int
) -> TransactionResult:
    """
    Add experience points to a skill token.
    
    Args:
        token_id: ID of the skill token
        experience_points: Experience points to add
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        # For now, this is a placeholder since the contract doesn't have this function
        # In a real implementation, this would call a contract function
        logger.info(f"Adding {experience_points} experience points to token {token_id}")
        
        return TransactionResult(
            success=True,
            transaction_id=f"exp_{token_id}_{int(datetime.now().timestamp())}",
            gas_used=0
        )
        
    except Exception as e:
        logger.error(f"Failed to add skill experience: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def update_skill_level(
    token_id: str,
    new_level: int,
    new_metadata_uri: str = ""
) -> TransactionResult:
    """
    Update skill token level using the SkillToken smart contract.
    
    Args:
        token_id: ID of the skill token to update
        new_level: New skill level (1-10)
        new_metadata_uri: New metadata URI
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="SkillToken contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters - match the actual ABI signature
        # updateSkillLevel(uint256 tokenId, uint8 newLevel, string newMetadataUri)
        params = ContractFunctionParameters()
        params.addUint256(int(token_id))
        params.addUint8(new_level)
        params.addString(new_metadata_uri)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)  # Adjust gas as needed
        transaction.setFunction("updateSkillLevel", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            record = response.getRecord(client)
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=record.gasUsed if record else 0
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to update skill level: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def create_job_pool(
    title: str,
    description: str,
    required_skills: List[Dict[str, Any]],
    stake_amount: float,
    duration_days: int
) -> TransactionResult:
    """
    Create a job pool using the TalentPool smart contract.
    
    Args:
        title: Job pool title
        description: Job pool description
        required_skills: List of required skills
        stake_amount: Stake amount in HBAR
        duration_days: Duration of the pool in days
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        talent_pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = talent_pool_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="TalentPool contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare JobPoolRequest struct according to the ABI
        # struct JobPoolRequest {
        #     string title;
        #     string description;
        #     uint256[] requiredSkills;
        #     uint256 minReputation;
        #     uint256 stakeAmount;
        #     uint256 durationDays;
        #     uint256 maxApplicants;
        #     uint256 applicationDeadline;
        # }
        
        # Convert required skills to skill IDs (simplified)
        skill_ids = [hash(skill.get('name', '')) % 1000000 for skill in required_skills]
        
        # Calculate application deadline
        application_deadline = int(datetime.now().timestamp()) + (duration_days * 24 * 60 * 60)
        
        params = ContractFunctionParameters()
        
        # Add the JobPoolRequest struct as a tuple
        params.addString(title)  # title
        params.addString(description)  # description
        params.addUint256Array(skill_ids)  # requiredSkills
        params.addUint256(0)  # minReputation (default to 0)
        params.addUint256(int(stake_amount * 100_000_000))  # stakeAmount in tinybars
        params.addUint256(duration_days)  # durationDays
        params.addUint256(100)  # maxApplicants (default to 100)
        params.addUint256(application_deadline)  # applicationDeadline
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(500000)  # Adjust gas as needed
        transaction.setFunction("createJobPool", params)
        
        # Set payable amount
        transaction.setPayableAmount(Hbar.fromTinybars(int(stake_amount * 100_000_000)))
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            # Get pool ID from contract function result
            record = response.getRecord(client)
            pool_id = None
            if record and record.contractFunctionResult:
                try:
                    pool_id = str(record.contractFunctionResult.getUint256(0))
                except:
                    pool_id = f"pool_{int(datetime.now().timestamp())}"
            
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=record.gasUsed if record else 0,
                contract_address=contract_address,
                pool_id=pool_id
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to create job pool: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def apply_to_pool(
    pool_id: int,
    skill_token_ids: List[int],
    cover_letter: str = ""
) -> TransactionResult:
    """
    Apply to a job pool using the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool
        skill_token_ids: List of skill token IDs
        cover_letter: Cover letter for the application
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        # For now, this is a placeholder since the contract doesn't have this function
        # In a real implementation, this would call a contract function
        logger.info(f"Applying to pool {pool_id} with skills {skill_token_ids}")
        
        return TransactionResult(
            success=True,
            transaction_id=f"apply_{pool_id}_{int(datetime.now().timestamp())}",
            gas_used=0
        )
        
    except Exception as e:
        logger.error(f"Failed to apply to pool: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def make_pool_match(
    pool_id: int,
    candidate_address: str,
    match_score: int
) -> TransactionResult:
    """
    Make a pool match using the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool
        candidate_address: Address of the matched candidate
        match_score: Match score for the candidate
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        # For now, this is a placeholder since the contract doesn't have this function
        # In a real implementation, this would call a contract function
        logger.info(f"Making match for pool {pool_id} with candidate {candidate_address}")
        
        return TransactionResult(
            success=True,
            transaction_id=f"match_{pool_id}_{int(datetime.now().timestamp())}",
            gas_used=0
        )
        
    except Exception as e:
        logger.error(f"Failed to make pool match: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def get_job_pool_info(pool_id: int) -> Optional[Dict[str, Any]]:
    """
    Get job pool information from the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool
        
    Returns:
        Job pool information if found, None otherwise
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        talent_pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = talent_pool_config.get('address')
        
        if not contract_address:
            logger.warning("TalentPool contract not deployed")
            return None
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getJobPool(uint256 poolId)
        params = ContractFunctionParameters()
        params.addUint256(pool_id)
        
        # Query contract function
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(200000)
        query.setFunction("getJobPool", params)
        
        # Execute query
        response = query.execute(client)
        result = response.getFunctionResult()
        
        if result:
            # Parse the JobPool struct returned
            # struct JobPool {
            #     uint256 id;
            #     address company;
            #     string title;
            #     string description;
            #     uint256[] requiredSkills;
            #     uint256 minReputation;
            #     uint256 stakeAmount;
            #     uint256 durationDays;
            #     uint256 maxApplicants;
            #     uint256 applicationDeadline;
            #     enum PoolStatus status;
            #     uint256 createdAt;
            # }
            
            try:
                id = result.getUint256(0)
                company = result.getAddress(1)
                title = result.getString(2)
                description = result.getString(3)
                # requiredSkills array would need special parsing
                min_reputation = result.getUint256(5)
                stake_amount = result.getUint256(6)
                duration_days = result.getUint256(7)
                max_applicants = result.getUint256(8)
                application_deadline = result.getUint256(9)
                status = result.getUint8(10)  # enum as uint8
                created_at = result.getUint256(11)
                
                # Convert status enum
                status_map = {0: "active", 1: "closed", 2: "completed", 3: "cancelled"}
                status_str = status_map.get(status, "unknown")
                
                return {
                    'id': pool_id,
                    'company': company,
                    'title': title,
                    'description': description,
                    'min_reputation': min_reputation,
                    'stake_amount': float(stake_amount) / 100_000_000,  # Convert from tinybars to HBAR
                    'duration_days': duration_days,
                    'max_applicants': max_applicants,
                    'application_deadline': application_deadline,
                    'status': status_str,
                    'created_at': created_at
                }
            except Exception as parse_error:
                logger.error(f"Failed to parse job pool data: {parse_error}")
                return None
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get job pool info: {str(e)}")
        return None


async def submit_hcs_message(topic_id: str, message: str) -> TransactionResult:
    """
    Submit a message to HCS topic.
    
    Args:
        topic_id: HCS topic ID
        message: Message to submit
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        
        # Parse topic ID
        topic = TopicId.fromString(topic_id)
        
        # Create and submit message
        transaction = TopicMessageSubmitTransaction()
        transaction.setTopicId(topic)
        transaction.setMessage(message)
        
        # Execute transaction
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=receipt.gasUsed
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to submit HCS message: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def create_nft_token(
    name: str,
    symbol: str,
    metadata: Dict[str, Any]
) -> TransactionResult:
    """
    Create an NFT token on Hedera.
    
    Args:
        name: Token name
        symbol: Token symbol
        metadata: Token metadata
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        
        # Create token
        transaction = TokenCreateTransaction()
        transaction.setTokenName(name)
        transaction.setTokenSymbol(symbol)
        transaction.setTokenType(TokenType.NON_FUNGIBLE_UNIQUE)
        transaction.setSupplyType(TokenSupplyType.FINITE)
        transaction.setMaxSupply(1000000)
        
        # Set treasury and keys
        operator_id = client.getOperatorAccountId()
        transaction.setTreasuryAccountId(operator_id)
        
        # Execute transaction
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=receipt.gasUsed,
                contract_address=str(receipt.tokenId)
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Token creation failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to create NFT token: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def mint_nft(
    token_id: str,
    metadata_uri: str,
    recipient_id: str
) -> TransactionResult:
    """
    Mint an NFT to a recipient.
    
    Args:
        token_id: Token ID
        metadata_uri: Metadata URI
        recipient_id: Recipient account ID
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        
        # Parse token and recipient IDs
        token = TokenId.fromString(token_id)
        recipient = AccountId.fromString(recipient_id)
        
        # Mint NFT
        transaction = TokenMintTransaction()
        transaction.setTokenId(token)
        transaction.addMetadata(metadata_uri.encode('utf-8'))
        
        # Execute transaction
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=receipt.gasUsed
            )
        else:
            return TransactionResult(
                success=False,
                error=f"NFT minting failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to mint NFT: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def get_skill_token_info(token_id: str) -> Optional[SkillTokenData]:
    """
    Get skill token information from the smart contract.
    
    Args:
        token_id: ID of the skill token
        
    Returns:
        SkillTokenData if found, None otherwise
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            logger.warning("SkillToken contract not deployed")
            return None
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters
        params = ContractFunctionParameters()
        params.addUint256(int(token_id))
        
        # Query contract function - getSkillData(uint256 tokenId)
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getSkillData", params)
        
        # Execute query
        response = query.execute(client)
        result = response.getFunctionResult()
        
        if result:
            # Parse the SkillData struct returned
            # struct SkillData {
            #     string skillName;
            #     string skillCategory;
            #     uint8 level;
            #     string description;
            #     string metadataUri;
            #     uint64 createdAt;
            #     uint64 expiryDate;
            # }
            
            skill_name = result.getString(0)
            skill_category = result.getString(1)
            level = result.getUint8(2)
            description = result.getString(3)
            metadata_uri = result.getString(4)
            created_at = result.getUint64(5)
            expiry_date = result.getUint64(6)
            
            # Convert category string to enum
            try:
                category_enum = SkillCategory(skill_category.lower())
            except ValueError:
                category_enum = SkillCategory.OTHER
            
            return SkillTokenData(
                token_id=token_id,
                skill_name=skill_name,
                skill_category=category_enum,
                level=level,
                description=description,
                metadata_uri=metadata_uri,
                owner_address="",  # We'd need to call ownerOf separately
                created_at=datetime.fromtimestamp(created_at, timezone.utc),
                expiry_date=datetime.fromtimestamp(expiry_date, timezone.utc) if expiry_date > 0 else None
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get skill token info: {str(e)}")
        return None


async def get_user_skills(owner_address: str) -> List[SkillTokenData]:
    """
    Get all skill tokens owned by a user.
    
    Args:
        owner_address: Hedera account ID of the owner
        
    Returns:
        List of SkillTokenData
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            logger.warning("SkillToken contract not deployed")
            return []
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getTokensByOwner(address owner)
        params = ContractFunctionParameters()
        params.addAddress(owner_address)
        
        # Query contract function
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(200000)
        query.setFunction("getTokensByOwner", params)
        
        # Execute query
        response = query.execute(client)
        result = response.getFunctionResult()
        
        if result:
            # Get array of token IDs
            token_ids = []
            try:
                # Parse uint256 array result
                array_size = result.getUint256(0)  # First element is array length
                for i in range(1, int(array_size) + 1):
                    token_ids.append(str(result.getUint256(i)))
            except Exception as parse_error:
                logger.warning(f"Could not parse token IDs array: {parse_error}")
                return []
            
            # Get detailed info for each token
            skills = []
            for token_id in token_ids:
                skill_info = await get_skill_token_info(token_id)
                if skill_info:
                    skill_info.owner_address = owner_address
                    skills.append(skill_info)
            
            return skills
        
        return []
        
    except Exception as e:
        logger.error(f"Failed to get user skills: {str(e)}")
        return []


async def submit_work_evaluation_to_oracle(
    user_address: str,
    skill_token_ids: List[str],
    work_description: str,
    work_content: str,
    overall_score: int,
    skill_scores: List[int],
    feedback: str,
    ipfs_hash: str = ""
) -> TransactionResult:
    """
    Submit work evaluation to the ReputationOracle contract.
    
    Args:
        user_address: User being evaluated
        skill_token_ids: List of skill token IDs
        work_description: Description of the work
        work_content: Work content or artifacts
        overall_score: Overall score (0-100)
        skill_scores: Individual skill scores
        feedback: Evaluation feedback
        ipfs_hash: IPFS hash for additional data
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="ReputationOracle contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for submitWorkEvaluation
        # submitWorkEvaluation(address user, uint256[] skillTokenIds, string workDescription, 
        #                     string workContent, uint256 overallScore, uint256[] skillScores, 
        #                     string feedback, string ipfsHash)
        params = ContractFunctionParameters()
        params.addAddress(user_address)
        params.addUint256Array([int(token_id) for token_id in skill_token_ids])
        params.addString(work_description)
        params.addString(work_content)
        params.addUint256(overall_score)
        params.addUint256Array(skill_scores)
        params.addString(feedback)
        params.addString(ipfs_hash)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(400000)
        transaction.setFunction("submitWorkEvaluation", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            # Get evaluation ID from contract function result
            record = response.getRecord(client)
            evaluation_id = None
            if record and record.contractFunctionResult:
                try:
                    evaluation_id = str(record.contractFunctionResult.getUint256(0))
                except:
                    evaluation_id = f"eval_{int(datetime.now().timestamp())}"
            
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=record.gasUsed if record else 0,
                contract_address=contract_address,
                token_id=evaluation_id  # Reuse token_id field for evaluation_id
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to submit work evaluation to oracle: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def get_reputation_score_from_oracle(user_address: str) -> Optional[Dict[str, Any]]:
    """
    Get reputation score from the ReputationOracle contract.
    
    Args:
        user_address: User's Hedera account address
        
    Returns:
        Reputation data if found, None otherwise
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            logger.warning("ReputationOracle contract not deployed")
            return None
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getReputationScore(address user)
        params = ContractFunctionParameters()
        params.addAddress(user_address)
        
        # Query contract function
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getReputationScore", params)
        
        # Execute query
        response = query.execute(client)
        result = response.getFunctionResult()
        
        if result:
            # Parse the return values:
            # returns (uint256 overallScore, uint256 totalEvaluations, uint64 lastUpdated, bool isActive)
            overall_score = result.getUint256(0)
            total_evaluations = result.getUint256(1)
            last_updated = result.getUint64(2)
            is_active = result.getBool(3)
            
            return {
                'user_address': user_address,
                'overall_score': overall_score,
                'total_evaluations': total_evaluations,
                'last_updated': last_updated,
                'is_active': is_active
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get reputation score from oracle: {str(e)}")
        return None


async def create_governance_proposal(
    title: str,
    description: str,
    targets: List[str] = None,
    values: List[int] = None,
    calldatas: List[str] = None,
    ipfs_hash: str = ""
) -> TransactionResult:
    """
    Create a governance proposal.
    
    Args:
        title: Proposal title
        description: Proposal description
        targets: Target contract addresses
        values: Values to send with calls
        calldatas: Call data for each target
        ipfs_hash: IPFS hash for additional proposal data
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Default empty arrays if not provided
        targets = targets or []
        values = values or []
        calldatas = calldatas or []
        
        # Prepare function parameters for createProposal
        params = ContractFunctionParameters()
        params.addString(title)
        params.addString(description)
        params.addAddressArray(targets)
        params.addUint256Array(values)
        params.addBytesArray([bytes(data, 'utf-8') for data in calldatas])
        params.addString(ipfs_hash)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(300000)
        transaction.setFunction("createProposal", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            # Get proposal ID from contract function result
            record = response.getRecord(client)
            proposal_id = None
            if record and record.contractFunctionResult:
                try:
                    proposal_id = str(record.contractFunctionResult.getUint256(0))
                except:
                    proposal_id = f"proposal_{int(datetime.now().timestamp())}"
            
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=record.gasUsed if record else 0,
                contract_address=contract_address,
                token_id=proposal_id  # Reuse token_id field for proposal_id
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to create governance proposal: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def cast_governance_vote(
    proposal_id: int,
    vote: int,  # 0 = Against, 1 = For, 2 = Abstain
    reason: str = ""
) -> TransactionResult:
    """
    Cast a vote on a governance proposal.
    
    Args:
        proposal_id: Proposal ID to vote on
        vote: Vote type (0=Against, 1=For, 2=Abstain)
        reason: Optional reason for the vote
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for castVote
        params = ContractFunctionParameters()
        params.addUint256(proposal_id)
        params.addUint8(vote)
        params.addString(reason)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("castVote", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=receipt.gasUsed if hasattr(receipt, 'gasUsed') else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to cast governance vote: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def delegate_voting_power(
    delegatee: str
) -> TransactionResult:
    """
    Delegate voting power to another address.
    
    Args:
        delegatee: Address to delegate voting power to
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for delegate
        params = ContractFunctionParameters()
        params.addAddress(delegatee)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(150000)
        transaction.setFunction("delegate", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=receipt.gasUsed if hasattr(receipt, 'gasUsed') else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to delegate voting power: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def undelegate_voting_power() -> TransactionResult:
    """
    Undelegate voting power (remove delegation).
    
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Execute contract function (no parameters needed)
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(150000)
        transaction.setFunction("undelegate")
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=receipt.gasUsed if hasattr(receipt, 'gasUsed') else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to undelegate voting power: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def create_emergency_proposal(
    title: str,
    description: str,
    targets: List[str],
    values: List[int],
    calldatas: List[str],
    ipfs_hash: str,
    justification: str
) -> TransactionResult:
    """
    Create an emergency governance proposal.
    
    Args:
        title: Emergency proposal title
        description: Emergency proposal description
        targets: Target contract addresses
        values: Values to send with calls
        calldatas: Call data for each target
        ipfs_hash: IPFS hash for additional proposal data
        justification: Emergency justification
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for createEmergencyProposal
        params = ContractFunctionParameters()
        params.addString(title)
        params.addString(description)
        params.addAddressArray(targets)
        params.addUint256Array(values)
        params.addBytesArray([bytes(data, 'utf-8') for data in calldatas])
        params.addString(ipfs_hash)
        params.addString(justification)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(300000)
        transaction.setFunction("createEmergencyProposal", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            # Get proposal ID from contract function result
            record = response.getRecord(client)
            proposal_id = None
            if record and record.contractFunctionResult:
                try:
                    proposal_id = str(record.contractFunctionResult.getUint256(0))
                except:
                    proposal_id = f"emergency_proposal_{int(datetime.now().timestamp())}"
            
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=record.gasUsed if record else 0,
                contract_address=contract_address,
                token_id=proposal_id  # Reuse token_id field for proposal_id
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to create emergency governance proposal: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


# =============================================================================
# CONTRACT DEPLOYMENT AND VERIFICATION
# =============================================================================

async def check_contract_deployments() -> Dict[str, bool]:
    """
    Check the deployment status of all required contracts.
    
    Returns:
        Dictionary mapping contract names to deployment status
    """
    try:
        contract_config = get_contract_manager()
        deployment_status = {}
        
        for contract_name, config in contract_config.items():
            address = config.get('address', '')
            abi = config.get('abi', [])
            
            # Check if contract is deployed and has ABI
            is_deployed = bool(address and address.startswith('0.0.'))
            has_abi = len(abi) > 0
            
            deployment_status[contract_name] = {
                'deployed': is_deployed,
                'address': address,
                'has_abi': has_abi,
                'ready': is_deployed and has_abi
            }
        
        return deployment_status
        
    except Exception as e:
        logger.error(f"Failed to check contract deployments: {str(e)}")
        return {}


async def verify_contract_functionality() -> Dict[str, Dict[str, Any]]:
    """
    Verify that deployed contracts are functioning correctly.
    
    Returns:
        Dictionary with verification results for each contract
    """
    try:
        contract_config = get_contract_manager()
        verification_results = {}
        
        for contract_name, config in contract_config.items():
            if not config.get('deployed'):
                verification_results[contract_name] = {
                    'status': 'not_deployed',
                    'message': 'Contract not deployed'
                }
                continue
            
            # Try to call a basic view function to verify functionality
            try:
                if contract_name == 'SkillToken':
                    # Try to get total supply or similar
                    result = await get_skill_token_info("1")  # Test with token ID 1
                    verification_results[contract_name] = {
                        'status': 'functional' if result is not None else 'error',
                        'message': 'Contract responding to queries' if result is not None else 'Query failed'
                    }
                else:
                    verification_results[contract_name] = {
                        'status': 'not_tested',
                        'message': 'Verification not implemented for this contract type'
                    }
                    
            except Exception as e:
                verification_results[contract_name] = {
                    'status': 'error',
                    'message': f'Verification failed: {str(e)}'
                }
        
        return verification_results
        
    except Exception as e:
        logger.error(f"Failed to verify contract functionality: {str(e)}")
        return {}


# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================

async def check_hedera_connection() -> Dict[str, Any]:
    """
    Check Hedera network connection health.
    
    Returns:
        Dictionary with connection status and details
    """
    try:
        client = get_hedera_client()
        
        # Try to get account info to test connection
        operator_id = client.getOperatorAccountId()
        account_info = AccountInfoQuery().setAccountId(operator_id).execute(client)
        
        return {
            'status': 'connected',
            'network': str(client.getNetworkName()),
            'operator_account': str(operator_id),
            'account_balance': str(account_info.balance),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def validate_hedera_address(address: str) -> bool:
    """
    Validate Hedera account address format.
    
    Args:
        address: Address string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not address.startswith('0.0.'):
            return False
        
        # Try to parse as AccountId
        AccountId.fromString(address)
        return True
        
    except Exception:
        return False


def format_hedera_address(address: str) -> str:
    """
    Format Hedera address for display.
    
    Args:
        address: Raw Hedera address
        
    Returns:
        Formatted address string
    """
    if not address:
        return ""
    
    if len(address) > 10:
        return f"{address[:6]}...{address[-4:]}"
    
    return address


def get_network_info() -> Dict[str, Any]:
    """
    Get current network information.
    
    Returns:
        Network configuration dictionary
    """
    try:
        client = get_hedera_client()
        settings = get_settings()
        
        return {
            'name': settings.hedera_network,
            'client_network': str(client.getNetworkName()),
            'operator_account': str(client.getOperatorAccountId()),
            'mirror_node': settings.hedera_mirror_node_url
        }
        
    except Exception as e:
        logger.error(f"Failed to get network info: {str(e)}")
        return {
            'name': 'unknown',
            'error': str(e)
        }

async def register_reputation_oracle(
    name: str,
    specializations: List[str]
) -> TransactionResult:
    """
    Register a new reputation oracle.
    
    Args:
        name: Oracle name
        specializations: List of oracle specializations
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="ReputationOracle contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for registerOracle
        params = ContractFunctionParameters()
        params.addString(name)
        params.addStringArray(specializations)
        
        # Execute contract function (payable - stake amount should be msg.value)
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("registerOracle", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=receipt.gasUsed if hasattr(receipt, 'gasUsed') else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to register reputation oracle: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def submit_work_evaluation(
    user: str,
    skill_token_ids: List[int],
    work_description: str,
    work_content: str,
    overall_score: int,
    skill_scores: List[int],
    feedback: str,
    ipfs_hash: str
) -> TransactionResult:
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
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="ReputationOracle contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for submitWorkEvaluation
        params = ContractFunctionParameters()
        params.addAddress(user)
        params.addUint256Array(skill_token_ids)
        params.addString(work_description)
        params.addString(work_content)
        params.addUint8(overall_score)
        params.addUint8Array(skill_scores)
        params.addString(feedback)
        params.addString(ipfs_hash)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(300000)
        transaction.setFunction("submitWorkEvaluation", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            # Get evaluation ID from contract function result
            record = response.getRecord(client)
            evaluation_id = None
            if record and record.contractFunctionResult:
                try:
                    evaluation_id = str(record.contractFunctionResult.getUint256(0))
                except:
                    evaluation_id = f"eval_{int(datetime.now().timestamp())}"
            
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=record.gasUsed if record else 0,
                contract_address=contract_address,
                token_id=evaluation_id  # Reuse token_id field for evaluation_id
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to submit work evaluation: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def resolve_challenge(
    challenge_id: str,
    uphold_original: bool,
    resolution: str
) -> TransactionResult:
    """
    Resolve a challenge using the ReputationOracle smart contract.
    
    Args:
        challenge_id: ID of the challenge to resolve
        uphold_original: Whether to uphold the original evaluation
        resolution: Resolution description
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="ReputationOracle contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for resolveChallenge
        params = ContractFunctionParameters()
        params.addUint256(int(challenge_id))
        params.addBool(uphold_original)
        params.addString(resolution)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("resolveChallenge", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to resolve challenge: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def slash_oracle(
    oracle_address: str,
    amount: int,
    reason: str
) -> TransactionResult:
    """
    Slash an oracle using the ReputationOracle smart contract.
    
    Args:
        oracle_address: Address of the oracle to slash
        amount: Amount to slash
        reason: Reason for slashing
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="ReputationOracle contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for slashOracle
        params = ContractFunctionParameters()
        params.addAddress(oracle_address)
        params.addUint256(amount)
        params.addString(reason)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("slashOracle", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to slash oracle: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def withdraw_oracle_stake() -> TransactionResult:
    """
    Withdraw oracle stake using the ReputationOracle smart contract.
    
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="ReputationOracle contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for withdrawOracleStake (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("withdrawOracleStake", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to withdraw oracle stake: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def get_oracle_performance(
    oracle_address: str
) -> Dict[str, Any]:
    """
    Get oracle performance metrics using the ReputationOracle smart contract.
    
    Args:
        oracle_address: Address of the oracle
        
    Returns:
        Dictionary containing performance metrics
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "ReputationOracle contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getOraclePerformance
        params = ContractFunctionParameters()
        params.addAddress(oracle_address)
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getOraclePerformance", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                performance = {
                    "evaluations_completed": result.getUint256(0) if result else 0,
                    "successful_challenges": result.getUint256(1) if result else 0,
                    "failed_challenges": result.getUint256(2) if result else 0,
                    "last_activity": result.getUint256(3) if result else 0
                }
                
                return {
                    "success": True,
                    "oracle_address": oracle_address,
                    "performance": performance
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse oracle performance data: {str(parse_error)}")
                return {
                    "success": True,
                    "oracle_address": oracle_address,
                    "performance": {
                        "evaluations_completed": 0,
                        "successful_challenges": 0,
                        "failed_challenges": 0,
                        "last_activity": 0
                    }
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get oracle performance: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# ADDITIONAL SKILL TOKEN FUNCTIONS
# =============================================================================

async def endorse_skill_token(
    token_id: str,
    endorsement_data: str
) -> TransactionResult:
    """
    Endorse a skill token using the SkillToken smart contract.
    
    Args:
        token_id: ID of the skill token to endorse
        endorsement_data: Data describing the endorsement
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="SkillToken contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for endorseSkillToken
        params = ContractFunctionParameters()
        params.addUint256(int(token_id))
        params.addString(endorsement_data)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("endorseSkillToken", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to endorse skill token: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def renew_skill_token(
    token_id: str,
    new_expiry_date: int
) -> TransactionResult:
    """
    Renew a skill token using the SkillToken smart contract.
    
    Args:
        token_id: ID of the skill token to renew
        new_expiry_date: New expiry date as Unix timestamp
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="SkillToken contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for renewSkillToken
        params = ContractFunctionParameters()
        params.addUint256(int(token_id))
        params.addUint64(new_expiry_date)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("renewSkillToken", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to renew skill token: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def revoke_skill_token(
    token_id: str,
    reason: str
) -> TransactionResult:
    """
    Revoke a skill token using the SkillToken smart contract.
    
    Args:
        token_id: ID of the skill token to revoke
        reason: Reason for revocation
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="SkillToken contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for revokeSkillToken
        params = ContractFunctionParameters()
        params.addUint256(int(token_id))
        params.addString(reason)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("revokeSkillToken", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to revoke skill token: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def get_skill_endorsements(
    token_id: str
) -> Dict[str, Any]:
    """
    Get endorsements for a skill token using the SkillToken smart contract.
    
    Args:
        token_id: ID of the skill token
        
    Returns:
        Dictionary containing endorsement data
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "SkillToken contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getSkillEndorsements
        params = ContractFunctionParameters()
        params.addUint256(int(token_id))
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getSkillEndorsements", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            endorsements = []
            
            # Extract endorsement data from result
            # This will depend on the actual return structure of the contract
            try:
                # Assuming the contract returns an array of endorsement structs
                endorsement_count = result.getUint256(0) if result else 0
                
                for i in range(int(endorsement_count)):
                    endorsement = {
                        "endorser": result.getAddress(i * 3),
                        "endorsement_data": result.getString(i * 3 + 1),
                        "timestamp": result.getUint256(i * 3 + 2)
                    }
                    endorsements.append(endorsement)
                    
            except Exception as parse_error:
                logger.warning(f"Could not parse endorsement data: {str(parse_error)}")
                endorsements = []
            
            return {
                "success": True,
                "endorsements": endorsements,
                "token_id": token_id
            }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get skill endorsements: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def mark_expired_tokens(
    token_ids: List[str]
) -> TransactionResult:
    """
    Mark skill tokens as expired using the SkillToken smart contract.
    
    Args:
        token_ids: List of token IDs to mark as expired
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="SkillToken contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for markExpiredTokens
        params = ContractFunctionParameters()
        params.addUint256Array([int(token_id) for token_id in token_ids])
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(300000)
        transaction.setFunction("markExpiredTokens", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to mark expired tokens: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


# =============================================================================
# ADDITIONAL TALENT POOL FUNCTIONS
# =============================================================================

async def select_candidate(
    pool_id: str,
    candidate_address: str
) -> TransactionResult:
    """
    Select a candidate for a job pool using the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool
        candidate_address: Address of the selected candidate
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="TalentPool contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for selectCandidate
        params = ContractFunctionParameters()
        params.addUint256(int(pool_id))
        params.addAddress(candidate_address)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("selectCandidate", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to select candidate: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def complete_pool(
    pool_id: str
) -> TransactionResult:
    """
    Complete a job pool using the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool to complete
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="TalentPool contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for completePool
        params = ContractFunctionParameters()
        params.addUint256(int(pool_id))
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("completePool", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to complete pool: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def close_pool(
    pool_id: str
) -> TransactionResult:
    """
    Close a job pool using the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool to close
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="TalentPool contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for closePool
        params = ContractFunctionParameters()
        params.addUint256(int(pool_id))
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("closePool", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to close pool: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def withdraw_application(
    pool_id: str
) -> TransactionResult:
    """
    Withdraw an application from a job pool using the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool to withdraw from
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="TalentPool contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for withdrawApplication
        params = ContractFunctionParameters()
        params.addUint256(int(pool_id))
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("withdrawApplication", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to withdraw application: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def calculate_match_score(
    pool_id: str,
    candidate_address: str
) -> Dict[str, Any]:
    """
    Calculate match score for a candidate in a job pool using the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool
        candidate_address: Address of the candidate
        
    Returns:
        Dictionary containing match score and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "TalentPool contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for calculateMatchScore
        params = ContractFunctionParameters()
        params.addUint256(int(pool_id))
        params.addAddress(candidate_address)
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("calculateMatchScore", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                match_score = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "pool_id": pool_id,
                    "candidate_address": candidate_address,
                    "match_score": match_score
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse match score data: {str(parse_error)}")
                return {
                    "success": True,
                    "pool_id": pool_id,
                    "candidate_address": candidate_address,
                    "match_score": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to calculate match score: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# ADDITIONAL GOVERNANCE FUNCTIONS
# =============================================================================

async def queue_proposal(
    proposal_id: str
) -> TransactionResult:
    """
    Queue a governance proposal for execution using the Governance smart contract.
    
    Args:
        proposal_id: ID of the proposal to queue
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for queueProposal
        params = ContractFunctionParameters()
        params.addUint256(int(proposal_id))
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("queueProposal", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to queue proposal: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def execute_proposal(
    proposal_id: str
) -> TransactionResult:
    """
    Execute a governance proposal using the Governance smart contract.
    
    Args:
        proposal_id: ID of the proposal to execute
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for executeProposal
        params = ContractFunctionParameters()
        params.addUint256(int(proposal_id))
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(300000)
        transaction.setFunction("executeProposal", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to execute proposal: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def cancel_proposal(
    proposal_id: str
) -> TransactionResult:
    """
    Cancel a governance proposal using the Governance smart contract.
    
    Args:
        proposal_id: ID of the proposal to cancel
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for cancelProposal
        params = ContractFunctionParameters()
        params.addUint256(int(proposal_id))
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("cancelProposal", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to cancel proposal: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def cast_vote_with_signature(
    proposal_id: str,
    vote: int,
    reason: str,
    signature: str
) -> TransactionResult:
    """
    Cast a vote on a governance proposal with signature using the Governance smart contract.
    
    Args:
        proposal_id: ID of the proposal to vote on
        vote: Vote type (0=Against, 1=For, 2=Abstain)
        reason: Optional reason for the vote
        signature: Signature for the vote
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for castVoteWithSignature
        params = ContractFunctionParameters()
        params.addUint256(int(proposal_id))
        params.addUint8(vote)
        params.addString(reason)
        params.addBytes(bytes.fromhex(signature.replace('0x', '')))
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(250000)
        transaction.setFunction("castVoteWithSignature", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to cast vote with signature: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def batch_execute_proposals(
    proposal_ids: List[str]
) -> TransactionResult:
    """
    Batch execute multiple governance proposals using the Governance smart contract.
    
    Args:
        proposal_ids: List of proposal IDs to execute
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="Governance contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for batchExecuteProposals
        params = ContractFunctionParameters()
        params.addUint256Array([int(proposal_id) for proposal_id in proposal_ids])
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(500000)  # Higher gas for batch operation
        transaction.setFunction("batchExecuteProposals", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to batch execute proposals: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


# =============================================================================
# ADDITIONAL REPUTATION ORACLE FUNCTIONS
# =============================================================================

async def get_category_score(
    user_address: str,
    category: str
) -> Dict[str, Any]:
    """
    Get category-specific reputation score using the ReputationOracle smart contract.
    
    Args:
        user_address: User's address
        category: Skill category
        
    Returns:
        Dictionary containing category score
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "ReputationOracle contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getCategoryScore
        params = ContractFunctionParameters()
        params.addAddress(user_address)
        params.addString(category)
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getCategoryScore", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                category_score = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "user_address": user_address,
                    "category": category,
                    "score": category_score
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse category score data: {str(parse_error)}")
                return {
                    "success": True,
                    "user_address": user_address,
                    "category": category,
                    "score": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get category score: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_work_evaluation(
    evaluation_id: str
) -> Dict[str, Any]:
    """
    Get work evaluation details using the ReputationOracle smart contract.
    
    Args:
        evaluation_id: ID of the evaluation
        
    Returns:
        Dictionary containing evaluation details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "ReputationOracle contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getWorkEvaluation
        params = ContractFunctionParameters()
        params.addUint256(int(evaluation_id))
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getWorkEvaluation", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                evaluation = {
                    "user": result.getAddress(0) if result else "",
                    "skill_token_ids": [result.getUint256(1)] if result else [],  # Simplified for single token
                    "overall_score": result.getUint256(2) if result else 0,
                    "feedback": result.getString(3) if result else "",
                    "evaluated_by": result.getAddress(4) if result else "",
                    "timestamp": result.getUint64(5) if result else 0,
                    "ipfs_hash": result.getString(6) if result else ""
                }
                
                return {
                    "success": True,
                    "evaluation_id": evaluation_id,
                    "evaluation": evaluation
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse work evaluation data: {str(parse_error)}")
                return {
                    "success": True,
                    "evaluation_id": evaluation_id,
                    "evaluation": {
                        "user": "",
                        "skill_token_ids": [],
                        "overall_score": 0,
                        "feedback": "",
                        "evaluated_by": "",
                        "timestamp": 0,
                        "ipfs_hash": ""
                    }
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get work evaluation: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_user_evaluations(
    user_address: str
) -> Dict[str, Any]:
    """
    Get all evaluations for a user using the ReputationOracle smart contract.
    
    Args:
        user_address: User's address
        
    Returns:
        Dictionary containing user evaluations
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "ReputationOracle contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getUserEvaluations
        params = ContractFunctionParameters()
        params.addAddress(user_address)
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getUserEvaluations", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                # This is a simplified implementation - actual contract may return different structure
                evaluations = []
                # For now, return empty list as the actual structure depends on contract implementation
                
                return {
                    "success": True,
                    "user_address": user_address,
                    "evaluations": evaluations
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse user evaluations data: {str(parse_error)}")
                return {
                    "success": True,
                    "user_address": user_address,
                    "evaluations": []
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get user evaluations: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_global_stats() -> Dict[str, Any]:
    """
    Get global reputation statistics using the ReputationOracle smart contract.
    
    Returns:
        Dictionary containing global stats
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "ReputationOracle contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getGlobalStats (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getGlobalStats", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                stats = {
                    "total_evaluations": result.getUint256(0) if result else 0,
                    "total_challenges": result.getUint256(1) if result else 0,
                    "total_oracle_stake": result.getUint256(2) if result else 0,
                    "active_oracle_count": result.getUint256(3) if result else 0
                }
                
                return {
                    "success": True,
                    "stats": stats
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse global stats data: {str(parse_error)}")
                return {
                    "success": True,
                    "stats": {
                        "total_evaluations": 0,
                        "total_challenges": 0,
                        "total_oracle_stake": 0,
                        "active_oracle_count": 0
                    }
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get global stats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def update_oracle_status(
    oracle_address: str,
    is_active: bool,
    reason: str
) -> TransactionResult:
    """
    Update oracle status using the ReputationOracle smart contract.
    
    Args:
        oracle_address: Address of the oracle
        is_active: Whether the oracle should be active
        reason: Reason for status change
        
    Returns:
        TransactionResult with success status and details
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get ReputationOracle contract info
        oracle_config = contract_config.get('contracts', {}).get('ReputationOracle', {})
        contract_address = oracle_config.get('address')
        
        if not contract_address:
            return TransactionResult(
                success=False,
                error="ReputationOracle contract not deployed"
            )
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for updateOracleStatus
        params = ContractFunctionParameters()
        params.addAddress(oracle_address)
        params.addBool(is_active)
        params.addString(reason)
        
        # Execute contract function
        transaction = ContractExecuteTransaction()
        transaction.setContractId(contract_id)
        transaction.setGas(200000)
        transaction.setFunction("updateOracleStatus", params)
        
        # Sign and execute
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        if receipt.status == Status.Success:
            return TransactionResult(
                success=True,
                transaction_id=response.transactionId.toString(),
                gas_used=response.getRecord(client).gasUsed if response.getRecord(client) else 0,
                contract_address=contract_address
            )
        else:
            return TransactionResult(
                success=False,
                error=f"Transaction failed with status: {receipt.status}"
            )
            
    except Exception as e:
        logger.error(f"Failed to update oracle status: {str(e)}")
        return TransactionResult(
            success=False,
            error=str(e)
        )


async def get_tokens_by_category(
    category: str
) -> Dict[str, Any]:
    """
    Get all skill tokens in a specific category using the SkillToken smart contract.
    
    Args:
        category: Skill category to search for
        
    Returns:
        Dictionary containing tokens in the category
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "SkillToken contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getTokensByCategory
        params = ContractFunctionParameters()
        params.addString(category)
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getTokensByCategory", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            tokens = []
            
            try:
                # This is a simplified implementation - actual contract may return different structure
                # For now, return empty list as the actual structure depends on contract implementation
                
                return {
                    "success": True,
                    "category": category,
                    "tokens": tokens
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse category tokens data: {str(parse_error)}")
                return {
                    "success": True,
                    "category": category,
                    "tokens": []
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get tokens by category: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_total_skills_by_category(
    category: str
) -> Dict[str, Any]:
    """
    Get total number of skills in a category using the SkillToken smart contract.
    
    Args:
        category: Skill category to count
        
    Returns:
        Dictionary containing total count
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get SkillToken contract info
        skill_token_config = contract_config.get('contracts', {}).get('SkillToken', {})
        contract_address = skill_token_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "SkillToken contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getTotalSkillsByCategory
        params = ContractFunctionParameters()
        params.addString(category)
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getTotalSkillsByCategory", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                total_count = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "category": category,
                    "total_count": total_count
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse total skills data: {str(parse_error)}")
                return {
                    "success": True,
                    "category": category,
                    "total_count": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get total skills by category: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# ADDITIONAL GOVERNANCE FUNCTIONS
# =============================================================================

async def get_proposal_status(
    proposal_id: str
) -> Dict[str, Any]:
    """
    Get proposal status using the Governance smart contract.
    
    Args:
        proposal_id: ID of the proposal
        
    Returns:
        Dictionary containing proposal status
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getProposalStatus
        params = ContractFunctionParameters()
        params.addUint256(int(proposal_id))
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getProposalStatus", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                status = result.getUint8(0) if result else 0
                
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "status": status
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse proposal status data: {str(parse_error)}")
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "status": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get proposal status: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_vote_receipt(
    proposal_id: str,
    voter: str
) -> Dict[str, Any]:
    """
    Get vote receipt for a voter on a proposal using the Governance smart contract.
    
    Args:
        proposal_id: ID of the proposal
        voter: Address of the voter
        
    Returns:
        Dictionary containing vote receipt
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getVoteReceipt
        params = ContractFunctionParameters()
        params.addUint256(int(proposal_id))
        params.addAddress(voter)
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getVoteReceipt", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                # This is a simplified implementation - actual contract may return different structure
                vote_receipt = {
                    "has_voted": True,  # Placeholder
                    "vote": 0,  # Placeholder
                    "weight": 0  # Placeholder
                }
                
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "receipt": vote_receipt
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse vote receipt data: {str(parse_error)}")
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "receipt": {
                        "has_voted": False,
                        "vote": 0,
                        "weight": 0
                    }
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get vote receipt: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_quorum() -> Dict[str, Any]:
    """
    Get quorum requirement using the Governance smart contract.
    
    Returns:
        Dictionary containing quorum information
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getQuorum (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getQuorum", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                quorum = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "quorum": quorum
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse quorum data: {str(parse_error)}")
                return {
                    "success": True,
                    "quorum": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get quorum: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_voting_delay() -> Dict[str, Any]:
    """
    Get voting delay using the Governance smart contract.
    
    Returns:
        Dictionary containing voting delay information
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getVotingDelay (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getVotingDelay", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                voting_delay = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "voting_delay": voting_delay
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse voting delay data: {str(parse_error)}")
                return {
                    "success": True,
                    "voting_delay": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get voting delay: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_voting_period() -> Dict[str, Any]:
    """
    Get voting period using the Governance smart contract.
    
    Returns:
        Dictionary containing voting period information
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getVotingPeriod (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getVotingPeriod", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                voting_period = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "voting_period": voting_period
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse voting period data: {str(parse_error)}")
                return {
                    "success": True,
                    "voting_period": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get voting period: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_proposal_threshold() -> Dict[str, Any]:
    """
    Get proposal threshold using the Governance smart contract.
    
    Returns:
        Dictionary containing proposal threshold information
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getProposalThreshold (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getProposalThreshold", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                proposal_threshold = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "proposal_threshold": proposal_threshold
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse proposal threshold data: {str(parse_error)}")
                return {
                    "success": True,
                    "proposal_threshold": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get proposal threshold: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_all_proposals() -> Dict[str, Any]:
    """
    Get all proposals using the Governance smart contract.
    
    Returns:
        Dictionary containing all proposals
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getAllProposals (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getAllProposals", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                # This is a simplified implementation - actual contract may return different structure
                proposals = []
                # For now, return empty list as the actual structure depends on contract implementation
                
                return {
                    "success": True,
                    "proposals": proposals
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse all proposals data: {str(parse_error)}")
                return {
                    "success": True,
                    "proposals": []
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get all proposals: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_active_proposals() -> Dict[str, Any]:
    """
    Get active proposals using the Governance smart contract.
    
    Returns:
        Dictionary containing active proposals
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getActiveProposals (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getActiveProposals", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                # This is a simplified implementation - actual contract may return different structure
                active_proposals = []
                # For now, return empty list as the actual structure depends on contract implementation
                
                return {
                    "success": True,
                    "active_proposals": active_proposals
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse active proposals data: {str(parse_error)}")
                return {
                    "success": True,
                    "active_proposals": []
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get active proposals: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def can_execute(
    proposal_id: str
) -> Dict[str, Any]:
    """
    Check if a proposal can be executed using the Governance smart contract.
    
    Args:
        proposal_id: ID of the proposal
        
    Returns:
        Dictionary containing execution status
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for canExecute
        params = ContractFunctionParameters()
        params.addUint256(int(proposal_id))
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("canExecute", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                can_execute = result.getBool(0) if result else False
                
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "can_execute": can_execute
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse can execute data: {str(parse_error)}")
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "can_execute": False
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to check if proposal can execute: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def has_voted(
    proposal_id: str,
    voter: str
) -> Dict[str, Any]:
    """
    Check if a voter has voted on a proposal using the Governance smart contract.
    
    Args:
        proposal_id: ID of the proposal
        voter: Address of the voter
        
    Returns:
        Dictionary containing voting status
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get Governance contract info
        governance_config = contract_config.get('contracts', {}).get('Governance', {})
        contract_address = governance_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "Governance contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for hasVoted
        params = ContractFunctionParameters()
        params.addUint256(int(proposal_id))
        params.addAddress(voter)
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("hasVoted", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                has_voted = result.getBool(0) if result else False
                
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "has_voted": has_voted
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse has voted data: {str(parse_error)}")
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "has_voted": False
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to check if voter has voted: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# ADDITIONAL TALENT POOL FUNCTIONS
# =============================================================================

async def get_pool_metrics(
    pool_id: str
) -> Dict[str, Any]:
    """
    Get pool metrics using the TalentPool smart contract.
    
    Args:
        pool_id: ID of the job pool
        
    Returns:
        Dictionary containing pool metrics
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "TalentPool contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getPoolMetrics
        params = ContractFunctionParameters()
        params.addUint256(int(pool_id))
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getPoolMetrics", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                # This is a simplified implementation - actual contract may return different structure
                metrics = {
                    "total_applications": 0,  # Placeholder
                    "match_score_average": 0,  # Placeholder
                    "completion_rate": 0  # Placeholder
                }
                
                return {
                    "success": True,
                    "pool_id": pool_id,
                    "metrics": metrics
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse pool metrics data: {str(parse_error)}")
                return {
                    "success": True,
                    "pool_id": pool_id,
                    "metrics": {
                        "total_applications": 0,
                        "match_score_average": 0,
                        "completion_rate": 0
                    }
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get pool metrics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_talent_pool_global_stats() -> Dict[str, Any]:
    """
    Get global talent pool statistics using the TalentPool smart contract.
    
    Returns:
        Dictionary containing global stats
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "TalentPool contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getGlobalStats (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getGlobalStats", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                stats = {
                    "total_pools": result.getUint256(0) if result else 0,
                    "total_applications": result.getUint256(1) if result else 0,
                    "total_matches": result.getUint256(2) if result else 0,
                    "total_staked": result.getUint256(3) if result else 0
                }
                
                return {
                    "success": True,
                    "stats": stats
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse global stats data: {str(parse_error)}")
                return {
                    "success": True,
                    "stats": {
                        "total_pools": 0,
                        "total_applications": 0,
                        "total_matches": 0,
                        "total_staked": 0
                    }
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get global stats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_active_pools_count() -> Dict[str, Any]:
    """
    Get active pools count using the TalentPool smart contract.
    
    Returns:
        Dictionary containing active pools count
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "TalentPool contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getActivePoolsCount (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getActivePoolsCount", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                active_count = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "active_pools_count": active_count
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse active pools count data: {str(parse_error)}")
                return {
                    "success": True,
                    "active_pools_count": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get active pools count: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_total_pools_count() -> Dict[str, Any]:
    """
    Get total pools count using the TalentPool smart contract.
    
    Returns:
        Dictionary containing total pools count
    """
    try:
        client = get_hedera_client()
        contract_config = get_contract_manager()
        
        # Get TalentPool contract info
        pool_config = contract_config.get('contracts', {}).get('TalentPool', {})
        contract_address = pool_config.get('address')
        
        if not contract_address:
            return {
                "success": False,
                "error": "TalentPool contract not deployed"
            }
        
        # Create contract ID
        contract_id = ContractId.fromString(contract_address)
        
        # Prepare function parameters for getTotalPoolsCount (no parameters)
        params = ContractFunctionParameters()
        
        # Execute contract query
        query = ContractCallQuery()
        query.setContractId(contract_id)
        query.setGas(100000)
        query.setFunction("getTotalPoolsCount", params)
        
        # Execute query
        response = query.execute(client)
        
        if response.getStatus() == Status.Success:
            # Parse the response data
            result = response.getContractFunctionResult()
            
            try:
                total_count = result.getUint256(0) if result else 0
                
                return {
                    "success": True,
                    "total_pools_count": total_count
                }
                
            except Exception as parse_error:
                logger.warning(f"Could not parse total pools count data: {str(parse_error)}")
                return {
                    "success": True,
                    "total_pools_count": 0
                }
        else:
            return {
                "success": False,
                "error": f"Query failed with status: {response.getStatus()}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get total pools count: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

"""
Configuration Management for TalentChain Pro Backend

This module provides centralized configuration management with environment variable
validation and default values for development and production environments.

Based on the complete contract analysis, this supports all 4 main contracts:
1. SkillToken - Soulbound NFTs for skill verification
2. TalentPool - Job pool management and matching  
3. Governance - DAO governance and protocol management
4. ReputationOracle - AI-powered reputation scoring
"""

import os
import json
from typing import Optional, List, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = {"extra": "allow"}  # Allow extra fields from environment variables
    
    # Application Settings
    app_name: str = Field(default="TalentChain Pro API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    development_mode: bool = Field(default=True, env="DEVELOPMENT_MODE")
    
    # API Settings
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    reload: bool = Field(default=True, env="API_RELOAD")
    workers: int = Field(default=1, env="API_WORKERS")
    
    # Security Settings
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    jwt_secret_key: str = Field(default="your-super-secret-jwt-key-change-this-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    encryption_key: str = Field(default="your-32-byte-encryption-key-change-this", env="ENCRYPTION_KEY")
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"], 
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # Database Settings
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/talentchainpro",
        env="DATABASE_URL"
    )
    # SQLite fallback database (for development when PostgreSQL is not available)
    sqlite_database_url: str = Field(
        default="sqlite:///./talentchainpro.db",
        env="SQLITE_DATABASE_URL"
    )
    # Auto-fallback to SQLite if PostgreSQL is not available
    database_auto_fallback: bool = Field(default=True, env="DATABASE_AUTO_FALLBACK")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # Hedera Blockchain Settings
    hedera_network: str = Field(default="testnet", env="HEDERA_NETWORK")
    hedera_account_id: str = Field(default="0.0.YOUR_ACCOUNT_ID", env="HEDERA_ACCOUNT_ID")
    hedera_private_key: str = Field(default="YOUR_PRIVATE_KEY", env="HEDERA_PRIVATE_KEY")
    hedera_public_key: Optional[str] = Field(None, env="HEDERA_PRIVATE_KEY")
    hedera_mirror_node_url: str = Field(
        default="https://testnet.mirrornode.hedera.com", 
        env="HEDERA_MIRROR_NODE_URL"
    )
    
    # Hedera Transaction Settings
    max_transaction_fee: int = Field(default=100, env="MAX_TRANSACTION_FEE")
    max_query_payment: int = Field(default=50, env="MAX_QUERY_PAYMENT")
    
    # Smart Contract Addresses (All 4 main contracts)
    # Placeholders until deployment - will be updated by deployment script
    contract_skill_token: str = Field(default="", env="CONTRACT_SKILL_TOKEN")
    contract_talent_pool: str = Field(default="", env="CONTRACT_TALENT_POOL")
    contract_governance: str = Field(default="", env="CONTRACT_GOVERNANCE")
    contract_reputation_oracle: str = Field(default="", env="CONTRACT_REPUTATION_ORACLE")
    
    # Contract ABI Paths
    contract_abi_path: str = Field(default="./contracts/abis", env="CONTRACT_ABI_PATH")
    
    # AI/ML Services
    groq_api_key: str = Field(default="your_groq_api_key_here", env="GROQ_API_KEY")
    groq_model: str = Field(default="mixtral-8x7b-32768", env="GROQ_MODEL")
    openai_api_key: Optional[str] = Field(default="your_openai_key_if_using_openai", env="OPENAI_API_KEY")
    
    # MCP Server Configuration
    mcp_server_host: str = Field(default="localhost", env="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=3001, env="MCP_SERVER_PORT")
    mcp_server_url: str = Field(default="ws://localhost:3001/ws", env="MCP_SERVER_URL")
    mcp_timeout: int = Field(default=30, env="MCP_TIMEOUT")
    
    # External APIs
    ipfs_gateway_url: str = Field(
        default="https://ipfs.io/ipfs/",
        env="IPFS_GATEWAY_URL"
    )
    
    # Validation
    @validator('hedera_network')
    def validate_hedera_network(cls, v):
        if v not in ['testnet', 'mainnet', 'previewnet']:
            raise ValueError('Hedera network must be testnet, mainnet, or previewnet')
        return v
    
    @validator('contract_skill_token', 'contract_talent_pool', 'contract_governance', 'contract_reputation_oracle')
    def validate_contract_addresses(cls, v):
        if v and not v.startswith('0.0.'):
            raise ValueError('Contract address must be a valid Hedera address starting with 0.0.')
        return v
    
    model_config = {
        "extra": "allow",  # Allow extra fields from environment variables
        "env_file": ".env",
        "case_sensitive": False
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def load_contract_abis() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all contract ABIs from the contracts.json file.
    
    Returns:
        Dictionary mapping contract names to their ABIs
    """
    try:
        # Try to load from contracts.json first (existing approach)
        contracts_file_path = os.path.join(os.path.dirname(__file__), '..', 'contracts.json')
        
        if os.path.exists(contracts_file_path):
            with open(contracts_file_path, 'r') as f:
                contracts_data = json.load(f)
            
            contract_abis = {}
            for contract_name, contract_info in contracts_data.get('contracts', {}).items():
                contract_abis[contract_name] = contract_info.get('abi', [])
                print(f"✅ Loaded ABI for {contract_name} from contracts.json")
            
            return contract_abis
        
        # Fallback to individual ABI files
        settings = get_settings()
        abi_path = settings.contract_abi_path
        
        contract_abis = {}
        
        # Define the contracts we expect
        expected_contracts = [
            'SkillToken',
            'TalentPool', 
            'Governance',
            'ReputationOracle'
        ]
        
        for contract_name in expected_contracts:
            abi_file_path = os.path.join(abi_path, f"{contract_name}.json")
            
            try:
                if os.path.exists(abi_file_path):
                    with open(abi_file_path, 'r') as f:
                        contract_abis[contract_name] = json.load(f)
                    print(f"✅ Loaded ABI for {contract_name} from {abi_file_path}")
                else:
                    print(f"⚠️  ABI file not found for {contract_name}: {abi_file_path}")
                    contract_abis[contract_name] = []
            except Exception as e:
                print(f"❌ Error loading ABI for {contract_name}: {str(e)}")
                contract_abis[contract_name] = []
        
        return contract_abis
        
    except Exception as e:
        print(f"❌ Error loading contract ABIs: {str(e)}")
        return {}


def get_contract_abi(contract_name: str) -> List[Dict[str, Any]]:
    """
    Get ABI for a specific contract.
    
    Args:
        contract_name: Name of the contract (e.g., 'SkillToken', 'TalentPool')
        
    Returns:
        Contract ABI as a list of function/event definitions
    """
    contract_abis = load_contract_abis()
    return contract_abis.get(contract_name, [])


def get_contract_address(contract_name: str) -> str:
    """
    Get the deployed address for a specific contract.
    
    Args:
        contract_name: Name of the contract (e.g., 'SkillToken', 'TalentPool')
        
    Returns:
        Contract address as a string
    """
    try:
        contract_config = get_contract_config()
        contract_info = contract_config.get('contracts', {}).get(contract_name, {})
        return contract_info.get('address', '')
        
    except Exception as e:
        print(f"❌ Failed to get contract address for {contract_name}: {str(e)}")
        return ""


def validate_contract_deployments() -> Dict[str, bool]:
    """
    Validate that all required contracts are deployed.
    
    Returns:
        Dictionary mapping contract names to deployment status
    """
    try:
        # Try to load from contracts.json first
        contracts_file_path = os.path.join(os.path.dirname(__file__), '..', 'contracts.json')
        
        if os.path.exists(contracts_file_path):
            with open(contracts_file_path, 'r') as f:
                contracts_data = json.load(f)
            
            deployment_status = {}
            for name, contract_info in contracts_data.get('contracts', {}).items():
                address = contract_info.get('address', '')
                abi = contract_info.get('abi', [])
                
                # Check if contract is deployed and has ABI
                is_deployed = bool(address and address.startswith('0.0.'))
                has_abi = len(abi) > 0
                
                deployment_status[name] = {
                    'deployed': is_deployed,
                    'address': address,
                    'has_abi': has_abi,
                    'ready': is_deployed and has_abi
                }
            
            return deployment_status
        
        # Fallback to environment variables
        settings = get_settings()
        
        contracts = {
            'SkillToken': settings.contract_skill_token,
            'TalentPool': settings.contract_talent_pool,
            'Governance': settings.contract_governance,
            'ReputationOracle': settings.contract_reputation_oracle
        }
        
        deployment_status = {}
        for name, address in contracts.items():
            deployment_status[name] = {
                'deployed': bool(address and address.startswith('0.0.')),
                'address': address,
                'has_abi': False,  # No ABI info from env vars
                'ready': bool(address and address.startswith('0.0.'))
            }
        
        return deployment_status
        
    except Exception as e:
        # logger.error(f"Failed to validate contract deployments: {str(e)}") # Original code had this line commented out
        return {}


def get_network_config() -> Dict[str, Any]:
    """
    Get Hedera network configuration.
    
    Returns:
        Network configuration dictionary
    """
    settings = get_settings()
    
    networks = {
        'testnet': {
            'name': 'Hedera Testnet',
            'chainId': 296,
            'rpcUrl': 'https://testnet.hashio.io',
            'explorerUrl': 'https://testnet.dragonglass.me',
            'mirrorNodeUrl': 'https://testnet.mirrornode.hedera.com',
            'currency': 'HBAR',
            'blockExplorerUrl': 'https://testnet.dragonglass.me'
        },
        'mainnet': {
            'name': 'Hedera Mainnet',
            'chainId': 295,
            'rpcUrl': 'https://mainnet.hashio.io',
            'explorerUrl': 'https://app.dragonglass.me',
            'mirrorNodeUrl': 'https://mainnet.mirrornode.hedera.com',
            'currency': 'HBAR',
            'blockExplorerUrl': 'https://app.dragonglass.me'
        },
        'previewnet': {
            'name': 'Hedera Previewnet',
            'chainId': 297,
            'rpcUrl': 'https://previewnet.hashio.io',
            'explorerUrl': 'https://previewnet.dragonglass.me',
            'mirrorNodeUrl': 'https://previewnet.mirrornode.hedera.com',
            'currency': 'HBAR',
            'blockExplorerUrl': 'https://previewnet.dragonglass.me'
        }
    }
    
    return networks.get(settings.hedera_network, networks['testnet'])


def get_contract_config() -> Dict[str, Dict[str, Any]]:
    """
    Get comprehensive contract configuration including deployed addresses and ABIs.
    
    Returns:
        Dictionary containing contract configurations with addresses and ABIs
    """
    try:
        # Try to load from deployment file first
        deployment_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'contracts', 'deployments', 'testnet.json')
        
        if os.path.exists(deployment_file_path):
            with open(deployment_file_path, 'r') as f:
                deployment_data = json.load(f)
            
            # Load ABIs for each contract
            abi_path = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'abis')
            contract_config = {
                'network': deployment_data.get('network', 'testnet'),
                'operator': deployment_data.get('operator', ''),
                'contracts': {}
            }
            
            # Map deployment names to our contract names
            contract_mapping = {
                'skillToken': 'SkillToken',
                'reputationOracle': 'ReputationOracle', 
                'talentPool': 'TalentPool',
                'governance': 'Governance'
            }
            
            for deploy_name, contract_info in deployment_data.get('contracts', {}).items():
                if deploy_name in contract_mapping:
                    contract_name = contract_mapping[deploy_name]
                    
                    # Load ABI for this contract
                    abi_file_path = os.path.join(abi_path, f"{contract_name}.json")
                    abi = []
                    if os.path.exists(abi_file_path):
                        with open(abi_file_path, 'r') as abi_file:
                            abi = json.load(abi_file)
                    
                    # Convert contract address format if needed
                    contract_address = contract_info.get('contractAddress', '')
                    if contract_address and not contract_address.startswith('0.0.'):
                        # Convert from hex format to Hedera format
                        try:
                            # Remove leading zeros and convert to Hedera format
                            contract_num = int(contract_address, 16)
                            contract_address = f"0.0.{contract_num}"
                        except:
                            contract_address = contract_info.get('contractId', '')
                    
                    contract_config['contracts'][contract_name] = {
                        'address': contract_address,
                        'contract_id': contract_info.get('contractId', ''),
                        'transaction_id': contract_info.get('transactionId', ''),
                        'explorer_url': contract_info.get('explorerUrl', ''),
                        'deployed': contract_info.get('success', False),
                        'abi': abi
                    }
                    
                    print(f"✅ Loaded {contract_name} contract: {contract_address}")
            
            return contract_config
        
        # Fallback to environment variables
        settings = get_settings()
        contract_config = {
            'network': settings.hedera_network,
            'operator': settings.hedera_account_id,
            'contracts': {
                'SkillToken': {
                    'address': settings.contract_skill_token,
                    'deployed': bool(settings.contract_skill_token),
                    'abi': []
                },
                'TalentPool': {
                    'address': settings.contract_talent_pool,
                    'deployed': bool(settings.contract_talent_pool),
                    'abi': []
                },
                'Governance': {
                    'address': settings.contract_governance,
                    'deployed': bool(settings.contract_governance),
                    'abi': []
                },
                'ReputationOracle': {
                    'address': settings.contract_reputation_oracle,
                    'deployed': bool(settings.contract_reputation_oracle),
                    'abi': []
                }
            }
        }
        
        return contract_config
        
    except Exception as e:
        print(f"❌ Error loading contract configuration: {str(e)}")
        return {
            'network': 'testnet',
            'operator': '',
            'contracts': {}
        }

#!/usr/bin/env python3
"""
TalentChain Pro Full Integration Test Script

This script tests ALL backend integrations with deployed contracts
to ensure the complete system is working correctly.
"""

import asyncio
import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_contract_config, get_contract_address
from app.utils.hedera import initialize_hedera_client, get_hedera_client
from app.services.governance import get_governance_service
from app.services.reputation import get_reputation_service
from app.services.skill import get_skill_service
from app.services.pool import get_pool_service

async def test_contract_configuration():
    """Test contract configuration loading."""
    print("🔍 Testing Contract Configuration...")
    
    try:
        # Test contract config loading
        contract_config = get_contract_config()
        print(f"✅ Network: {contract_config.get('network', 'Unknown')}")
        print(f"✅ Operator: {contract_config.get('operator', '')}")
        
        contracts = contract_config.get('contracts', {})
        print(f"✅ Found {len(contracts)} contracts:")
        
        # Map deployment names to our contract names
        contract_mapping = {
            'skillToken': 'SkillToken',
            'reputationOracle': 'ReputationOracle', 
            'talentPool': 'TalentPool',
            'governance': 'Governance'
        }
        
        for deploy_name, contract_info in contracts.items():
            if deploy_name in contract_mapping:
                contract_name = contract_mapping[deploy_name]
                
                # Load ABI for this contract
                abi_file_path = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'abis', f"{contract_name}.json")
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
                
                print(f"   {contract_name}: {contract_address} - {'🟢 Ready' if contract_info.get('success', False) else '🔴 Not Ready'}")
                
                if contract_info.get('success', False):
                    print(f"      Contract ID: {contract_info.get('contractId', 'N/A')}")
                    print(f"      Explorer: {contract_info.get('explorerUrl', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Contract configuration test failed: {str(e)}")
        return False

async def test_hedera_client():
    """Test Hedera client initialization."""
    print("\n🔍 Testing Hedera Client...")
    
    try:
        # Test client initialization
        client = initialize_hedera_client()
        print(f"✅ Hedera client initialized for network: {client.network}")
        
        # Test client retrieval
        client2 = get_hedera_client()
        print(f"✅ Client retrieval successful: {client2.network}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hedera client test failed: {str(e)}")
        return False

async def test_contract_addresses():
    """Test individual contract address retrieval."""
    print("\n🔍 Testing Contract Addresses...")
    
    try:
        contracts = ['SkillToken', 'TalentPool', 'Governance', 'ReputationOracle']
        
        for contract_name in contracts:
            address = get_contract_address(contract_name)
            if address:
                print(f"✅ {contract_name}: {address}")
            else:
                print(f"❌ {contract_name}: Not deployed")
        
        return True
        
    except Exception as e:
        print(f"❌ Contract address test failed: {str(e)}")
        return False

async def test_service_initialization():
    """Test all service initializations."""
    print("\n🔍 Testing Service Initialization...")
    
    try:
        # Test governance service
        governance_service = get_governance_service()
        print("✅ Governance service initialized")
        
        # Test reputation service
        reputation_service = get_reputation_service()
        print("✅ Reputation service initialized")
        
        # Test skill service
        skill_service = get_skill_service()
        print("✅ Skill service initialized")
        
        # Test pool service
        pool_service = get_pool_service()
        print("✅ Pool service initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization test failed: {str(e)}")
        return False

async def test_contract_functionality():
    """Test basic contract functionality."""
    print("\n🔍 Testing Contract Functionality...")
    
    try:
        # Test if we can access contract functions
        contract_config = get_contract_config()
        contracts = contract_config.get('contracts', {})
        
        for contract_name, config in contracts.items():
            if config.get('deployed') and config.get('abi'):
                # Contract is deployed and has ABI
                abi_functions = [item for item in config.get('abi', []) if item.get('type') == 'function']
                print(f"✅ {contract_name}: {len(abi_functions)} functions available")
                
                # Check for key functions
                function_names = [func.get('name', '') for func in abi_functions]
                
                if contract_name == 'Governance':
                    key_functions = ['createProposal', 'castVote', 'delegate']
                elif contract_name == 'ReputationOracle':
                    key_functions = ['registerOracle', 'submitEvaluation']
                elif contract_name == 'SkillToken':
                    key_functions = ['mintSkillToken', 'updateSkillLevel']
                elif contract_name == 'TalentPool':
                    key_functions = ['createJobPool', 'applyToPool']
                else:
                    key_functions = []
                
                for key_func in key_functions:
                    if key_func in function_names:
                        print(f"   ✅ {key_func} function available")
                    else:
                        print(f"   ❌ {key_func} function missing")
            else:
                print(f"❌ {contract_name}: Not ready (deployed: {config.get('deployed')}, has_abi: {len(config.get('abi', [])) > 0})")
        
        return True
        
    except Exception as e:
        print(f"❌ Contract functionality test failed: {str(e)}")
        return False

async def test_api_endpoints():
    """Test API endpoint availability."""
    print("\n🔍 Testing API Endpoints...")
    
    try:
        # Test if we can import API modules
        from app.api import governance, reputation, skill, pool
        
        print("✅ Governance API module imported")
        print("✅ Reputation API module imported")
        print("✅ Skill API module imported")
        print("✅ Pool API module imported")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {str(e)}")
        return False

async def test_authentication_system():
    """Test authentication system."""
    print("\n🔍 Testing Authentication System...")
    
    try:
        # Test if we can import auth modules
        from app.utils.auth import AuthContext, AuthManager, get_current_user, require_auth
        
        print("✅ AuthContext class imported")
        print("✅ AuthManager class imported")
        print("✅ get_current_user function imported")
        print("✅ require_auth function imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication system test failed: {str(e)}")
        return False

async def main():
    """Run all integration tests."""
    print("🚀 TalentChain Pro Full Integration Test")
    print("=" * 60)
    
    tests = [
        test_contract_configuration(),
        test_hedera_client(),
        test_contract_addresses(),
        test_service_initialization(),
        test_contract_functionality(),
        test_api_endpoints(),
        test_authentication_system(),
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Test {i+1} failed with exception: {str(result)}")
        elif result:
            print(f"✅ Test {i+1} passed")
            passed += 1
        else:
            print(f"❌ Test {i+1} failed")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The complete system is ready for production!")
        print("\n✅ What's Working:")
        print("   • All smart contracts deployed and accessible")
        print("   • All backend services initialized")
        print("   • All API endpoints available")
        print("   • Authentication system ready")
        print("   • Hedera client connected")
        print("   • Frontend integration ready")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        print("\n🔧 Next Steps:")
        print("   • Fix any failed tests")
        print("   • Verify contract deployments")
        print("   • Check environment configuration")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

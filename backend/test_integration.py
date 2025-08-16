#!/usr/bin/env python3
"""
TalentChain Pro Integration Test Script

This script tests the backend integration with deployed contracts
to ensure everything is working correctly.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_contract_config, get_contract_address
from app.utils.hedera import initialize_hedera_client, get_hedera_client

async def test_contract_configuration():
    """Test contract configuration loading."""
    print("🔍 Testing Contract Configuration...")
    
    try:
        # Test contract config loading
        contract_config = get_contract_config()
        print(f"✅ Network: {contract_config.get('network', 'Unknown')}")
        print(f"✅ Operator: {contract_config.get('operator', 'Unknown')}")
        
        contracts = contract_config.get('contracts', {})
        print(f"✅ Found {len(contracts)} contracts:")
        
        for name, info in contracts.items():
            address = info.get('address', 'Not deployed')
            deployed = info.get('deployed', False)
            has_abi = len(info.get('abi', [])) > 0
            
            status = "🟢 Ready" if deployed and has_abi else "🔴 Not Ready"
            print(f"   {name}: {address} - {status}")
            
            if deployed and has_abi:
                print(f"      Contract ID: {info.get('contract_id', 'N/A')}")
                print(f"      Explorer: {info.get('explorer_url', 'N/A')}")
        
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

async def main():
    """Run all integration tests."""
    print("🚀 TalentChain Pro Integration Test")
    print("=" * 50)
    
    tests = [
        test_contract_configuration(),
        test_hedera_client(),
        test_contract_addresses(),
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print("\n" + "=" * 50)
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
        print("🎉 All tests passed! Backend integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
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

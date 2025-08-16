#!/usr/bin/env python3
"""
Contract Analysis Script
Extracts all function names and parameters from contract ABIs for auditing
"""

import json
import os

def analyze_contract_abi(abi_file_path):
    """Analyze a contract ABI and extract function information."""
    with open(abi_file_path, 'r') as f:
        abi = json.load(f)
    
    functions = []
    events = []
    
    for item in abi:
        if item.get('type') == 'function':
            function_info = {
                'name': item.get('name', ''),
                'inputs': [input_param.get('name', '') for input_param in item.get('inputs', [])],
                'outputs': [output_param.get('name', '') for output_param in item.get('outputs', [])],
                'stateMutability': item.get('stateMutability', ''),
                'payable': item.get('payable', False),
                'constant': item.get('constant', False),
                'view': item.get('stateMutability') == 'view',
                'pure': item.get('stateMutability') == 'pure'
            }
            functions.append(function_info)
        elif item.get('type') == 'event':
            event_info = {
                'name': item.get('name', ''),
                'inputs': [input_param.get('name', '') for input_param in item.get('inputs', [])],
                'anonymous': item.get('anonymous', False)
            }
            events.append(event_info)
    
    return {
        'contract_name': os.path.basename(abi_file_path).replace('.json', ''),
        'functions': functions,
        'events': events,
        'total_functions': len(functions),
        'total_events': len(events)
    }

def main():
    """Analyze all contract ABIs."""
    contracts_dir = 'contracts/abis'
    
    if not os.path.exists(contracts_dir):
        print(f"Contracts directory {contracts_dir} not found!")
        return
    
    contract_files = [f for f in os.listdir(contracts_dir) if f.endswith('.json')]
    
    print("🔍 CONTRACT FUNCTIONALITY AUDIT")
    print("=" * 80)
    
    all_contracts = {}
    
    for contract_file in contract_files:
        abi_path = os.path.join(contracts_dir, contract_file)
        contract_info = analyze_contract_abi(abi_path)
        all_contracts[contract_info['contract_name']] = contract_info
        
        print(f"\n📋 {contract_info['contract_name'].upper()} CONTRACT")
        print("-" * 50)
        print(f"Total Functions: {contract_info['total_functions']}")
        print(f"Total Events: {contract_info['total_events']}")
        
        print("\n🔧 FUNCTIONS:")
        for func in contract_info['functions']:
            inputs_str = ', '.join(func['inputs']) if func['inputs'] else 'none'
            outputs_str = ', '.join(func['outputs']) if func['outputs'] else 'void'
            mutability = func['stateMutability']
            
            print(f"  • {func['name']}({inputs_str}) → {outputs_str} [{mutability}]")
        
        print("\n📡 EVENTS:")
        for event in contract_info['events']:
            inputs_str = ', '.join(event['inputs']) if event['inputs'] else 'none'
            print(f"  • {event['name']}({inputs_str})")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    total_functions = sum(c['total_functions'] for c in all_contracts.values())
    total_events = sum(c['total_events'] for c in all_contracts.values())
    
    print(f"Total Contracts: {len(all_contracts)}")
    print(f"Total Functions: {total_functions}")
    print(f"Total Events: {total_events}")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Check backend services implement all functions")
    print("2. Verify API endpoints match contract functions")
    print("3. Ensure consistent parameter naming")
    print("4. Validate error handling for all functions")
    
    return all_contracts

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to verify that extract_text_tool_calls can handle multiple tool calls.
"""
import sys
import os
sys.path.insert(0, '/volume/home/chubb/bots/JakeySelfBot')

from bot.client import extract_text_tool_calls

def test_multiple_tool_calls():
    """Test that multiple tool calls are extracted correctly"""
    
    # Test Case 1: Multiple JSON tool calls
    test_response_1 = '''{"type":"function","name":"fattips_withdraw","parameters":{"destination_address":"abc123","amount":1.5,"token":"SOL"}}
{"type":"function","name":"fattips_get_swap_quote","parameters":{"input_token":"SOL","output_token":"USDC","amount":2.5,"amount_type":"token"}}
{"type":"function","name":"fattips_execute_swap","parameters":{"input_token":"SOL","output_token":"USDC","amount":2.5,"amount_type":"token","slippage":1.0}}
{"type":"function","name":"fattips_get_leaderboard","parameters":{"type":"tippers","limit":10}}'''
    
    print("Test Case 1: Multiple JSON tool calls")
    print("=" * 50)
    tool_calls, cleaned = extract_text_tool_calls(test_response_1)
    print(f"Found {len(tool_calls)} tool calls:")
    for i, tc in enumerate(tool_calls, 1):
        print(f"  {i}. {tc['function']['name']}")
    print(f"Cleaned response: {cleaned}")
    print()
    
    # Test Case 2: Single JSON tool call (should still work)
    test_response_2 = '{"type":"function","name":"fattips_get_balance","parameters":{"user_id":"123"}}'
    
    print("Test Case 2: Single JSON tool call")
    print("=" * 50)
    tool_calls, cleaned = extract_text_tool_calls(test_response_2)
    print(f"Found {len(tool_calls)} tool calls:")
    for i, tc in enumerate(tool_calls, 1):
        print(f"  {i}. {tc['function']['name']}")
    print(f"Cleaned response: {cleaned}")
    print()
    
    # Test Case 3: Mixed content with multiple tool calls
    test_response_3 = '''Here are the results you requested:
{"type":"function","name":"fattips_withdraw","parameters":{"destination_address":"wallet123","amount":0.5,"token":"SOL"}}
{"type":"function","name":"fattips_get_swap_quote","parameters":{"input_token":"SOL","output_token":"BONK","amount":1000,"amount_type":"token"}}

Let me know if you need anything else!'''
    
    print("Test Case 3: Mixed content with multiple tool calls")
    print("=" * 50)
    tool_calls, cleaned = extract_text_tool_calls(test_response_3)
    print(f"Found {len(tool_calls)} tool calls:")
    for i, tc in enumerate(tool_calls, 1):
        print(f"  {i}. {tc['function']['name']}")
    print(f"Cleaned response: {cleaned}")
    print()
    
    # Test Case 4: No tool calls (should return empty)
    test_response_4 = "Hello! How can I help you today?"
    
    print("Test Case 4: No tool calls")
    print("=" * 50)
    tool_calls, cleaned = extract_text_tool_calls(test_response_4)
    print(f"Found {len(tool_calls)} tool calls")
    print(f"Cleaned response: {cleaned}")
    print()
    
    # Verify expected results
    print("VERIFICATION")
    print("=" * 50)
    
    # Test 1 should have 4 tool calls
    tool_calls1, _ = extract_text_tool_calls(test_response_1)
    assert len(tool_calls1) == 4, f"Expected 4 tool calls, got {len(tool_calls1)}"
    assert tool_calls1[0]['function']['name'] == 'fattips_withdraw'
    assert tool_calls1[1]['function']['name'] == 'fattips_get_swap_quote'
    assert tool_calls1[2]['function']['name'] == 'fattips_execute_swap'
    assert tool_calls1[3]['function']['name'] == 'fattips_get_leaderboard'
    print("✓ Test 1 PASSED: Multiple tool calls extracted correctly")
    
    # Test 2 should have 1 tool call
    tool_calls2, _ = extract_text_tool_calls(test_response_2)
    assert len(tool_calls2) == 1, f"Expected 1 tool call, got {len(tool_calls2)}"
    assert tool_calls2[0]['function']['name'] == 'fattips_get_balance'
    print("✓ Test 2 PASSED: Single tool call extracted correctly")
    
    # Test 3 should have 2 tool calls
    tool_calls3, _ = extract_text_tool_calls(test_response_3)
    assert len(tool_calls3) == 2, f"Expected 2 tool calls, got {len(tool_calls3)}"
    print("✓ Test 3 PASSED: Mixed content with multiple tool calls works")
    
    # Test 4 should have 0 tool calls
    tool_calls4, _ = extract_text_tool_calls(test_response_4)
    assert len(tool_calls4) == 0, f"Expected 0 tool calls, got {len(tool_calls4)}"
    print("✓ Test 4 PASSED: No tool calls returns empty list")
    
    print("\n🎉 ALL TESTS PASSED! Multiple tool calls are now handled correctly.")

if __name__ == "__main__":
    test_multiple_tool_calls()

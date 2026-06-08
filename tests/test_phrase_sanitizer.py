#!/usr/bin/env python3
"""
Test script for phrase sanitizer functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.phrase_sanitizer import clean_phrase_comprehensive

def test_phrase_sanitizer():
    """Test the phrase sanitizer with various inputs"""
    
    test_cases = [
        # Basic test cases
        ("*hello world*", "hello world"),
        ("**hello world**", "hello world"),
        ("* hello world *", "hello world"),
        ("some text *hello world* more text", "hello world"),
        
        # Cases with invisible characters
        ("*hello\u200Bworld*", "hello world"),  # Zero Width Space
        ("*hello\u200Cworld*", "hello world"),  # Zero Width Non-Joiner
        ("*hello\u200Dworld*", "hello world"),  # Zero Width Joiner
        ("*hello\uFEFFworld*", "hello world"),  # Zero Width No-Break Space
        ("*hello\u00ADworld*", "hello world"),   # Soft Hyphen (now adds space)
        
        # Cases with newlines and formatting
        ("*hello\nworld*", "hello world"),
        ("**hello\nworld**", "hello world"),
        
        # Edge cases
        ("*", ""),
        ("**", ""),
        ("no asterisks here", "no asterisks here"),
        ("", ""),
    ]
    
    print("Testing phrase sanitizer...")
    print("=" * 50)
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = clean_phrase_comprehensive(input_text)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"Test {i}: {status}")
        print(f"  Input:    {repr(input_text)}")
        print(f"  Expected: {repr(expected)}")
        print(f"  Got:      {repr(result)}")
        
        if result != expected:
            print(f"  ❌ Expected '{expected}' but got '{result}'")
        print()
    
    print("Testing complete!")

if __name__ == "__main__":
    test_phrase_sanitizer()
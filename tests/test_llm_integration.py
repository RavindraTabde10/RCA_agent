"""
Test script for Azure OpenAI LLM integration
Run this script to verify your LLM configuration is working correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.llm_client import LLMClient


def test_llm_connection():
    """Test basic LLM connection and chat completion"""
    print("=" * 80)
    print("Testing Azure OpenAI LLM Integration")
    print("=" * 80)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    required_vars = [
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_VERSION',
        'AZURE_OPENAI_DEPLOYMENT_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the API key for security
            if 'KEY' in var:
                display_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"   ✓ {var}: {display_value}")
        else:
            print(f"   ✗ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nPlease create a .env file with the following variables:")
        print("AZURE_OPENAI_API_KEY=your_api_key_here")
        print("AZURE_OPENAI_ENDPOINT=https://your-apim.azure-api.net")
        print("AZURE_OPENAI_API_VERSION=2024-02-15-preview")
        print("AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4")
        return False
    
    # Initialize LLM client
    print("\n2. Initializing LLM client...")
    try:
        client = LLMClient()
        print("   ✓ LLM client initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize LLM client: {str(e)}")
        return False
    
    # Test simple chat completion
    print("\n3. Testing chat completion...")
    try:
        response = client.analyze_text(
            prompt="What is 2 + 2? Answer in one word.",
            system_message="You are a helpful assistant.",
            temperature=0.3
        )
        print(f"   ✓ Chat completion successful")
        print(f"   Response: {response}")
    except Exception as e:
        print(f"   ✗ Chat completion failed: {str(e)}")
        return False
    
    # Test RCA-specific analysis
    print("\n4. Testing RCA analysis...")
    try:
        test_error = "NullPointerException at line 42 in UserService.java"
        response = client.analyze_text(
            prompt=f"Analyze this error and provide a brief hypothesis about the root cause: {test_error}",
            system_message="You are an expert in software debugging and root cause analysis.",
            temperature=0.3
        )
        print(f"   ✓ RCA analysis successful")
        print(f"   Analysis: {response[:200]}..." if len(response) > 200 else f"   Analysis: {response}")
    except Exception as e:
        print(f"   ✗ RCA analysis failed: {str(e)}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ All tests passed! Your LLM integration is working correctly.")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_llm_connection()
    sys.exit(0 if success else 1)

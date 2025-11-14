"""Test LLM integration."""
from dotenv import load_dotenv
import anthropic
import os

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')

if not api_key:
    print("[ERROR] ANTHROPIC_API_KEY not set")
    exit(1)

print(f"[OK] API Key loaded: {api_key[:20]}...")

try:
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Say 'LLM integration working' if you can read this."}
        ]
    )

    response_text = message.content[0].text
    print(f"\n[SUCCESS] Claude Response: {response_text}")
    print("\n[OK] LLM integration is working correctly!")

except Exception as e:
    print(f"\n[ERROR] LLM test failed: {str(e)}")

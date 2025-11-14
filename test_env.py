from dotenv import load_dotenv
import os

load_dotenv()

alpaca_key = os.getenv('ALPACA_API_KEY')
alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

print("Environment Check:")
print("=" * 50)
if alpaca_key and alpaca_key != 'your_api_key_here':
    print(f"[OK] ALPACA_API_KEY: {alpaca_key[:10]}...")
else:
    print("[X] ALPACA_API_KEY: NOT SET (still has placeholder)")

if alpaca_secret and alpaca_secret != 'your_secret_key_here':
    print(f"[OK] ALPACA_SECRET_KEY: {alpaca_secret[:10]}...")
else:
    print("[X] ALPACA_SECRET_KEY: NOT SET (still has placeholder)")

if anthropic_key and len(anthropic_key) > 10:
    print(f"[OK] ANTHROPIC_API_KEY: {anthropic_key[:15]}...")
else:
    print("[X] ANTHROPIC_API_KEY: NOT SET")

print("=" * 50)

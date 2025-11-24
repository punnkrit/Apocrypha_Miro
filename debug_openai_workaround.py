
import openai
import httpx

print("Attempting to initialize httpx.Client directly...")
try:
    http_client = httpx.Client()
    print("httpx.Client initialized successfully.")
except Exception as e:
    print(f"Error initializing httpx.Client: {e}")

print("\nAttempting to initialize OpenAI with custom http_client...")
try:
    from openai import OpenAI
    client = OpenAI(api_key="test", http_client=http_client)
    print("Successfully initialized OpenAI client with custom http_client")
except Exception as e:
    print(f"Error initializing OpenAI with custom http_client: {e}")


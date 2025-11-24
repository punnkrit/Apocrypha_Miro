
import openai
import inspect
import sys

print(f"Python version: {sys.version}")
print(f"OpenAI version: {openai.__version__}")
print(f"OpenAI file: {openai.__file__}")

try:
    from openai import OpenAI
    print(f"OpenAI class: {OpenAI}")
    sig = inspect.signature(OpenAI.__init__)
    print(f"OpenAI init signature: {sig}")
except Exception as e:
    print(f"Error inspecting OpenAI: {e}")

try:
    client = OpenAI(api_key="test")
    print("Successfully initialized OpenAI client with api_key")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")


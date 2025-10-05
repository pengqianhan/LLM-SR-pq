from google import genai
from dotenv import load_dotenv
load_dotenv(override=True)  # Load from .env file in the current directory
print("dotenv loaded successfully from .env file")
# client = genai.Client()

# response = client.models.generate_content(
#     model="gemini-flash-lite-latest",
#     contents="Explain how AI works in a few words",
# )

# print(response.text)

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-flash-lite-latest",
    contents="Explain how AI works in a few words",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=100) # Disables thinking
    ),
)
print(response.text)
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def generate_response(prompt: str, model: str = "gpt-4o-mini") -> str:
    if not api_key or client is None:
        raise ValueError("OPENAI_API_KEY is not set")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content or ""
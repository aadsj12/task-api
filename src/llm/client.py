import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.llm.prompt import load_prompt


load_dotenv()

MODEL_NAME = "openrouter/free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def extract_intent_with_llm(task_text: str) -> dict:
    system_prompt = load_prompt()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": task_text,
            },
        ],
        temperature=0.1,
    )

    raw_output = response.choices[0].message.content

    if raw_output is None:
        raise ValueError("LLM returned an empty response")

    return json.loads(raw_output)
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from src.llm.prompt import load_prompt
from src.llm.schemas import IntentExtractResponse


load_dotenv()

MODEL_NAME = "openrouter/free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

class LLMValidationError(Exception):
    """Raised when the LLM output fails validation after one repair attempt."""
    pass

def quarantine_failure(task_text: str, raw_output: str, repaired_output: str) -> None:
    quarantine_dir = Path("quarantine")
    quarantine_dir.mkdir(exist_ok=True)

    quarantine_file = quarantine_dir / "llm_failures.jsonl"

    record = {
        "task_text": task_text,
        "raw_output": raw_output,
        "repaired_output": repaired_output,
    }

    with quarantine_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")

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

    try:
        parsed_output = json.loads(raw_output)
        validated_output = IntentExtractResponse.model_validate(parsed_output)
        return validated_output.model_dump()

    except (json.JSONDecodeError, ValidationError):
        repair_response = client.chat.completions.create(
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
                {
                    "role": "assistant",
                    "content": raw_output,
                },
                {
                    "role": "user",
                    "content": (
                        "Your previous response was invalid. "
                        "Repair it so it follows the required JSON schema exactly. "
                        "Return valid JSON only."
                    ),
                },
            ],
            temperature=0.1,
        )

        repaired_output = repair_response.choices[0].message.content

        if repaired_output is None:
            raise ValueError("LLM repair returned an empty response")

        try:
            repaired_json = json.loads(repaired_output)
            validated_repair = IntentExtractResponse.model_validate(repaired_json)
            return validated_repair.model_dump()

        except (json.JSONDecodeError, ValidationError) as exc:
            quarantine_failure(
                task_text=task_text,
                raw_output=raw_output,
                repaired_output=repaired_output,
            )

            raise LLMValidationError(
                "LLM output failed validation after one repair attempt"
            ) from exc
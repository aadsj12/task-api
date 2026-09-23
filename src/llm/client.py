import json
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, APIStatusError, RateLimitError
from pydantic import ValidationError

from src.llm.prompt import load_prompt
from src.llm.schemas import IntentExtractResponse


load_dotenv()

MODEL_NAME = "openrouter/free"
PROMPT_VERSION = "intent-extraction-v1"


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    timeout=30.0,
    max_retries=0,
)


def call_llm_with_retry(messages, max_attempts=3):
    """
    Call the LLM with selective retries.

    Retry only:
    - timeouts
    - rate limits (429)
    - server errors (5xx)

    Do not retry client errors such as 400, 401, or 403.
    """
    for attempt in range(max_attempts):
        try:
            return client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1,
            )

        except (APITimeoutError, RateLimitError):
            if attempt == max_attempts - 1:
                raise

        except APIStatusError as exc:
            if exc.status_code < 500:
                raise

            if attempt == max_attempts - 1:
                raise

        # Exponential backoff with jitter.
        delay = (2 ** attempt) + random.uniform(0, 0.5)
        time.sleep(delay)


class LLMValidationError(Exception):
    """Raised when the LLM output fails validation after one repair attempt."""

    pass


def quarantine_failure(
    task_text: str,
    raw_output: str,
    repaired_output: str,
) -> None:
    """
    Store failed LLM outputs locally for debugging.

    The quarantine directory is ignored by Git.
    """
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


def log_llm_call(
    response,
    duration_seconds: float,
    repair_count: int,
) -> None:
    """
    Log operational information about an LLM request.

    OpenRouter's free model route is treated as $0 for this assignment,
    so the estimated cost is logged as 0.0.
    """
    usage = response.usage

    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    total_tokens = usage.total_tokens if usage else 0

    estimated_cost_usd = 0.0

    log_record = {
        "prompt_version": PROMPT_VERSION,
        "model": MODEL_NAME,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "duration_seconds": round(duration_seconds, 3),
        "repair_count": repair_count,
        "estimated_cost_usd": estimated_cost_usd,
    }

    print(
        "LLM_METRICS "
        + json.dumps(log_record),
        flush=True,
    )


def extract_intent_with_llm(task_text: str) -> dict:
    system_prompt = load_prompt()

    start_time = time.perf_counter()

    response = call_llm_with_retry(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": task_text,
            },
        ]
    )

    raw_output = response.choices[0].message.content

    if raw_output is None:
        raise ValueError("LLM returned an empty response")

    try:
        parsed_output = json.loads(raw_output)
        validated_output = IntentExtractResponse.model_validate(parsed_output)

        duration = time.perf_counter() - start_time

        log_llm_call(
            response=response,
            duration_seconds=duration,
            repair_count=0,
        )

        return validated_output.model_dump()

    except (json.JSONDecodeError, ValidationError):
        repair_response = call_llm_with_retry(
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
            ]
        )

        repaired_output = repair_response.choices[0].message.content

        if repaired_output is None:
            raise LLMValidationError(
                "LLM repair returned an empty response"
            )

        try:
            repaired_json = json.loads(repaired_output)
            validated_repair = IntentExtractResponse.model_validate(
                repaired_json
            )

            duration = time.perf_counter() - start_time

            log_llm_call(
                response=repair_response,
                duration_seconds=duration,
                repair_count=1,
            )

            return validated_repair.model_dump()

        except (json.JSONDecodeError, ValidationError) as exc:
            quarantine_failure(
                task_text=task_text,
                raw_output=raw_output,
                repaired_output=repaired_output,
            )

            duration = time.perf_counter() - start_time

            log_llm_call(
                response=repair_response,
                duration_seconds=duration,
                repair_count=1,
            )

            raise LLMValidationError(
                "LLM output failed validation after one repair attempt"
            ) from exc
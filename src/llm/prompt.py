from pathlib import Path


PROMPT_VERSION = "intent-extraction-v2"

PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / f"{PROMPT_VERSION}.md"
)


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()
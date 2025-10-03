import logging
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(filename: str) -> str:
    prompt_path = PROMPTS_DIR / filename
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.error(f"Prompt file {filename} not found in {PROMPTS_DIR}")
        return ""
    except Exception as e:
        logging.error(f"Error reading prompt file {filename}: {e}")
        return ""

import logging
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(filename: str) -> str:
    """
    Reads a prompt template from a file in the prompts directory.

    Args:
        filename: The name of the file to load (e.g., "text_filter_prompt.txt").

    Returns:
        The content of the file as a string, or an empty string if an error occurs.
    """

    prompt_path = PROMPTS_DIR / filename
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.exception("Prompt file not found at path: %s", prompt_path)
        return ""
    except Exception:
        logging.exception("An error occurred while reading the prompt file")
        return ""

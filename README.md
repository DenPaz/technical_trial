# 🤖 AI-Powered Twitter Clip Finder

[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Linter](https://img.shields.io/badge/linter-ruff-brightgreen.svg)](https://github.com/astral-sh/ruff)
[![Framework](https://img.shields.io/badge/framework-LangChain-purple.svg)](https://www.langchain.com/)

An intelligent CLI tool that automates finding specific video clips on **Twitter/X**. Powered by **LangChain** and Google's **Gemini** models, this application can take a simple text description and a target duration, and return a precise video segment matching your query.

The entire pipeline is orchestrated by **LangGraph**, creating a modular and robust state machine that handles the flow from initial scraping to final clip selection.

---

## ✨ Features

- **🔍 Smart Scraping**: Searches Twitter for recent tweets containing videos that match a given query.
- **🤖 AI-Powered Filtering**: Utilizes a Gemini model to perform a rapid first-pass filter on tweet text, drastically reducing the number of videos that require expensive analysis.
- **👁️ Advanced Vision Analysis**: Downloads and analyzes the video content of top candidates frame-by-frame using the Gemini Vision model to identify segments matching the user's description.
- **🎬 Precise Clip Identification**: Returns the exact start and end timestamps for the best-matching continuous clip, ready for immediate use.
- **📄 Structured Output**: Provides a clean, machine-readable JSON output with the best clip, alternate suggestions, and a full trace of the pipeline's execution for maximum transparency.

---

## 🛠️ Architecture

The application is built as a modular Python package within the `src/` directory. The core logic is orchestrated by a LangGraph state machine defined in `src/graph.py`, which connects the following modules:

- `scraper`: Handles all interactions with Twitter.
- `filters`: Narrows down candidates using text-based AI.
- `vision`: Performs frame-by-frame video analysis.
- `selector`: Ranks all findings and selects the final best clip.

Data models are centralized in `src/schemas.py`, and all prompts are managed in the `src/prompts/` directory.

```
technical_trial/
├── src/
│ ├── schemas.py # Core data models (Pydantic)
│ ├── graph.py # LangGraph pipeline orchestrator
│ ├── config/ # Settings and logging
│ ├── prompts/ # LLM prompt templates
│ ├── scraper/ # Twitter scraping logic
│ ├── filters/ # Text-based filtering logic
│ ├── vision/ # Video analysis logic
│ └── selector/ # Final clip selection logic
├── tests/ # Unit and integration tests
├── main.py # CLI entrypoint
└── pyproject.toml
```

---

## 🚀 Getting started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (for blazing-fast environment and package management)

### Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/DenPaz/technical_trial.git
    cd technical_trial
    ```

2.  **Create virtual environment & install dependencies**
    This command uses `uv` to create a virtual environment and install all required packages from `pyproject.toml`.

    ```bash
    uv sync
    ```

3.  **Set up environment variables**
    Create a file named `.env` in the project root and add your credentials.

    ```env
    # .env - Replace placeholders with your actual credentials

    # Twitter/X Credentials
    TWITTER_USERNAME="your_twitter_username"
    TWITTER_EMAIL="your_twitter_email@example.com"
    TWITTER_PASSWORD="your_twitter_password"

    # Google Gemini API Key
    GEMINI_API_KEY="your_google_ai_studio_api_key"
    ```

4.  **Set up Twitter cookies**
    To ensure a stable connection, the scraper uses an existing session cookie.
    - Log in to [x.com](https://x.com) in your web browser.
    - Use a browser extension (e.g., "[Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)") to export your cookies as a JSON file.
    - Save this file as `cookies_raw.json` in the project's root directory.
    - Run the provided conversion script: `uv run convert_cookies.py`. This generates a `cookies.json` file, which is automatically ignored by Git.

---

## ▶️ Usage

The application is run from the command line.

### Command

```bash
uv run main.py --description "A description of the clip" --duration <seconds> [--max-candidates <int>] [--out <output_file>]
```

### Arguments

| Argument           | Type    | Required | Description                                                       | Default        |
| ------------------ | ------- | -------- | ----------------------------------------------------------------- | -------------- |
| `--description`    | String  | Yes      | A string describing the content of the clip you are looking for.  | N/A            |
| `--duration`       | Integer | Yes      | An integer representing the target length of the clip in seconds. | N/A            |
| `--max-candidates` | Integer | No       | The maximum number of initial tweets to scrape.                   | `10`           |
| `--out`            | String  | No       | The path for the output JSON file.                                | `results.json` |

### Example

To find a 15-second clip of "Trump talking about Charlie Kirk" and save it to `output.json`:

```bash
uv run main.py --description "Trump talking about Charlie Kirk" --duration 15 --out output.json
```

The tool will log its progress and, upon success, create the `output.json` file with the results.

---

## 🧪 Running Tests

This project uses `pytest` for unit testing.

1. Install `pytest` (if not already installed by `uv sync`):

   ```bash
   uv pip install pytest
   ```

2. Run the tests:
   From the project root, simply run:
   ```bash
   uv run pytest
   ```

`pytest` will automatically discover and run all tests inside the `tests/` directory.

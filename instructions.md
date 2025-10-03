# Technical Trial: Twitter clip scraper with AI selection

## Goal

To build a Python tool that:

1. Takes input: A media description and a target duration (in seconds).
2. Scrapes Twitter: Searches for tweets with video attachments that might match the query.
3. Filters candidates: Based on tweet text analysis, shortlists the most relevant ones.
4. Analyzes video: Runs Gemini vision on shortlisted videos to find the best match and identify a continuous clip of the requested duration.
5. Returns result: Provides the chosen tweet/video URL, exact start and end timestamps, confidence score, reasoning, and at least one alternative suggestion.

## Example input

```
{
  "description": "Trump talking about Charlie Kirk",
  "duration_in_seconds": 12
}
```

## Example output

```
{
  "tweet_url": "https://x.com/user/status/123456789",
  "video_url": "https://video.twimg.com/...",
  "start_time_s": 47.2,
  "end_time_s": 59.2,
  "confidence": 0.86,
  "reason": "Speaker identified as Donald Trump. Mentions Charlie Kirk at 49-52s. Continuous speech. Clear audio and face.",
  "alternates": [
     {"start_time_s": 122.1, "end_time_s": 134.1, "confidence": 0.77},
  ],
  "trace": {
      "candidates_considered": 18,
      "filtered_by_text": 9,
      "vision_calls": 6,
      "final_choice_rank": 1
    }
}
```

## Requirements

1. Scraper:
   - Use **twikit** or any other open source tool to scrape Twitter/X for tweets with video attachments that may match the query.
   - Collect for each candidate: tweet URL, tweet text, author handle, created time, engagement metrics, video URL or HLS playlist.
   - Implement retries with jitter/backoff and respect rate limits.
   - Do not use Selenium or the paid X API.
2. Candidate filtering:
   - Filter and rank tweets based on text analysis to create a shortlist.
   - The filtering logic is entirely up to you -- focus on accuracy and efficiency.
3. Video analysis:
   - Download or stream the candidate videos.
   - Use Gemini vision to:
     - Confirm speaker/topic relevance.
     - Locate a continuous segment of the required duration (+/- 2s if exact is not available).
     - Return a confidence score and reasoning for why this clip matches.
4. Clip selection:
   - Rank all candidates based on relevance and confidence.
   - Return the best match and optionally one or two alternates.
5. Tooling and interface:

   - Provide a CLI:

   ```
   python main.py --description "Trump talking about Charlie Kirk" --duration 12 --max-candidates 30
   ```

6. Orchestration & LLM usage:
   - Use **LangChain** for all LLM calls (e.g., text/vision analysis, reasoning, ranking).
   - Use **LangGraph** to orchestrate the pipeline, keeping components modular and clearly defined.
   - Use **structured output parsing** (e.g., `with_structured_output()` or equivalent) to ensure all LLM responses are clean JSON and machine-readable.
   - Handle error cases gracefully if the LLM returns malformed output.

## Deliverables

1. GitHub repo with:
   - `README.md` (setup, dependencies, run instructions for CLI/API).
   - Modular Python code (`scraper/`, `filters/`, `vision/`, `selector/`) clean architecture or solid principles are encouraged.
   - Prompts (if used) in a `prompts/` folder.
   - Minimal tests for filtering logic and timestamp math.
2. Design note explaining:
   - Your strategy.
   - How you filter candidates.
   - How you minimize expensive calls.
   - Why you selected the final clip.
3. Short screen recording showing an end-to-end run.

## Anti-cheat and realism

- Provide one or two seed search terms you will test with, but keep your validation queries private.
- We will review logs to ensure real scraping and vision calls are happening.
- Submit a quick screen recording to confirm end-to-end behavior.
- If scraping is blocked by rate limits, document a fallback approach (cached HTML, smaller candidate pool, etc.).

## Scoring rubric

| Criteria       | Weight | Notes                                                                                                                                                                                                                             |
| -------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Correctness    | 30%    | Finds a valid tweet/video and returns a segment that matches the description with accurate timestamps.                                                                                                                            |
| Prompt quality | 20%    | Prompts (if used) are modular, cleanly separated, and demonstrate clear reasoning. Very detailed prompts for each service Meta prompting with examples are encouraged. Making prompts to be caching ready is also an extra point. |
| Efficiency     | 15%    | Good filtering reduces unnecessary video downloads and Gemini calls. Runtime is reasonable.                                                                                                                                       |
| Code quality   | 20%    | Readable Python with clean naming conventions, docstrings, modular structure, and proper error handling.                                                                                                                          |
| Reliability    | 10%    | Graceful handling of missing media, private tweets, and rate-limit errors with retries.                                                                                                                                           |
| Traceability   | 5%     | Logs and outputs clearly show what candidates were considered and why the final clip was chosen.                                                                                                                                  |

## Notes

- LLM usage is encouraged inside the pipeline -- you may use LLMs for tweet text analysis, candidate reasoning, or final selection logic.
- Use of AI coding assistants (e.g., Cursor, GPT, Claude) to speed up development is welcome. We care about a clean, working solution -- not how many lines of code you typed manually.
- Test for non-perfect / not twitter ready media descriptions where query conversion may be needed.

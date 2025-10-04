import logging
from pathlib import Path
from typing import Literal

from twikit import Client
from twikit import TooManyRequests
from twikit import Tweet

from src.config.settings import BASE_DIR
from src.config.settings import settings
from src.schemas import Candidate

logger = logging.getLogger(__name__)


class TwikitClient:
    """
    Wrapper around the twikit.Client for handling authentication and
    low-level API operations.
    """

    def __init__(
        self,
        language: str = "en-US",
        cookies_file: Path | None = BASE_DIR / "cookies.json",
    ) -> None:
        self._client = Client(language=language)
        self._cookies_file = cookies_file

    async def login(self) -> None:
        """
        Performs session login using cached cookies or credentials.
        """
        try:
            await self._client.login(
                auth_info_1=settings.twitter_username,
                auth_info_2=settings.twitter_email,
                password=settings.twitter_password.get_secret_value(),
                cookies_file=self._cookies_file,
            )
            logger.debug("Twikit login successful.")
        except Exception:
            logger.exception("Twikit login failed.")
            raise

    async def search_tweets(
        self,
        query: str,
        product: Literal["Top", "Latest", "Media"] = "Top",
        count: int = 20,
    ) -> list[Tweet]:
        """
        Searches for tweets and handles rate limiting.
        """
        try:
            tweets: list[Tweet] = await self._client.search_tweet(
                query=query,
                product=product,
                count=count,
            )
        except TooManyRequests:
            logger.warning("Rate limit exceeded while searching tweets.")
            return []
        except Exception:
            logger.exception("Error occurred while searching tweets.")
            return []
        else:
            logger.debug("Fetched %d raw tweets for query: %s", len(tweets), query)
            return tweets or []


def _get_best_video_url(tweet: Tweet) -> str | None:
    """
    Extracts the highest bitrate MP4 video URL from a tweet's media.
    """
    if not hasattr(tweet, "media") or not tweet.media:
        return None

    video_media = next((m for m in tweet.media if m.type == "video"), None)
    if not video_media or not hasattr(video_media, "streams"):
        return None

    mp4_streams = [
        s for s in video_media.streams if s.url and "mp4" in (s.content_type or "")
    ]
    if not mp4_streams:
        return getattr(video_media, "url", None)

    best_stream = max(mp4_streams, key=lambda s: s.bitrate or 0)
    return best_stream.url


async def scrape_candidates(
    query: str,
    max_candidates: int = 10,
) -> list[Candidate]:
    """
    Scrapes Twitter for tweets with videos that match a search query.

    Args:
        query: The search term for finding relevant tweets.
        max_candidates: The maximum number of valid candidate to return.

    Returns:
        A list of Candidate objects for the next pipeline stage.
    """
    client = TwikitClient()
    await client.login()

    search_limit = max_candidates * 5
    logger.info("Searching for up to %d tweets with query: %s", search_limit, query)
    raw_tweets = await client.search_tweets(query=query, count=search_limit)

    if not raw_tweets:
        logger.warning("Initial Twitter search returned no results.")
        return []

    results: list[Candidate] = []
    for tweet in raw_tweets:
        if len(results) >= max_candidates:
            break

        best_video_url = _get_best_video_url(tweet)
        if not best_video_url:
            continue

        candidate = Candidate(
            tweet_url=f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
            video_urls=[
                s.url
                for m in (tweet.media or [])
                if m.type == "video"
                for s in (m.streams or [])
                if s.url
            ],
            best_video_url=best_video_url,
            text=tweet.text,
            author=tweet.user.screen_name,
            created_at=tweet.created_at,
        )
        results.append(candidate)

    logger.info("Found %d candidate tweets with processable videos.", len(results))
    return results

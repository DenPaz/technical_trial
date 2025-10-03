import logging
from typing import Any
from typing import List
from typing import Optional

from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from .client import TwikitClient
from .schemas import Candidate

logger = logging.getLogger(__name__)


def _get_best_video_url(tweet: Any) -> Optional[str]:
    if not hasattr(tweet, "media") or not tweet.media:
        return None
    video_media = next((m for m in tweet.m if m.type == "video"), None)
    if not video_media or not hasattr(video_media, "streams"):
        return None
    mp4_streams = [
        s for s in video_media.streams if s.url and "mp4" in (s.content_type or "")
    ]
    if not mp4_streams:
        return None
    best_stream = max(mp4_streams, key=lambda s: s.bitrate or 0)
    return best_stream.url


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _hydrate_tweet(client: TwikitClient, tweet_id: str) -> Any:
    logger.debug(f"Hydrating tweet ID: {tweet_id}")
    return await client.get_tweet(tweet_id)


async def scrape_candidates(query: str, max_candidates: int = 10) -> List[Candidate]:
    """
    Scrapes Twitter/X for tweets with videos that match a search query.

    Args:
        query: Search query string (e.g., "Trump talking about Charlie Kirk").
        max_candidates: Maximum number of tweets to return.

    Returns:
        List of dicts with tweet metadata.
    """

    client = TwikitClient()
    await client.login()

    logger.info(f"Searching video tweets for query='{query}', max={max_candidates}")

    tweets = await client.search(query=query, count=max_candidates)
    results: List[Candidate] = []

    for tweet in tweets:
        if not tweet.media or not any(media.type == "video" for media in tweet.media):
            continue

        video_urls = []
        for media in tweet.media:
            if media.type == "video":
                for s in media.streams:
                    if s.url:
                        video_urls.append(s.url)
            if not media.streams and media.url:
                video_urls.append(media.url)

        results.append(
            Candidate(
                tweet_url=f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
                text=tweet.text,
                author=tweet.user.screen_name,
                created_at=str(tweet.created_at),
                video_urls=video_urls,
                like_count=tweet.favorite_count,
                retweet_count=tweet.retweet_count,
            )
        )
    logger.info(f"Found {len(results)} candidate tweets with videos.")
    return results

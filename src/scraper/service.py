import logging
from typing import List

from .client import TwikitClient
from .schemas import Candidate

logger = logging.getLogger(__name__)


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

    tweets = await client.search_tweet(query=query, count=max_candidates)
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

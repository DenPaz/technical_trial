import logging
from typing import List
from typing import Optional

from twikit import Tweet

from .client import TwikitClient
from .schemas import Candidate

logger = logging.getLogger(__name__)


def _get_best_video_url(tweet: Tweet) -> Optional[str]:
    """ "
    Extracts the highest bitrate MP4 video URL from a tweet object.
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
        if hasattr(video_media, "url") and video_media.url:
            return video_media.url
        return None
    best_stream = max(mp4_streams, key=lambda s: s.bitrate or 0)
    return best_stream.url


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

    search_multiplier = 4
    search_limit = max_candidates * search_multiplier
    initial_tweets = await client.search_tweet(query=query, count=search_limit)

    if not initial_tweets:
        logger.warning("Initial search returned no tweets.")
        return []

    results: List[Candidate] = []
    for tweet in initial_tweets:
        if len(results) >= max_candidates:
            break
        best_video_url = _get_best_video_url(tweet)
        if not best_video_url:
            continue
        results.append(
            Candidate(
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
                like_count=tweet.favorite_count,
                retweet_count=tweet.retweet_count,
            )
        )
    logger.info(f"Found {len(results)} candidate tweets with videos.")
    return results

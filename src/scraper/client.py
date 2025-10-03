import logging
from pathlib import Path
from typing import List
from typing import Optional

from twikit import Client
from twikit import TooManyRequests
from twikit import Tweet

from src.config.settings import BASE_DIR
from src.config.settings import settings

logger = logging.getLogger(__name__)


class TwikitClient:
    """
    Thin wrapper around twikit.Client for auth + low-level operations.

    Usage:
        client = TwikitClient()
        await client.login()
        tweets = await client.search_tweet(query="some query", count=30)
        detailed_tweet = await client.get_tweet_by_id(tweet_id="1234567890")
    """

    def __init__(
        self,
        locale: str = "en-US",
        cookies_file: Optional[Path] = None,
    ) -> None:
        self._client = Client(locale)
        self._cookies_file = str(cookies_file or BASE_DIR / "cookies.json")

    async def login(self) -> None:
        """
        Perform session login.

        Notes:
        - auth_info_1 + password are required.
        - auth_info_2 is optional (email/phone/username).
        - enable_ui_metrics improves stability with twikit.
        - cookies_file allows reusing the session across runs.
        """
        await self._client.login(
            auth_info_1=settings.twitter_username,
            auth_info_2=settings.twitter_email or None,
            password=settings.twitter_password.get_secret_value(),
            cookies_file=self._cookies_file,
            enable_ui_metrics=True,
        )
        logger.debug("Twikit login successful.")

    async def search_tweet(
        self,
        query: str,
        count: int,
        product: str = "Top",
    ) -> List[Tweet]:
        """
        Search tweets for a query. Returns a list of lightweight Tweet objects.

        Params:
            query: Free text search query.
            count: Maximum number of results to fetch.
            product: Search product ("Top", "Latest", "Media").

        Returns:
            List[Tweet]: Twikit tweet objects (lightweight). For full details, hydrate via get_tweet_by_id().
        """
        try:
            tweets: List[Tweet] = await self._client.search_tweet(
                query=query,
                product=product,
                count=count,
            )
            return tweets or []
        except TooManyRequests:
            logger.error("Rate limited by Twitter/X API during search.")
            return []
        except Exception as e:
            logger.warning(f"An unexpected error occurred during search: {e}")
            return []

    async def get_tweet_by_id(self, tweet_id: str | int) -> Optional[Tweet]:
        """
        Hydrate a single tweet by id. The returned object generally includes
        full media information (e.g. Video.streams / url).
        """
        try:
            tweet: Tweet = await self._client.get_tweet_by_id(tweet_id)
            return tweet
        except TooManyRequests:
            logger.error(f"Rate limited while fetching tweet {tweet_id}.")
            raise
        except Exception as e:
            logger.warning(f"Failed to get tweet {tweet_id}: {e}")
            raise

    @property
    def raw(self) -> Client:
        """
        Expose the underlying twikit.Client instance for advanced usage.
        """
        return self._client

import logging
from pathlib import Path
from typing import Any
from typing import List
from typing import Optional

from twikit import Client
from twikit import TooManyRequests

from src.config import BASE_DIR
from src.config import settings

logger = logging.getLogger(__name__)


class TwikitClient:
    """
    Thin wrapper around twikit.Client for auth + low-level operations.

    Usage:
        tc = TwikitClient()
        await tc.login()
        tweets = await tc.search("some query", count=30)
        full = await tc.get_tweet_by_id(tweets[0].id)
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
            auth_info_1=settings.TWITTER_USERNAME,
            auth_info_2=settings.TWITTER_EMAIL or None,
            password=settings.TWITTER_PASSWORD,
            cookies_file=self._cookies_file,
            enable_ui_metrics=True,
        )
        logger.debug("Twikit login successful.")

    async def search(self, query: str, count: int, product: str = "top") -> List[Any]:
        """ "
        Search tweets for a query. Returns a list of lightweight Tweet objects.

        Params:
            query: Free text search query.
            count: Maximum number of results to fetch.
            product: Search product ("top", "latest", etc).

        Returns:
            List[Any]: Twikit tweet objects (lightweight). For full details, use get_tweet_by_id().
        """
        try:
            tweets = await self._client.search_tweet(
                query=query,
                product=product,
                count=count,
            )
            return tweets or []
        except TooManyRequests:
            logger.error("Rate limited by Twitter/X API. Try again later.")
            return []
        except Exception as e:
            logger.warning(f"search() failed: {e}")
            return []

    async def get_tweet_by_id(self, tweet_id: str | int) -> Any:
        """
        Hydrate a single tweet by id. The returned object generally includes
        full media information (e.g. Video.streams / url).
        """
        try:
            return await self._client.get_tweet_by_id(tweet_id)
        except TooManyRequests:
            logger.error("Rate limited by Twitter/X API. Try again later.")
            raise
        except Exception as e:
            logger.warning(f"get_tweet_by_id() failed: {e}")
            raise

    @property
    def raw(self) -> Client:
        """
        Expose the underlying twikit.Client instance for advanced usage.
        """
        return self._client

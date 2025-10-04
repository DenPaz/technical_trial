from src.scraper.scraper import _get_best_video_url


class MockStream:
    def __init__(self, url, content_type, bitrate):
        self.url = url
        self.content_type = content_type
        self.bitrate = bitrate


class MockMedia:
    def __init__(self, media_type, streams=None, url=None):
        self.type = media_type
        self.streams = streams or []
        self.url = url


class MockTweet:
    def __init__(self, media=None):
        self.media = media or []


def test_get_best_video_url_selects_highest_bitrate():
    """
    Ensures the function selects the MP4 stream with the highest bitrate.
    """
    mock_tweet = MockTweet(
        media=[
            MockMedia(
                media_type="video",
                streams=[
                    MockStream("https://video.com/low.mp4", "video/mp4", 832000),
                    MockStream("https://video.com/high.mp4", "video/mp4", 2176000),
                    MockStream("https://video.com/medium.mp4", "video/mp4", 1280000),
                ],
            ),
        ],
    )
    best_url = _get_best_video_url(mock_tweet)
    assert best_url == "https://video.com/high.mp4"


def test_get_best_video_url_no_media():
    """
    Ensures the function returns None when a tweet has no media.
    """
    mock_tweet = MockTweet(media=[])
    assert _get_best_video_url(mock_tweet) is None


def test_get_best_video_url_no_video_media():
    """
    Ensures the function returns None when a tweet has media, but no videos.
    """
    mock_tweet = MockTweet(media=[MockMedia(media_type="photo")])  # Changed to 'type'
    assert _get_best_video_url(mock_tweet) is None


def test_get_best_video_url_no_mp4_streams():
    """
    Ensures the function falls back to the media URL if no MP4 streams are found.
    """
    mock_tweet = MockTweet(
        media=[
            MockMedia(
                media_type="video",
                url="https://video.com/fallback.m3u8",
                streams=[
                    MockStream(
                        "https://video.com/stream1.m3u8",
                        "application/x-mpegURL",
                        832000,
                    ),
                    MockStream(
                        "https://video.com/stream2.m3u8",
                        "application/x-mpegURL",
                        2176000,
                    ),
                ],
            ),
        ],
    )
    fallback_url = _get_best_video_url(mock_tweet)
    assert fallback_url == "https://video.com/fallback.m3u8"

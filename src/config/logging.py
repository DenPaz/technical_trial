from logging.config import dictConfig


def setup_logging() -> None:
    """
    Sets up a shared logging configuration for the entire application.
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(levelname)s] %(asctime)s %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "loggers": {
            "httpx": {"level": "WARNING", "propagate": True},
            "watchfiles": {"level": "WARNING", "propagate": True},
        },
    }
    dictConfig(logging_config)

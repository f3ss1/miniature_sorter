import sys

from loguru import logger

logger.remove()

logger.add(
    sink=sys.stderr,
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    colorize=True,
    format=(
        "<g>{time:YYYY-MM-DD HH:mm:ss.SSS}</> |"
        " <lvl>{level: <8}</> |"
        " {extra[user_id]} |"
        " <c>{name}</>:<c>{function}</>:<c>{line}</> - <lvl>{message}</>"
    ),
)

# TODO: replace with bind.
logger.configure(extra={"user_id": "ssl_exception_bot"})  # Default values

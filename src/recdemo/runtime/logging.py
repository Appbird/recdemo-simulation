import logging

from rich.logging import RichHandler


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                show_path=False,
                rich_tracebacks=True,
            )
        ],
    )

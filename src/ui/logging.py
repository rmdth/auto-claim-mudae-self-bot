import logging
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from src.ui.layout import DEBUG, layout

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"


class DebugHandler(logging.Handler):
    def __init__(
        self,
        layout: Layout,
        live: Live,
        title: str,
        border_style: str,
        max_lines: int = 15,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.layout = layout
        self.live = live
        self.title = title
        self.border_style = border_style
        self.logs = deque(maxlen=max_lines)

    def emit(self, record):
        message = self.format(record)

        match record.levelname:
            case "INFO":
                style = "green"
            case "DEBUG":
                style = "dim yellow"
            case "WARNING":
                style = "yellow"
            case "ERROR":
                style = "red"
            case _:
                style = "green"

        self.logs.append(Text(message, style=style))

        renderable_text = Text("\n").join(self.logs)

        panel = Panel(
            renderable_text,
            title=self.title,
            border_style=self.border_style,
        )
        self.layout.update(panel)
        self.live.refresh()


def setup_logging() -> None:
    from src.ui.layout import live

    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.INFO)

    LOGS_DIR.mkdir(exist_ok=True, parents=True)

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        LOGS_DIR / "mudae.log",
        maxBytes=1024 * 1024 * 5,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

    if DEBUG:
        debug_handler = DebugHandler(layout["debug"], live, "DEBUG", "blue")
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        log.addHandler(debug_handler)

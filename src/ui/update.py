from logging import getLogger

from rich.panel import Panel
from rich.text import Text

from src.ui import setup
from src.ui.layout import channel_layout, layout, live

log = getLogger(__name__)


def refresh_ui() -> None:
    layout["bot"]["status"].update(
        Panel(
            Text("\n".join(setup.bot_status.values()), style="dim yellow")
            or Text("...", style="dim yellow"),
            title="BOT STATE",
            border_style="blue",
        )
    )
    channel_layout["status"].update(
        Panel(
            Text(
                "\n".join(
                    setup.channel_page_uis[
                        setup.page_id_map[setup.page]
                    ].statuses.values()
                ),
                style="dim yellow",
            )
            or Text("...", style="dim yellow"),
            title=f"CHANNEL {setup.page + 1} STATE",
            border_style="blue",
        ),
    )
    channel_layout["log"].update(
        Panel(
            Text(
                "\n".join(
                    setup.channel_page_uis[setup.page_id_map[setup.page]].roll_queue
                )
            ),
            title=f"CHANNEL {setup.page + 1} LOGS",
            border_style="blue",
        )
    )
    live.refresh()


def update_bot_state(state_key: str, status: str) -> None:
    setup.bot_status[state_key] = status
    refresh_ui()


def update_channel_state(channel_key: int, state_key: str, status: str) -> None:
    setup.channel_page_uis[channel_key].statuses[state_key] = status
    refresh_ui()


def update_mudae_log_message(channel_key: int, message: str) -> None:
    setup.channel_page_uis[channel_key].roll_queue.append(message)
    refresh_ui()


def update_mudae_log_roll(
    channel_key: int,
    char: str,
    watching: bool,
    been_claimed: bool,
    is_wished: bool,
) -> None:
    icon = "♥️" if been_claimed else "🤍"
    _wished = " - 🌟" if is_wished else ""
    watching_msg = " - 👀" if watching else ""
    msg = f"{icon} ---- {char}{_wished}{watching_msg}"

    setup.channel_page_uis[channel_key].roll_queue.append(msg)
    refresh_ui()


def update_mudae_log_kakera(
    channel_key: int,
    kakera: str,
    watching: bool,
    is_wished: bool,
) -> None:
    icon = "💎"
    _wished = " - 🌟" if is_wished else ""
    watching_msg = " - 👀" if watching else ""
    msg = f"{icon} ---- {kakera}{_wished}{watching_msg}"
    setup.channel_page_uis[channel_key].roll_queue.append(msg)
    refresh_ui()


def update_log_debug(message: str) -> None:
    log.debug(message)


def update_log_info(message: str) -> None:
    log.info(message)


def update_log_error(message: str) -> None:
    log.error(message)

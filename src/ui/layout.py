from tomllib import load

from rich.layout import Layout
from rich.live import Live

with open("./bot-settings.toml", "rb") as f:
    DEBUG: bool = load(f).get("debug", False)


if DEBUG:
    if_debug = Layout()
    if_debug.split_column(Layout(name="debug"), Layout(name="bot"))
    layout = if_debug
else:
    layout = Layout(name="bot")

channel_layout = Layout(name="channel")
channel_layout.split_row(Layout(name="status"), Layout(name="log"))

layout["bot"].split_column(Layout(name="status"), channel_layout)
layout["bot"]["channel"].ratio = 3


live = Live(layout, auto_refresh=False, screen=True)

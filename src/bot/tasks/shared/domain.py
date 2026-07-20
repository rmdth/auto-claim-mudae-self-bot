from typing import Any, Awaitable, Callable, NamedTuple

from discord.client import Client

from src.bot.domain import Channel
from src.bot.shared.domain import MudaeMessage
from src.bot.states import StateType


class Preference[Context](NamedTuple):
    name: str
    conditional: Callable[[Context, dict[str, Any]], bool]
    input_data: dict[str, Any]
    preference_data: dict[str, Any]


class Task[Context, TaskContext](NamedTuple):
    name: str
    trigger: str
    action: Callable[[TaskContext], Awaitable[None]]
    preferences: tuple[Preference, ...]
    context_generator: Callable[
        [
            Context,
            tuple[Preference, ...],
        ],
        TaskContext,
    ]
    state: StateType | None = None


class OnMessageContext(NamedTuple):
    bot: Client
    channel: Channel
    message: MudaeMessage | None

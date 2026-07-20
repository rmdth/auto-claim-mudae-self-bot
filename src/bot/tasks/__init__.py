from src.bot.states import BotState, ChannelState
from src.bot.tasks.auto_roll.task import auto_roll, auto_roll_context_generator
from src.bot.tasks.claim_daily.task import claim_daily, daily_context_generator
from src.bot.tasks.claim_kakera.preferences import claim_kakera_preferences
from src.bot.tasks.claim_kakera.task import (
    claim_kakera_context_generator,
    claim_kakeras,
)
from src.bot.tasks.claim_roll.preferences import claim_roll_preferences
from src.bot.tasks.claim_roll.task import (
    claim_roll,
    claim_roll_context_generator,
)
from src.bot.tasks.shared.domain import Preference, Task

preferences: dict[str, tuple[Preference, ...]] = {
    "claim_roll": claim_roll_preferences,
    "claim_kakera": claim_kakera_preferences,
}

tasks = (
    Task("auto_roll", "setup", auto_roll, (), auto_roll_context_generator, None),
    Task(
        "claim_daily",
        "setup",
        claim_daily,
        (),
        daily_context_generator,
        BotState.DAILY,
    ),
    Task(
        "claim_roll",
        "on_message_roll",
        claim_roll,
        preferences["claim_roll"],
        claim_roll_context_generator,
        ChannelState.ROLL,
    ),
    Task(
        "claim_kakera",
        "on_message_kakera",
        claim_kakeras,
        preferences["claim_kakera"],
        claim_kakera_context_generator,
        ChannelState.KAKERA,
    ),
)

_registry_tasks = {task.name: task for task in tasks}


def get_task(name: str) -> Task:
    return _registry_tasks[name]


def prepare_tasks(tasks: tuple[tuple[str, dict], ...]) -> tuple[Task, ...]:
    return tuple(
        _registry_tasks[name]._replace(
            preferences=tuple(
                pref._replace(input_data=prefs.get(pref.name, {}))
                for pref in preferences.get(name, ())
                if pref.name in prefs
            )
        )
        for name, prefs in tasks
    )


__all__ = ("Task",)

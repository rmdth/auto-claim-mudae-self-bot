from typing import Any

from src.bot.shared.domain import MudaeInfo
from src.bot.states.domain import (
    BotState,
    ChannelState,
    DailyState,
    KakeraState,
    RollState,
    State,
    StateType,
)
from src.ui import update_log_debug


def get_states(tasks: tuple[Any, ...]) -> tuple[set[BotState], set[ChannelState]]:
    seen_channel_states = set()
    seen_bot_states = set()
    update_log_debug(str(tasks))
    for task in tasks:
        if task.state is None:
            continue
        if isinstance(task.state, ChannelState):
            seen_channel_states.add(task.state)
        elif isinstance(task.state, BotState):
            seen_bot_states.add(task.state)
    update_log_debug(str(seen_bot_states))
    update_log_debug(str(seen_channel_states))
    return seen_bot_states, seen_channel_states


def create_state(type: StateType, data: MudaeInfo) -> State:
    match type:
        case ChannelState.ROLL:
            state = RollState(
                data.parsed_tu.rolls_available,
                data.max_rolls,
                data.delay_claim_roll,
                data.parsed_tu.claim_in,
                data.parsed_tu.rt_in,
                data.rt_max_cd,
                data.wished_rolls,
                data.wished_series,
            )
        case ChannelState.KAKERA:
            state = KakeraState(
                data.parsed_tu.curr_kakera_power,
                data.max_kakera_power,
                data.delay_claim_kakera,
                data.parsed_tu.kakera_claim_cost,
                data.parsed_tu.dk_in,
                data.dk_max_cd,
                data.wished_kakera,
            )
        case BotState.DAILY:
            state = DailyState(data.parsed_tu.daily_in)
        case _:
            raise Exception("No ")

    return state

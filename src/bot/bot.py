import asyncio
from collections import defaultdict

from discord import Client, Message

from src.bot.domain import Channel
from src.bot.shared.domain import (
    MUDAE_ID,
    ChannelInformation,
    ChannelMudaeSettings,
    KakeraMessage,
    MudaeInfo,
    RollMessage,
)
from src.bot.shared.logic import identify_message
from src.bot.states import (
    BotState,
    State,
    create_state,
    get_states,
)
from src.bot.tasks import Task
from src.bot.tasks.parse_tu.task import fetch_tu_data
from src.bot.tasks.shared.domain import OnMessageContext
from src.ui import (
    refresh_ui,
    update_bot_state,
    update_channel_state,
    update_log_debug,
    update_log_error,
    update_log_info,
)


def _prepare_tasks(tasks: tuple[Task, ...]) -> dict[str, tuple[Task, ...]]:
    grouped = defaultdict(list)
    for task in tasks:
        grouped[task.trigger].append(task)
    return {trigger: tuple(_tasks) for trigger, _tasks in grouped.items()}


class MudaeBot(Client):
    def __init__(
        self,
        tasks: tuple[Task, ...],
        channels_information: tuple[ChannelInformation, ...],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.channels_information: tuple[ChannelInformation, ...] = channels_information
        self.tasks_selected = tasks

        self.preferences: dict[str, bool]
        self.states: dict[BotState, State]

    async def on_ready(self):
        assert self.user is not None
        update_log_info(f"Logged on as {self.user} (ID: {self.user.id})!")

    async def _mudae_setup(self) -> None:
        await self.wait_until_ready()
        update_log_info("bot is ready")
        refresh_ui()

        _channel_information = self.channels_information
        _tasks_to_do = self.tasks_selected

        update_log_debug(str(_tasks_to_do))
        _bot_states, _channel_states = get_states(_tasks_to_do)
        self.tasks = _prepare_tasks(_tasks_to_do)
        update_log_debug(str(self.tasks))

        self.channels = dict()

        _datas: list[MudaeInfo] = []
        for channel_information in _channel_information:
            discord_channel = self.get_channel(channel_information["id"])

            if discord_channel is None:
                update_log_error(f"Channel {id} not found.")
                continue

            parsed_tu = await fetch_tu_data(
                self, discord_channel, channel_information["prefix"]
            )
            data = MudaeInfo(
                parsed_tu,
                channel_information["max_rolls"],
                channel_information["delay_claim_roll"],
                channel_information["max_kakera_power"],
                channel_information["delay_claim_kakera"],
                channel_information["rt_max_cd"],
                channel_information["dk_max_cd"],
                channel_information["wished_rolls"],
                channel_information["wished_series"],
                channel_information["wished_kakera"],
            )
            _datas.append(data)

            channel_states = {}
            for state in _channel_states:
                _state = create_state(state, data)
                channel_states[state] = _state
                update_channel_state(channel_information["id"], state, _state.print())

            self.channels[channel_information["id"]] = Channel(
                discord_channel,
                channel_states,  # type: ignore
                ChannelMudaeSettings(
                    channel_information["prefix"],
                    channel_information["command"],
                    channel_information["shifthour"],
                    channel_information["minute_reset"],
                ),
            )

        self.states = {}
        for state in _bot_states:
            _state = create_state(state, _datas[-1])
            self.states[state] = _state
            update_bot_state(state, _state.print())

        # Also create a task executer that takes in a trigger and executes something. This can be a decorator (if it doesnt interfere w the library) or w.e. But the trigger is compound by "event" + ("_entity") if needed

        if not (tasks := self.tasks.get("setup", ())):
            return

        results = await asyncio.gather(
            *(
                task.action(
                    task.context_generator(
                        self,
                        task.preferences,
                    )
                )
                for task in tasks
            ),
            return_exceptions=True,
        )
        update_log_debug(f"results: {results}")

    async def setup_hook(self) -> None:
        self._mudae_setup_task = self.loop.create_task(self._mudae_setup())

    async def on_message(self, message: Message):
        assert self.user is not None

        ctx = self.channels.get(message.channel.id)
        if ctx is None:
            return

        if message.author.id != MUDAE_ID or not message.embeds:
            return

        embed = message.embeds[0].to_dict()
        # update_log_debug(f"embed: {embed}")
        msg = identify_message(message, embed, self.user.name)
        # update_log_debug(f"msg: {msg}")

        match msg:
            case RollMessage():
                type = "on_message_roll"
            case KakeraMessage():
                type = "on_message_kakera"
            case None:
                type = "on_message"
            case _:
                raise ValueError(f"Unexpected message type: {msg}")

        if not (tasks := self.tasks.get(type, ())):
            return

        results = await asyncio.gather(
            *(
                task.action(
                    task.context_generator(
                        OnMessageContext(self, channel=ctx, message=msg),
                        task.preferences,
                    )
                )
                for task in tasks
            ),
            return_exceptions=True,
        )

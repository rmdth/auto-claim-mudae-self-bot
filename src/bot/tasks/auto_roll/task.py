from asyncio import sleep as asyncio_sleep

from src.bot.states import ChannelState, RollState
from src.bot.tasks.auto_roll.domain import AutoRollContext, BotWithChannels
from src.bot.tasks.shared.domain import Preference
from src.ui import update_channel_state, update_log_info


def auto_roll_context_generator(
    bot: BotWithChannels, preferences: tuple[Preference, ...]
) -> AutoRollContext:
    channels = bot.channels
    assert isinstance(channels, dict)
    return AutoRollContext(channels=channels)


async def auto_roll(ctx: AutoRollContext) -> None:
    while True:
        for channel in ctx.channels.values():
            discord_channel = channel.discord_channel
            command = channel.mudae_settings.command
            prefix = channel.mudae_settings.prefix
            roll_state: RollState = channel.states[ChannelState.ROLL.value]
            update_log_info(
                f"Auto-rolling in {discord_channel.name} with {roll_state.curr_rolls} rolls"
            )
            update_channel_state(
                channel.discord_channel.id,
                ChannelState.ROLL.value,
                roll_state.print(),
            )
            for _ in range(roll_state.curr_rolls):
                await asyncio_sleep(0.5)
                await discord_channel.send(f"{prefix}{command}")
                roll_state.curr_rolls -= 1
                update_channel_state(
                    channel.discord_channel.id,
                    ChannelState.ROLL.value,
                    roll_state.print(),
                )
            update_log_info(
                f"Finished Auto-roll in {discord_channel.name} with {roll_state.curr_rolls} rolls"
            )
            roll_state.curr_rolls = roll_state.max_rolls
        await asyncio_sleep(3600)

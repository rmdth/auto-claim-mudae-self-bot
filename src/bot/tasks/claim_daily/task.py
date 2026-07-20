from asyncio import create_task, sleep, wait
from random import choice as random_choice
from time import time as time_time
from typing import Any

from src.bot.shared.domain import MUDAE_ID
from src.bot.states.domain import BotState, DailyState
from src.bot.tasks.claim_daily.domain import DailyContext
from src.bot.tasks.shared.domain import Preference
from src.shared.retry import retry
from src.ui import update_bot_state

_DAILY_COOLDOWN = 72000


def daily_context_generator(
    bot: Any, preferences: tuple[Preference, ...]
) -> DailyContext:
    daily_state = bot.states[BotState.DAILY]
    assert isinstance(daily_state, DailyState)
    assert isinstance(bot.channels, dict)
    return DailyContext(bot=bot, channels=bot.channels, daily_state=daily_state)


@retry(delay=0.5)
async def _claim_daily(ctx: DailyContext):
    def check(reaction, user):
        return (
            reaction.message.id == sent_message.id
            and user.id == MUDAE_ID
            and str(reaction.emoji) == "✅"
        )

    def already_claimed_check(message):
        return (
            message.channel.id == sent_message.channel.id
            and message.author.id == MUDAE_ID
            and (
                "$daily" in message.content and "$vote" in message.content
            )  # faster than using regex
        )

    channel = ctx.channels[random_choice(tuple(ctx.channels.keys()))]
    discord_channel = channel.discord_channel
    mudae_settings = channel.mudae_settings

    sent_message = await discord_channel.send(f"{mudae_settings.prefix}daily")

    reaction_task = create_task(
        ctx.bot.wait_for("reaction_add", check=check, timeout=1.5)
    )
    message_task = create_task(
        ctx.bot.wait_for("message", check=already_claimed_check, timeout=1.5)
    )
    completed, remaining = await wait([reaction_task, message_task])

    num_e = 0
    for c in completed:
        if c.exception() is not None:
            num_e += 1

    if num_e == 2:
        raise TimeoutError()

    for r in remaining:
        r.cancel()

    ctx.daily_state.claim_in = time_time() + _DAILY_COOLDOWN


async def claim_daily(
    ctx: DailyContext,
):
    while True:
        if ctx.daily_state.claim_in <= time_time():
            update_bot_state(BotState.DAILY.value, ctx.daily_state.print())
            await _claim_daily(ctx)
            update_bot_state(BotState.DAILY.value, ctx.daily_state.print())
        await sleep(ctx.daily_state.claim_in - time_time())

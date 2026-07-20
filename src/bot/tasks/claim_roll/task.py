from asyncio import create_task, sleep, wait
from re import compile as re_compile
from time import time as time_time
from typing import Any

from discord.client import Client

from src.bot.shared.domain import MUDAE_ID, ClaimMethod, RollMessage
from src.bot.shared.logic import determine_claim_method
from src.bot.states import ChannelState, RollState
from src.bot.tasks.claim_roll.domain import ClaimRollContext, Roll
from src.bot.tasks.claim_roll.logic import (
    should_claim,
    time_till_next_claim,
    was_claimed,
)
from src.bot.tasks.shared.domain import OnMessageContext, Preference
from src.shared.retry import retry
from src.ui import (
    update_channel_state,
    update_log_debug,
    update_log_info,
    update_mudae_log_message,
    update_mudae_log_roll,
)

_RT_COOLDOWN = 72000.0
_RT_CLAIMED_PATTERN = re_compile(r".*\$rt.*\(\$rtu\)$")


def claim_roll_context_generator(
    ctx: OnMessageContext,
    preferences: tuple[Preference, ...],
) -> ClaimRollContext:
    assert isinstance(ctx.message, RollMessage)

    return ClaimRollContext(
        bot=ctx.bot,
        discord_channel=ctx.channel.discord_channel,
        prefix=ctx.channel.mudae_settings.prefix,
        roll_message=ctx.message,
        roll_state=ctx.channel.states[ChannelState.ROLL.value],
        minute_reset=ctx.channel.mudae_settings.minute_reset,
        shifthour=ctx.channel.mudae_settings.shifthour,
        preferences=preferences,
    )


async def claim_roll(ctx: ClaimRollContext) -> None:
    _is_wished = (
        ctx.roll_message.character in ctx.roll_state.wished_rolls
        or ctx.roll_message.series in ctx.roll_state.wished_series
    )
    if (
        claim_method := determine_claim_method(
            bool(ctx.roll_state.claim_in <= time_time()),
            bool(ctx.roll_state.reset_in <= time_time()),
        )
    ) is None or not should_claim(
        claim_method,
        ctx.roll_message,
        ctx.preferences,
        _is_wished,
        ctx.minute_reset,
        ctx.shifthour,
    ):
        update_mudae_log_roll(
            ctx.discord_channel.id,
            ctx.roll_message.print(),
            False,
            False,
            _is_wished,
        )
        return
    roll = Roll(roll_message=ctx.roll_message, is_wished=_is_wished)
    ctx.roll_state.watched_rolls.append(roll)
    update_mudae_log_roll(
        ctx.discord_channel.id,
        ctx.roll_message.print(),
        True,
        False,
        _is_wished,
    )
    update_log_info(
        f"Added {ctx.roll_message.print()} to watch list in {ctx.discord_channel.guild.name}"
    )
    update_log_info(
        f"{ctx.roll_state.watched_rolls} in {ctx.discord_channel.guild.name}"
    )
    if ctx.roll_state.lock.locked():
        return

    async with ctx.roll_state.lock:
        update_log_info(
            f"Waiting {ctx.roll_state.delay_claim_roll} before claiming watched rolls in {ctx.discord_channel.guild.name}"
        )
        await sleep(ctx.roll_state.delay_claim_roll)
        ctx.roll_state.watched_rolls.sort(
            key=lambda r: (r.is_wished, r.roll_message.kakera_value), reverse=False
        )
        update_log_info(
            f"Claiming watched rolls in {ctx.discord_channel.guild.name}..."
        )
        update_log_info(f"{ctx.roll_state.watched_rolls}")
        while ctx.roll_state.watched_rolls:
            r: Roll = ctx.roll_state.watched_rolls.pop()
            if (
                claim_method := determine_claim_method(
                    bool(ctx.roll_state.claim_in <= time_time()),
                    bool(ctx.roll_state.reset_in <= time_time()),
                )
            ) is None:
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"❌ ---- {r.roll_message.print()} CAN'T CLAIM ---- ❌",
                )
                update_log_info(
                    f"No claim method determined in {ctx.discord_channel.guild.name}, breaking loop"
                )
                break

            _is_wished = (
                ctx.roll_message.character in ctx.roll_state.wished_rolls
                or ctx.roll_message.series in ctx.roll_state.wished_series
            )

            if not should_claim(
                claim_method,
                r.roll_message,
                ctx.preferences,
                _is_wished,
                ctx.minute_reset,
                ctx.shifthour,
            ):
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"❌ ---- {r.roll_message.print()} SHOULD NOT CLAIM ---- ❌",
                )
                continue

            if was_claimed(r.roll_message):
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"❌ ---- {r.roll_message.print()} WAS CLAIMED BY OTHER ---- ❌",
                )
                continue

            if claim_method is ClaimMethod.RESET:
                await claim_rt(ctx.bot, ctx.discord_channel, ctx.roll_state, ctx.prefix)

            try:
                await r.roll_message.message.components[0].children[0].click()  # Claim
                ctx.roll_state.claim_in = time_time() + time_till_next_claim(
                    ctx.minute_reset, ctx.shifthour
                )
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"✅ ---- {r.roll_message.print()} CLAIMED SUCCESFULLY ---- ✅",
                )
                update_channel_state(
                    ctx.discord_channel.id,
                    ChannelState.ROLL.value,
                    ctx.roll_state.print(),
                )

            except Exception as e:
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"❌ ---- {r.roll_message.print()} ERROR CLAIMING ---- ❌",
                )
                update_log_info(f"Failed to claim roll: {e}, {e.__class__}")
                pass
        ctx.roll_state.watched_rolls.clear()
        update_log_info(f"Cleared watched rolls in {ctx.discord_channel.guild.name}")
        update_channel_state(
            ctx.discord_channel.id, ChannelState.ROLL.value, ctx.roll_state.print()
        )
    return


@retry()
async def claim_rt(
    bot: Client, discord_channel: Any, roll_state: RollState, prefix: str
) -> None:
    update_mudae_log_message(
        discord_channel.id,
        f"⚠️ ---- Claiming rt on {discord_channel.guild.name} ---- ⚠️",
    )
    sent_message = await discord_channel.send(f"{prefix}rt")

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
            and bool(_RT_CLAIMED_PATTERN.match(message.content))
        )

    reaction_task = create_task(bot.wait_for("reaction_add", check=check, timeout=1.5))
    message_task = create_task(
        bot.wait_for("message", check=already_claimed_check, timeout=1.5)
    )
    completed, remaining = await wait([reaction_task, message_task])

    num_e = 0
    for c in completed:
        if c.exception() is not None:
            num_e += 1
    if num_e == 2:
        raise TimeoutError

    for c in remaining:
        c.cancel()

    roll_state.reset_in = time_time() + _RT_COOLDOWN
    update_mudae_log_message(
        discord_channel.id,
        f"✅ ---- Successfully claimed rt on {discord_channel.guild.name} ---- ✅",
    )

    update_channel_state(
        discord_channel.id, ChannelState.ROLL.value, roll_state.print()
    )

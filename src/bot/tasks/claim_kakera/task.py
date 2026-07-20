from asyncio import sleep as asyncio_sleep
from time import time as time_time
from typing import Any

from discord.client import Client

from src.bot.shared.domain import MUDAE_ID, KakeraMessage
from src.bot.shared.logic import determine_claim_method
from src.bot.states import ChannelState, KakeraState
from src.bot.tasks.claim_kakera.domain import ClaimKakeraContext, Kakera
from src.bot.tasks.claim_kakera.logic import (
    _KAKERA_PRIORITY,
    get_kakera_claim_cost,
    should_claim,
)
from src.bot.tasks.shared.domain import OnMessageContext, Preference
from src.shared.retry import retry
from src.ui import (
    update_channel_state,
    update_log_debug,
    update_log_info,
    update_mudae_log_kakera,
    update_mudae_log_message,
)

_DK_COOLDOWN = 72000


def claim_kakera_context_generator(
    ctx: OnMessageContext, preferences: tuple[Preference, ...]
) -> ClaimKakeraContext:
    assert isinstance(ctx.message, KakeraMessage)
    return ClaimKakeraContext(
        bot=ctx.bot,
        discord_channel=ctx.channel.discord_channel,
        prefix=ctx.channel.mudae_settings.prefix,
        kakera_state=ctx.channel.states[ChannelState.KAKERA.value],
        kakera_message=ctx.message,
        preferences=preferences,
    )


async def claim_kakeras(ctx: ClaimKakeraContext) -> None:
    _is_wished = ctx.kakera_message.color in ctx.kakera_state.wished_kakera
    claim_cost = get_kakera_claim_cost(
        ctx.kakera_state.claim_cost,
        ctx.kakera_message.color,
        ctx.kakera_message.key_amount,
        ctx.kakera_message.is_owned_char,
    )

    if (
        claim_method := determine_claim_method(
            ctx.kakera_state.power >= claim_cost,
            bool(ctx.kakera_state.reset_in <= time_time()),
        )
    ) is None or not should_claim(
        claim_method, ctx.kakera_message, ctx.preferences, _is_wished
    ):
        update_mudae_log_kakera(
            ctx.discord_channel.id,
            ctx.kakera_message.print(),
            False,
            _is_wished,
        )
        return

    kakera = Kakera(
        kakera_message=ctx.kakera_message,
        claim_cost=claim_cost,
        is_wished=_is_wished,
        priority=_KAKERA_PRIORITY[ctx.kakera_message.color],
    )
    ctx.kakera_state.watched_kakera.append(kakera)
    update_log_info(
        f"Added {ctx.kakera_message.print()} to watch list with priority {kakera.priority} in {ctx.kakera_state.watched_kakera}"
    )
    update_mudae_log_kakera(
        ctx.discord_channel.id,
        ctx.kakera_message.print(),
        True,
        kakera.is_wished,
    )
    if ctx.kakera_state.lock.locked():
        return

    async with ctx.kakera_state.lock:
        update_log_info(
            f"Waiting {ctx.kakera_state.delay_claim_kakera} before claiming watched kakera"
        )
        await asyncio_sleep(ctx.kakera_state.delay_claim_kakera)
        ctx.kakera_state.watched_kakera.sort(
            key=lambda k: (-k.claim_cost, k.is_wished, k.priority), reverse=False
        )
        update_log_info(
            f"Claiming watched kakera in {ctx.discord_channel.guild.name}..."
        )
        while ctx.kakera_state.watched_kakera:
            k: Kakera = ctx.kakera_state.watched_kakera.pop()
            update_log_info(
                f"Claiming {k.kakera_message.color} in {ctx.discord_channel.guild.name}..."
            )
            claim_cost = get_kakera_claim_cost(
                ctx.kakera_state.claim_cost,
                k.kakera_message.color,
                k.kakera_message.key_amount,
                k.kakera_message.is_owned_char,
            )
            if (
                claim_method := determine_claim_method(
                    ctx.kakera_state.power >= claim_cost,
                    bool(ctx.kakera_state.reset_in <= time_time()),
                )
            ) is None:
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"❌ ---- {k.kakera_message.print()} CAN'T CLAIM ---- ❌",
                )
                update_log_debug(
                    f"No claim method determined in {ctx.discord_channel.guild.name}, breaking loop"
                )
                break

            is_wished = k.kakera_message.color in ctx.kakera_state.wished_kakera
            if not should_claim(
                claim_method, k.kakera_message, ctx.preferences, is_wished
            ):
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"❌ ---- {k.kakera_message.print()} SHOULD NOT CLAIM ---- ❌",
                )
                update_log_info(
                    f"Kakera {k.kakera_message.print()} not claimed in {ctx.discord_channel.guild.name}"
                )
                continue
            # if was_claimed(k):
            # continue
            # The only way to know if kakera was claimed is checking the chat history, but it can also count kakera claimed by other people
            # Is probably better to check your kakera power before or after some time or certain action like seeing kakera with cooldown in par with the claim_window
            if claim_method == "reset":
                await claim_dk(
                    ctx.bot,
                    ctx.discord_channel,
                    ctx.kakera_state,
                    ctx.prefix,
                )
            try:
                await (
                    k.kakera_message.message.components[0].children[0].click()
                )  # Claim
                ctx.kakera_state.power -= k.claim_cost
                update_log_info(
                    f"Claimed kakera {k.kakera_message.print()} in {ctx.discord_channel.guild.name}"
                )
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"✅ ---- {k.kakera_message.print()} WAS CLAIMED SUCCESFULLY ---- ✅",
                )
                update_channel_state(
                    ctx.discord_channel.id,
                    ChannelState.KAKERA.value,
                    ctx.kakera_state.print(),
                )
            except Exception as e:
                update_mudae_log_message(
                    ctx.discord_channel.id,
                    f"❌ ---- {k.kakera_message.print()} ERROR CLAIMING ---- ❌",
                )
                update_log_info(f"Failed to claim kakera: {e}, {e.__class__}")
                pass
        ctx.kakera_state.watched_kakera.clear()
        update_log_info(f"Cleared watched kakera in {ctx.discord_channel.guild.name}")
        update_channel_state(
            ctx.discord_channel.id, ChannelState.KAKERA.value, ctx.kakera_state.print()
        )
    return


@retry(delay=0.5)
async def claim_dk(
    bot: Client,
    discord_channel: Any,
    kakera_state: KakeraState,
    prefix: str,
) -> None:
    update_mudae_log_message(
        discord_channel.id,
        f"⚠️ ---- Claiming dk on {discord_channel.guild.name} ---- ⚠️",
    )
    sent_message = await discord_channel.send(f"{prefix}dk")

    def check(message):
        return (
            message.channel.id == sent_message.channel.id
            and message.author.id == MUDAE_ID
            and (
                "**<:kakera:469835869059153940>kakera" in message.content
                or ("$dk" in message.content and "!" not in message.content)
            )
        )

    await bot.wait_for(
        "message",
        check=check,
        timeout=1.5,
    )
    update_mudae_log_message(
        discord_channel.id,
        f"✅ ---- Successfully claimed dk on {discord_channel.guild.name} ---- ✅",
    )
    kakera_state.reset_in = time_time() + _DK_COOLDOWN
    kakera_state.power = kakera_state.max

    update_channel_state(
        discord_channel.id, ChannelState.KAKERA.value, kakera_state.print()
    )

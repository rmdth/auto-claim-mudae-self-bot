from re import compile as re_compile

from discord import Message
from discord.types.embed import Embed

from src.bot.shared.domain import (
    ClaimMethod,
    KakeraMessage,
    MudaeMessage,
    RollMessage,
)

_ROLL_KEYS_PATTERN = re_compile(r"\(.+(\d).+\)")


def extract_key_amount(description: str) -> int:
    if match := _ROLL_KEYS_PATTERN.findall(description):
        return int(match[0])
    return 0


_ROLL_SERIES_PATTERN = re_compile(r"([\s\S]+?)\s(?::\w+:|\*\*\d+\*\*)")
_ROLL_KAKERA_PATTERN = re_compile(r"\*\*(.+)\*\*")


def extract_serie(description: str) -> str:
    if not (match := _ROLL_SERIES_PATTERN.findall(description)):
        return ""
    return match[0].replace("\n", " ").rstrip()


def extract_kakera_value(description: str) -> int:
    match = _ROLL_KAKERA_PATTERN.findall(description)
    if match:
        return int(match[0].replace(".", ""))
    return 0


def determine_claim_method(
    claim_ready: bool,
    reset_ready: bool,
) -> ClaimMethod | None:
    if claim_ready:
        return ClaimMethod.CLAIM
    elif reset_ready:
        return ClaimMethod.RESET
    return


def identify_message(
    message: Message, embed: Embed, user_name: str
) -> MudaeMessage | None:

    if "image" not in embed or "author" not in embed or "description" not in embed:
        return None
    if "footer" in embed and "text" in embed["footer"]:
        if "/" in embed["footer"]["text"]:
            return None
        if (
            message.components
            and "kakera" in message.components[0].children[0].emoji.name  # type: ignore
        ):
            return KakeraMessage(
                message=message,
                color=message.components[0].children[0].emoji.name,  # type: ignore
                key_amount=extract_key_amount(embed["description"]),
                is_owned_char=embed["footer"]["text"] == user_name,
            )

    return RollMessage(
        message=message,
        character=embed["author"]["name"],
        series=extract_serie(embed["description"]),
        kakera_value=extract_kakera_value(embed["description"]),
        key_amount=extract_key_amount(embed["description"]),
    )

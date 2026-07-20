from datetime import timedelta

import pytest

from src.shared.infrastructure.discord.parsers import (
    get_claim_timedelta,
    get_daily_timedelta,
    get_dk_timedelta,
    get_kakera_and_cost,
    get_rolls,
    get_rt_timedelta,
    get_tu_information,
    has_current_claim,
    is_dk_confirmation,
    is_tu_message,
)


@pytest.fixture
def tu_message_es() -> str:
    return """**cool_name**, __puedes__ reclamar ahora mismo. El siguiente reclamo será en **17** min.
    Tienes **10** rolls restantes.
    El siguiente reinicio será en **17** min.
    ¡$daily está disponible!

    ¡__Puedes__ reaccionar a kakera en este momento!
    Poder: **110%**
    Cada botón de kakera consume 36% de su poder de reacción.
    Tus personajes con 10+ llaves, consumen la mitad del poder (18%)
    Capital: **38.789**<:kakera:469835869059153940>

    ¡$rt está disponible!
    ¡$dk está listo!
    ¡Puedes votar en este momento!

    Capital: **3.900** <:sp:1437140700604137554>
    **=>** $tuarrange"""


def test_is_tu_message(tu_message_es) -> None:
    assert is_tu_message(tu_message_es)


def test_has_current_claim(tu_message_es) -> None:
    assert has_current_claim(tu_message_es) is True


def test_get_claim_timedelta(tu_message_es) -> None:
    assert get_claim_timedelta(tu_message_es) == timedelta()


def test_get_daily_timedelta(tu_message_es) -> None:
    assert get_daily_timedelta(tu_message_es) == timedelta()


def test_get_rt_timedelta(tu_message_es) -> None:
    assert get_rt_timedelta(tu_message_es) == timedelta()


def test_get_dk_timedelta(tu_message_es) -> None:
    assert get_dk_timedelta(tu_message_es) == timedelta()


def test_get_kakera_and_cost(tu_message_es) -> None:
    kakera, kakera_default_cost = get_kakera_and_cost(tu_message_es)
    assert kakera == 110
    assert kakera_default_cost == 36


def test_get_rolls(tu_message_es) -> None:
    rolls = get_rolls(tu_message_es)
    assert rolls == 10


def test_get_tu_information(tu_message_es) -> None:
    FIXED_NOW = 1000.0

    result = get_tu_information(tu_message_es, FIXED_NOW)
    assert result["daily_cooldown_until"] == pytest.approx(1000.0)
    assert result["rt_cooldown_until"] == pytest.approx(1000.0)
    assert result["dk_cooldown_until"] == pytest.approx(1000.0)
    assert result["kakera_value"] == 110
    assert result["kakera_cost"] == 36
    assert result["rolls_available"] == 10


def test_dk_confirmation_pattern() -> None:
    message_1 = "Excelente, **+320**<:kakera:469835869059153940>kakera añadidos a tu colección. (**48.626** total)."
    message_2 = "**+261**<:kakera:469835869059153940>kakera añadidos a tu colección. (**37.837** total)."
    message_3 = "lol"
    assert is_dk_confirmation(message_1)
    assert is_dk_confirmation(message_2)
    assert not is_dk_confirmation(message_3)


def test_series_extraction() -> None:
    from src.shared.infrastructure.discord.parsers import extract_series

    message = (
        "The Legend of Zelda: Ocarina of\nTime\n**47**<:kakera:469835869059153940>"
    )
    message_2 = "Life is Strange\n**103**<:kakera:469835869059153940>"
    message_3 = (
        "The Legend of Zelda: Breath of\nthe\nWild\n**50**<:kakera:469835869059153940>"
    )
    assert extract_series(message) == "The Legend of Zelda: Ocarina of Time"
    assert extract_series(message_2) == "Life is Strange"
    assert extract_series(message_3) == "The Legend of Zelda: Breath of the Wild"

from datetime import timedelta

import pytest

from src.core import parsers


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
    assert parsers.is_tu_message(tu_message_es)


def test_available_claim(tu_message_es) -> None:
    assert parsers.available_claim(tu_message_es) == timedelta()


def test_get_claim_timedelta(tu_message_es) -> None:
    assert parsers.get_claim_timedelta(tu_message_es) == timedelta(minutes=17)


def test_get_daily_timedelta(tu_message_es) -> None:
    assert parsers.get_daily_timedelta(tu_message_es) == timedelta()


def test_get_rt_timedelta(tu_message_es) -> None:
    assert parsers.get_rt_timedelta(tu_message_es) == timedelta()


def test_get_dk_timedelta(tu_message_es) -> None:
    assert parsers.get_dk_timedelta(tu_message_es) == timedelta()

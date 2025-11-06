"""Shared regular expression patterns for the Mudae bot."""

from re import compile as re_compile


FIND_TU_PATTERN = re_compile(r"\*\*=>\*\* \$tuarrange")


CURRENT_ROLLS_IN_TU_PATTERN = re_compile(r"\*\*(\d+)\*\* roll")

CURRENT_CLAIM_IN_TU_PATTERN = re_compile(r"__(.+)__.+\.")
CURRENT_CLAIM_TIME_PATTERN = re_compile(r",\D+(\d+)?\D+(\d+).+min")

DAILY_IN_TU_PATTERN = re_compile(r"\$daily\D+(\d\d+)?\D+(\d+)")
RT_IN_TU_PATTERN = re_compile(r"\$rt\D+(\d+)?\D+(\d+)")
DK_IN_TU_PATTERN = re_compile(r"\$dk\D+(\d+)?\D+(\d+)")

KAKERA_IN_TU_PATTERN = re_compile(r"(\d+)%")
KAKERA_COLOR_PATTERN = re_compile(r":(\w+):")
KAKERA_DK_CONFIRMATION_PATTERN = re_compile(
    r"\*\*\+\d+\*\*<:kakera:469835869059153940>kakera"
)

ROLL_KAKERA_PATTERN = re_compile(r"\*\*(.+)\*\*")
ROLL_CHAR_PATTERN = re_compile(r"(.+)\s")
ROLL_SERIES_PATTERN = re_compile(r"(.+)\s")
KAKERA_KEYS_PATTERN = re_compile(r"\(.+(\d).+\)")

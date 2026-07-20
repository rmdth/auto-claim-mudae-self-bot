import sys
from asyncio import to_thread

import readchar

from src.ui import setup
from src.ui.update import refresh_ui


def move_right() -> tuple[int, bool]:
    return min(setup.page + 1, setup.max_pages - 1), True


def move_left() -> tuple[int, bool]:
    return max(setup.page - 1, 0), True


def stop() -> tuple[int, bool]:
    return 0, False


_keymap = {
    readchar.key.RIGHT: move_right,
    "l": move_right,
    readchar.key.LEFT: move_left,
    "h": move_left,
    readchar.key.CTRL_C: stop,
    readchar.key.CTRL_Z: stop,
    "q": stop,
}


async def listen_keys(bot) -> None:
    while True:
        try:
            key = await to_thread(readchar.readkey)
        except KeyboardInterrupt:
            key = readchar.key.CTRL_C

        _continue = on_input(key)
        if not _continue:
            await bot.close()
            sys.exit(0)

        refresh_ui()


def on_input(input) -> bool:
    try:
        setup.page, _continue = _keymap[input]()
        return _continue
    except Exception:
        return True

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/downloads/)

# Auto-Claim-Mudae-Self-Bot

## Disclaimer

Automating user accounts is against the Discord ToS. I don't recommend using it. Do so at your own risk.

## Overview

Python script that requires settings to mimic your rolling behavior of claiming kakera and rolls for the mudae waifu game. First it's setup with the given settings, then rolls every hour on given channels, validates messages so that it only reads the given channels and Mudae's messages, discerns if is a claimable roll or a kakera claim, then checks if it should claim with it's settings or if is the last claim hour to add the roll to claims, when one roll is added after given delay will check it's rolls to choose the one with the highest kakera value (will always prioritize the wished ones if there is any).

## What does it do

- Gets $tu information on setup
- Auto rolling on given channels.

## Available tasks:

- `claim_daily`: Auto claims daily
- `claim_roll`: Can claim by: characters, series, last_claim, can use dk. If the wanted claim was claimed, it will try to claim another based on the same criteria.
- `claim_kakera`: Can claim by: color, Any, can use rt.
- `claim_roll` and `claim_kakera` have their own delay.
- `claim_roll` and `claim_kakera` have priority with wishes and color/cost/kakera value.

## Cool things to add

- Adjust to different restart claims. Currently I dont know how does the 120 minute claim works to make it.
- Automate the sphere stuff

## Known Issues

- I don't participate in big servers, so:
  - You can't really be sure if you claimed kakera.
  - When claiming $dk it may think it claimed it since the verification looks if the content contains "$dk" and doesn't have (not) "!"

## Notes

- I don't really use github. I'm a new programmer who wants to be a great one so any criticism is welcome.
- This project was heavily inspired by this deprecated [one](https://github.com/vivinano/MudaeAutoBot).
- Tested in private servers with a few players.
- You need to have rt unlocked.
- $togglerolls must be disabled and $togglebutton enabled

## Installation

1. **Clone the repo**:

```
git clone https://github.com/rmdth/auto-claim-mudae-self-bot.git
cd auto-claim-mudae-self-bot
```

2. **Setup enviroment**:
   This project uses [uv](https://docs.astral.sh/uv/) be sure to install it.

After doing so, you can do:

```
uv sync
```

That's it

4. **Make sure to read and Change bot-settings-example.toml**.

5. **Run**:
   `uv run main.py`

## Configuration reference

You will edit or copy `bot-settings-example.toml` and rename that to `bot-settings.toml`. Most values can be grabbed with Mudae's `$settings` command.

- `user_token`: Your Discord account token.
- `debug`: bool, to see it in the UI.

- `tasks`: List of tasks to run, more info in the `.toml`. It can be complicated to config/understand but by default i would say it has a great config.

Each `[[channels_information]]` block is one channel (copy it to add more):

- `id`: Channel id where rolls happen.
- `max_rolls`: Max rolls you can do in that channel.
- `prefix`: Server prefix for mudae.
- `command`: Command you want to roll.
- `shifthour`: Server `$shifthour` value.
- `minute_reset`: Minute where rolls restart.
- `delay_claim_roll`: Delay you want for roll claims.
- `delay_claim_kakera`: Delay you want for kakera claims.
- `rt_max_cd`: Cooldown threshold before trying `$rt` again. Make sure to adjust it based on your own cooldown
- `dk_max_cd`: Cooldown threshold before trying `$dk` again. Make sure to adjust it based on your own cooldown
- `max_kakera_power`: Your maximum kakera power.
- `wished_rolls`: Characters to always claim. _Case sensitive_.
- `wished_series`: Series to always claim. _Case sensitive_.
- `wished_kakera`: Kakera colors to click [Might not work since it's not tested] (`"kakera"` means any color leave it as it is if you want that ELSE add the color initial in uppercase. Example: `kakeraO` for orange). [reference](https://mudae.fandom.com/wiki/Kakera) _Case sensitive_.

## Contributions

As I mentioned I don't really use Github so I don't know how would you do it. But you are welcome to contribute to the project!

If you need to install dependencies use [uv](https://docs.astral.sh/uv/ accordingly.

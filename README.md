# Auto-Claim-Mudae-Self-Bot

## Disclaimer

Automating user accounts is against the Discord ToS. I don't recommend using it. Do so at your own risk.

## Overview

Python script that requires settings to mimic your rolling behavior of claiming kakera and rolls for the mudae waifu game. First it's setup with the given settings, then rolls every hour on given channels, validates messages so that it only reads the given channels and Mudae's messages, discerns if is a claimable roll or a kakera claim, then checks if it should claim with it's settings or if is the last claim hour to add the roll to claims, when one roll is added after given delay will check it's rolls to choose the one with the highest kakera value (will always prioritize the wished ones if there is any).

## What does it do

- Claims wishlist characters and given ones.
- Claims by series.
- Claims kakera with desired colors.
- Claims with given delay.
- Auto claim if its on given last seconds.
- Checks if dk and rt are available to use them.
- Gets $tu information on setup
- Reconnects.

## Cool things to add

- Adjust claim kakera cost for characters with 10+ keys.
- Adjust to different restart claims. Currently I dont know how does the 120 minute claim works to make it.
- Currently is made for kakera value efficiency. It would be cool to use rt only for wished ones or have different modes if there are any.
- Tests.
- Maybe Inherit from the discord.TextChannel or the actual Abstract Class to Channel, so when it takes a channel as a parameter it can be a channel object you don't have to provide prefix, minute_reset and those stuff.

## Known Issues

- When someone else claims first it still believes it claimed.

## Notes

- I don't really use github. I'm a new programmer who wants to be a great one so any criticism is welcome.
- This project was heavily inspired by this deprecated [one](https://github.com/vivinano/MudaeAutoBot).
- Tested in private servers with a few players.

## Contributions

As I mentioned I don't really use Github so I don't know how would you do it. But you are welcome to contribute to the project!

## Installation

1. **Clone the repo**:

```
git clone https://github.com/goatedguy67/auto-claim-mudae-self-bot.git
cd auto-claim-mudae-self-bot
```

2. **Create a virtual enviroment** (Optional but recommended):

```
# On Windows
python -m venv .venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source venv/bin/activate
```

3. **Install dependencies**:

```
pip install -r requirements.txt
```

4. **Make sure to read and Change bot-settings-example.toml**.

5. **Run**:
   `python main.py`

## Configuration reference

You will edit or copy `bot-settings-exmaple.toml` and rename that to `bot-settings.toml`. Most values can be grabbed with Mudae's `$settings` command.

- `token`: Your Discord account token.
- `UTC_delta`: Your offset from UTC (for example VET is UTC-4 so `-4`).

Each `[[channels_information]]` block is one channel (copy it to add more):

- `id`: Channel id where rolls happen.
- `[channels_information.settings]`: Everything inside is per channel.
  - `max_rolls`: Max rolls you can do in that channel.
  - `prefix`: Server prefix for mudae.
  - `command`: Command you want to roll.
  - `shifthour`: Server `$shifthour` value.
  - `restart_time_minute`: Minute where rolls restart.
  - `uptime`: Delay you want for roll claims.
  - `delay`: Delay you want for kakera claims.
  - `max_rt_cooldown_in_seconds`: Cooldown threshold before trying `$rt` again. Make sure to adjust it based on your own cooldown
  - `kakera_power_total`: Your total kakera power.
  - `wish_list`: Characters to always claim. _Case sensitive_.
  - `wish_series`: Series to always claim. _Case sensitive_.
  - `wish_kakera`: Kakera colors to click (`"kakera"` means any color leave it as it is if you want that ELSE add the color initial in uppercase. Example: `kakeraO` for orange). [reference](https://mudae.fandom.com/wiki/Kakera) _Case sensitive_.
  - `min_kakera_value`: Minimum kakera value required to auto claim.

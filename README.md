# Auto-Claim-Mudae-Self-Bot

## Disclaimer

Automating user accounts is against the Discord ToS. I don't recommend using it. Do so at your own risk.

## Overview

Python script that requires settings to mimic your rolling behavior of claiming kakera and rolls for the mudae waifu game. First it's setup with the given settings, then rolls every hour on given channels, validates messages so that it only reads the given channels and Mudae's messages, discerns if is a claimable roll or a kakera claim, then checks if it should claim with it's settings or if is the last claim hour to add the roll to claims, when one roll is added after given delay will check it's rolls to choose the one with the highest kakera value (will always prioritize the wished ones if there is any).

## What does it do

- Claims wishlist characters and given ones.
- Claims by series.
- Claims kakera.
- Claims with given delay.
- Auto claim if its last hour claim.
- Checks if dk and rt are available to use them.
- Reconnects.

## Cool things to add

- Adjust to different restart claims. Currently I dont know how does the 120 minute claim works to make it.
- Currently is made for kakera value efficiency. It would be cool to use rt only for wished ones or have different modes if there are any.
- Choose which kakera color you wanna claim.
- Adjust claim kakera cost for characters with 10+ keys.
- No need to provide the $ku and $rtu information aswell as the availability of claim and rt to settings and get them at setup.
- Tests.

- Maybe Inherit from the discord.TextChannel or the actual Abstract Class to Channel, to add prefix so it doesn't get passed as another parameter

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

4. **Read and Change bot-settings-example.toml**.

5. **Run**:
   `python MudaeBot.py`

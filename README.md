# PyParkingBot

Simple telegram bot on python3 for parking booking and some statistics about parking use.

This bot uses the [python telegram bot](https://python-telegram-bot.org) framework to make Telegram API calls.

All messages are in russian, but you can adapt it with no effort, there about 10 of them.

## Installation

### Install 

It's really simple, just do following steps to run from source (you need python3 & token from your bot).
1. `git clone https://github.com/GarikFirst/PyParkingBot` - clone this repo.
2. `pip3 install -r requirements.txt` - install requirements.
3. specify your bot _token_ in **token** key in `config.json`.
4. specify your bot _user id_ in **bot_owner** tag in `config.json`, if you'd like to use admin commands.

### Launch the bot

1. `python3 parking_bot.py -c CONFIG-FILE`, default (no keys specified) is **config.json**.
2. Your bot is running! You can go and check your bot in Telegram client by sending /start command.

## Usage

Logic is really simple - each place has three states:
- free
- reserved
- occupied

and can change state between these possible states (free -> reserved -> occupied -> free -> ...). 

User can make reserve for place (and cancel if necessary), than occupy the place, then free the place. Since place occupied no other user can take this place.

Also, anybody have an option to free all parking if at least one of the places is not free (for those, who forget to check out from parking in the evening).

There is some statistics (like top usage of the places, persons, weekdays, etc) about usage available in statistics "menu".

## Admin commands

This bot has several admin commands.

- `/logs n` (n can be omitted) - bot will reply with message that contains n lines from logfile, if n is omitted, than **log_length** from config file number of lines
- `/whitelist` - toggle whitelist mode on and of. If whitelist mode is on, bot will reply to users that already using the bot (users in **users.json**)
- `get_stats` - bot will reply with message that contains statistics in json format (not with file)
- `set_stats {json}` - overwrite current statistics with provided json formated message (not a file) as argument

## Config options

| Option             | Description                       |
| ------------------ | --------------------------------- |
| owner_id           | bot admin user_id                 |
| places             | list of desired parking places    |
| token              | bot token                         |
| whitelist          | whitelist mode on start           |
| logging/log_file   | filename for logfile              |
| logging/log_length | default log length for `/logs`    |      
| users_file         | filename for users file           |
| data_file_prefix   | prefix for data files             |

Copyright © 2021 Igor Bulekov
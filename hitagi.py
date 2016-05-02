#!/bin/env python3

import util
from bot import Bot

config = util.ConfigUtils()  # Create config object
bot = Bot(config)  # Create bot object


def main():
    bot.init()
    while True:  # Main loop
        bot.get_update()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        bot.session(shutdown=True)

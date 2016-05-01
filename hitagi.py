#!/bin/env python3

from bot import Bot
import util

config = util.ConfigUtils()  # Create config object
bot = Bot(config)  # Create bot object


def main():
    bot.init()
    while True:  # Main loop
        bot.get_update()

if __name__ == '__main__':
    main()

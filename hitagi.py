#!/bin/env python3

import util
from bot import Bot


def main():
    config = util.ConfigUtils()  # Create config object
    bot = Bot(config)  # Create bot object
    bot.init()
    try:
        while True:  # Main loop
            bot.get_update()
    except KeyboardInterrupt:
        bot.session(shutdown=True)


if __name__ == '__main__':
    main()

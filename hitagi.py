#!/bin/env python3
from bot import Bot
import os


def main():
    if not os.path.exists('data'):
        os.makedirs('data/files')
        os.makedirs('data/logs')
    x = 0
    bot = Bot()  # Create bot object
    while True:
        x = bot.get_update(x)


if __name__ == '__main__':
    main()

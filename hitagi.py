#!/bin/env python3
from bot import Bot


def main():
    x = 0
    bot = Bot()  # Create bot object
    while True:
        x = bot.get_update(x)


if __name__ == '__main__':
    main()

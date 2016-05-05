#!/bin/env python3
from bot import Bot


def main():
    bot = Bot()  # Create bot object
    bot.get_update(0)


if __name__ == '__main__':
    main()

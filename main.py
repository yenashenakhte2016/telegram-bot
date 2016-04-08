from tgapi import TelegramAPI
import config
import time

bot = TelegramAPI(config.API, config.plugins)

while True:  # Main loop
    bot.get_update()
    time.sleep(.5)

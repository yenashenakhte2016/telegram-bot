from tgapi import TelegramAPI
import util
import time


config = util.ConfigUtils()  # Create config object
bot = TelegramAPI(config)  # Create bot object

while True:  # Main loop
    bot.get_update()  # It's possible to run multiple bots here, be sure to provide separate API keys
    time.sleep(.5)  # Lower or raise this to adjust resource usage

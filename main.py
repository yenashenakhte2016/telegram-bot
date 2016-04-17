from bot import Bot
import util

config = util.ConfigUtils()  # Create config object
bot = Bot(config)  # Create bot object

while True:  # Main loop
    bot.get_update()  # It's possible to run multiple bots here, be sure to provide separate API keys

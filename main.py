from bot import Bot
import util

config = util.ConfigUtils()  # Create config object
bot = Bot(config)  # Create bot object

while True:  # Main loop
    bot.get_update()

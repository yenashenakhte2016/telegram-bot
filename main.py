from tgrequest import TelegramRequest
from plugin import PluginInit
import config
import requests

offset = 0
session = requests.Session()
getUpdateObj = TelegramRequest("getUpdates")
getMeObj = TelegramRequest("getMe")
getMe = getMeObj.fetch()
plugins = PluginInit(config.plugins)


while True:  # Main loop
    append = "?offset={}".format(offset)
    getUpdate = getUpdateObj.fetch(append)
    for i in getUpdate['result']:
        msg = i['message']
        plugins.process_regex(msg)
        offset = i['update_id'] + 1

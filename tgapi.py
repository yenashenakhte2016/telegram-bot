import requests
import util
from plugin_handler import PluginInit


class TelegramAPI:
    def __init__(self, bot_token, plugin_list):
        self.url = "https://api.telegram.org/bot{0}/".format(bot_token)
        self.session = requests.session()
        self.update_id = 0
        self.getMe = self.get_me()
        self.plugin_handle = PluginInit(plugin_list, self.getMe)
        self.current_msg = None

    def get_update(self):  # Gets new messages and sends them to plugin_handler
        url = "{}getUpdates?offset={}".format(self.url, self.update_id)
        response = util.fetch(self.session, url)
        for i in response['result']:
            self.current_msg = i['message']
            self.send_message(self.plugin_handle.process_regex(self.current_msg))
            self.update_id = i['update_id'] + 1  # Updates update_id's value

    def send_message(self, content):  # sendMessage
        url = "{}sendMessage".format(self.url)  # Creates URL
        default = {  # Default return
            'chat_id': self.current_msg['chat']['id'],
            'text': "",
            'parse_mode': "HTML",
            'reply_to_message_id': self.current_msg['message_id']
        }
        if isinstance(content, str):  # If only a string is given sends with default option
            default['text'] = content
        elif isinstance(content, dict):  # If a dictionary is returned, overwrites default values
            for k, v in content:
                default[k] = v
        return util.make_request(self.session, url, default)  # Sends it to off to be sent

    def get_me(self):  # getMe
        url = "{}getMe".format(self.url)
        return util.fetch(self.session, url)

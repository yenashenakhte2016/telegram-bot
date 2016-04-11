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
            self.route_return(self.plugin_handle.process_regex(self.current_msg))
            self.update_id = i['update_id'] + 1  # Updates update_id's value

    def route_return(self, returned_value):  # Figures out where plugin return values belong
        content = {}
        if isinstance(returned_value, str):  # If string sendMessage
            content['text'] = returned_value
            self.send_message(content)
        elif isinstance(returned_value, dict):
            self.send_method(returned_value)

    def get_me(self):  # getMe
        url = "{}getMe".format(self.url)
        return util.fetch(self.session, url)

    def send_message(self, content):  # If String is returned
        package = {'url': "{}sendMessage".format(self.url)}
        package['data'] = {  # Default return
            'chat_id': self.current_msg['chat']['id'],
            'text': "",
            'parse_mode': "HTML",
            'reply_to_message_id': self.current_msg['message_id']
        }
        package['data']['text'] = content['text']
        util.post_post(self.session, package)

    def send_method(self, returned_value):  # If dict is returned
        method = returned_value['method']
        del returned_value['method']
        package = {'url': "{}{}".format(self.url, method)}
        for k, v in returned_value.items():
            package[k] = v
        if 'chat_id' not in package['data']:  # Makes sure a chat_id is provided
            package['data']['chat_id'] = self.current_msg['chat']['id']
        util.post_post(self.session, package)

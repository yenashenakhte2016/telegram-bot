import config
import requests


class TelegramResponse:

    def __init__(self, method):
        self.url = "https://api.telegram.org/bot{0}/{1}".format(config.API, method)
        self.session = requests.session()

    def make_request(self, content, append=""):
        response = self.session.post(
            url=self.url + append,
            data=content
        ).json()
        return response

    def send_message(self, content, msg):
        default = {
            'chat_id': msg['chat']['id'],
            'text': "",
            'parse_mode': "Markdown",
            'reply_to_message_id': msg['message_id']
        }
        if isinstance(content, str):
            default['text'] = content
        elif isinstance(content, dict):
            for k, v in content:
                default[k] = v
        return self.make_request(default)

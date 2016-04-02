import requests
import config


class TelegramResponse:

    def __init__(self, type):
        self.url = "https://api.telegram.org/bot{0}/{1}".format(config.API, type)

    def make_request(self, content, append=""):
        session = requests.Session()  # Make this part of init and global
        response = session.post(
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

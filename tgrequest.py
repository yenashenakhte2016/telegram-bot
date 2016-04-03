import config
import json
import requests


class TelegramRequest:

    def __init__(self, request_type):  # Create session
        self.url = "https://api.telegram.org/bot{0}/{1}".format(config.API, request_type)
        self.session = requests.session()

    def fetch(self, append=""):
        response = self.session.get(self.url + append)
        return json.loads(response.text)

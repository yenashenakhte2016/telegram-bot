import config
import requests
import json


class TelegramRequest:

    def __init__(self, type):
        self.url = "https://api.telegram.org/bot{0}/{1}".format(config.API, type)

    def fetch(self, append=""):
        session = requests.Session()  # Make this part of init and global
        response = session.get(self.url + append)
        return json.loads(response.text)

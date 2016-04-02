class TelegramRequest:

    def __init__(self, type):
        import config
        self.url = "https://api.telegram.org/bot{0}/{1}".format(config.API, type)

    def fetch(self, append=""):
        import requests
        import json
        session = requests.Session()
        response = session.get(self.url + append)
        return json.loads(response.text)

    #is append="" the best solution here?
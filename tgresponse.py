class TelegramResponse:

    def __init__(self, type):
        import config
        self.url = "https://api.telegram.org/bot{0}/{1}".format(config.API, type)

    def sendMessage(self, content):
        import requests
        session = requests.Session()  # Make this part of init and global
        response = session.post(
            url=self.url,
            data=content).json()
        return response

    def sendMessageProcess(self):


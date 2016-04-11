import json


class ConfigUtils:
    def __init__(self, filename='config.ini'):
        import configparser
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        self.token = self.config['MAIN_BOT']['token']
        self.plugins = self.config['MAIN_BOT']['plugins'].split(',')

    def write_config(self):
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)


def post_post(session, content):
    response = session.post(**content)
    return response


def fetch(session, url):  # Grabs from url and parses as json. note2self, don't make it parse json by default
    response = session.get(url)
    return json.loads(response.text)

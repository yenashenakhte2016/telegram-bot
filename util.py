import requests
import time
import shutil
import re


class ConfigUtils:
    def __init__(self, filename='config.ini', bot_name='MAIN_BOT'):
        import configparser
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        self.token = self.config[bot_name]['token']
        self.plugins = self.config[bot_name]['plugins'].split(',')
        self.plugin_path = self.config[bot_name]['plugin_path']

    def write_config(self):
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)


def post_post(content, session=requests):
    response = session.post(**content)
    return response


def fetch(url, session=requests):  # Grabs from url and parses as json. note2self, don't make it parse json by default
    try:
        response = session.get(url, timeout=3)
        return response
    except requests.exceptions.ReadTimeout:
        return 'Request timed out :('
    except requests.exceptions.ConnectionError:
        return 'Unable to connect :('


def fetch_file(url, file_path, session=requests):
    response = session.get(url, stream=True)
    with open(file_path, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    return file_path


def timeout(site):
    print('Trying to connect to google.com...')
    response = fetch('www.google.com')
    if response == 200:
        print("{} seems to be down :(\nTrying again in 5 seconds...".format(site))
    else:
        print('{} - trying again in 5 seconds...'.format(response))
    time.sleep(5)


def clean_message(message_text, bot_name):
    username = "@{}".format(bot_name['result']['username'])
    text = message_text
    name_match = re.search('^[!#@/]([^ ]*)({})'.format(username), text)
    if name_match:
        return text.replace(text[:name_match.end(0)], text[:name_match.end(0) - len(username)])
    else:
        return text


def name_file(file_id, file_name):
    if file_name:
        match = re.findall('(\.[0-9a-zA-Z]+$)', file_name)
        return file_id + match[0]
    else:
        return str(file_id)

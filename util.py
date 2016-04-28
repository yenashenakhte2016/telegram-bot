import requests
import shutil
import re
import os


class ConfigUtils:
    def __init__(self, filename='config.ini', bot_name='MAIN_BOT'):
        import configparser
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        self.token = self.config[bot_name]['token']
        self.plugins = self.config[bot_name]['plugins'].split(',')
        self.plugin_path = self.config[bot_name]['plugin_path']
        self.sleep = float(self.config[bot_name]['sleep'])

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
    if not os.path.exists('data/files'):
        os.makedirs('data/files')
    with open(file_path, 'wb') as out_file:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, out_file)
    return file_path


def clean_message(text, bot_name):
    username = "@{}".format(bot_name)
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

import sqlite3
import requests
import time


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

'''
class Databases:  # Soon
    def __init__(self):
'''


def post_post(session, content):
    response = session.post(**content)
    return response


def fetch(session, url):  # Grabs from url and parses as json. note2self, don't make it parse json by default
    try:
        response = session.get(url, timeout=3)
        return response
    except requests.exceptions.ReadTimeout:
        return 'Request timed out :('
    except requests.exceptions.ConnectionError:
        return 'Unable to connect :('


def timeout(site):
    print('Trying to connect to google.com...')
    response = fetch(requests, 'https://www.google.com')
    if response == 200:
        print("{} seems to be down :(\nTrying again in 5 seconds...".format(site))
    else:
        print('{} - trying again in 5 seconds...'.format(response))
    time.sleep(5)

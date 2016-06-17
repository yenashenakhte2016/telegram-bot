# -*- coding: utf-8 -*-


from subprocess import Popen, PIPE


def main(tg):
    if str(tg.chat_data['from']['id']) in tg.config['BOT_CONFIG']['admins']:
        arg = tg.message['match'].replace(u"\u2014", '--')
        try:
            command = Popen(arg.split(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            response, error = command.communicate()
            if type(response) is bytes:
                response = response.decode('UTF-8')
            if type(error) is bytes:
                error = error.decode('UTF-8')
            result = response or error
        except BaseException as error:
            result = error
        tg.send_message("<code>{}</code>".format(result))


parameters = {
    'name': "Shell",
    'short_description': "Run shell commands from the bot",
    'permissions': "11",
    'hidden': True
}

arguments = {
    'text': [
        "^/shell (.*)"
    ]
}

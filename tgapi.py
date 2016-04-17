import util


class PluginHelper:
    def __init__(self, message, misc):
        self.msg = message
        self.misc = misc

    def send_chat_action(self, action, chat_id=0):
        if type(chat_id) != int or chat_id is 0:
            chat_id = self.msg['chat']['id']
        package = dict()
        package['data'] = {
            'chat_id': chat_id,
            'action': action
        }
        send_method(self.misc, package, 'sendChatAction')

    def send_message(self, text, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'text': text,
            'parse_mode': "HTML",
            'reply_to_message_id': self.msg['message_id']
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        send_method(self.misc, package, 'sendMessage')

    def send_photo(self, photo, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'reply_to_message_id': self.msg['message_id']
        }
        package['files'] = photo
        for k, v in kwargs.items():
            package['data'][k] = v
        send_method(self.misc, package, 'sendPhoto')


def send_method(misc, returned_value, method, base_url='{0}{1}{2}'):  # If dict is returned
    package = {'url': base_url.format(misc['base_url'], misc['token'], method)}
    for k, v in returned_value.items():
        package[k] = v
    util.post_post(package, misc['session'])


def get_me(misc):  # getMe
    url = "{}{}getMe".format(misc['base_url'], misc['token'])
    response = util.fetch(url, misc['session'])
    parsed_response = response.json()
    return parsed_response


def download_file(misc, document_object):
    package = dict()
    package['url'] = "{}{}getFile".format(misc['base_url'], misc['token'])
    package['data'] = {'file_id': document_object['file_id']}
    response = util.post_post(package, misc['session']).json()
    if response['ok']:
        url = "{}/file/{}{}".format(misc['base_url'], misc['token'], response['result']['file_path'])
        try:
            name = document_object['file_name']
        except KeyError:
            name = None
        file_name = util.name_file(document_object['file_id'], name)
        response = util.fetch_file(url, 'data/files/{}'.format(file_name),misc['session'])
        return response
    else:
        return response['error_code']
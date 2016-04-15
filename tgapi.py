import util


def send_message(misc, msg, content):  # Send a message with default parameters
    package = dict()
    package['url'] = "{}{}sendMessage".format(misc['base_url'], misc['token'])
    package['data'] = {  # Default return
        'chat_id': msg['chat']['id'],
        'text': None,
        'parse_mode': "HTML",
        'reply_to_message_id': msg['message_id']
    }
    package['data']['text'] = content['text']
    util.post_post(misc['session'], package)


def get_me(misc):  # getMe
    url = "{}{}getMe".format(misc['base_url'], misc['token'])
    response = util.fetch(misc['session'], url)
    parsed_response = response.json()
    return parsed_response


def send_method(misc, msg, returned_value):  # If dict is returned
    method = returned_value['method']
    del returned_value['method']
    package = {'url': "{}{}{}".format(misc['base_url'], misc['token'], method)}
    for k, v in returned_value.items():
        package[k] = v
    try:
        if 'chat_id' not in package['data']:  # Makes sure a chat_id is provided
            package['data'] = {'chat_id': msg['chat']['id']}
    except KeyError:
        package['data'] = dict()
        package['data'] = {'chat_id': msg['chat']['id']}
    util.post_post(misc['session'], package)


def download_file(misc, msg):
    package = dict()
    package['url'] = "{}{}getFile".format(misc['base_url'], misc['token'])
    package['data'] = {'file_id': msg['document']['file_id']}
    response = util.post_post(misc['session'], package).json()
    if response['ok']:
        url = "{}/file/{}{}".format(misc['base_url'], misc['token'], response['result']['file_path'])
        try:
            name = msg['document']['file_name']
        except KeyError:
            name = None
        file_name = util.name_file(msg['document']['file_id'], name)
        response = util.fetch_file(misc['session'], url, 'data/files/{}'.format(file_name))
        return response
    else:
        return response['error_code']

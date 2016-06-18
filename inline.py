# -*- coding: utf-8 -*-


import json
import time

import _mysql_exceptions
import certifi
import urllib3


class TelegramInlineAPI:
    def __init__(self, database, get_me, plugin_name, config, inline_query):
        self.database = database
        self.cursor = self.database.cursor()
        self.get_me = get_me
        self.plugin_name = plugin_name
        self.config = config
        self.inline_query = inline_query
        self.http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        self.token = self.config['BOT_CONFIG']['token']
        self.message = self.callback_query = None
        self.input_location_message_content = input_location_message_content
        self.input_venue_message_content = input_venue_message_content
        self.input_contact_message_content = input_contact_message_content

    def answer_inline_query(self, results, **kwargs):
        url = "https://api.telegram.org/bot{}/answerInlineQuery".format(self.token)
        if type(results) is not list:
            results = [results]
        package = {
            'inline_query_id': self.inline_query['id'],
            'results': json.dumps(results)
        }
        package.update(kwargs)
        post = self.http.request_encode_body('POST', url, fields=package).data
        return json.loads(post.decode('UTF-8'))

    def inline_query_result_article(self, title, input_message_content, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': 'article',
            'id': '{}{}{}'.format(self.inline_query['id'], self.plugin_name, time.time()),
            'title': title,
            'input_message_content': input_message_content
        }
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_photo(self, photo, thumb_url=None, cached=False, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': "photo",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time())
        }
        if cached:
            package['photo_file_id'] = photo
        else:
            package['photo_url'] = photo
            package['thumb_url'] = thumb_url or photo
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_gif(self, gif, thumb_url=None, cached=False, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': "gif",
            'id': '{}{}{}'.format(self.inline_query['id'], self.plugin_name, time.time())
        }
        if cached:
            package['gif_file_id'] = gif
        else:
            package['gif_url'] = gif
            package['thumb_url'] = thumb_url or gif
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_mpeg4_gif(self, mpeg4, thumb_url=None, cached=False, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': "mpeg4_gif",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time())
        }
        if cached:
            package['mpeg4_file_id'] = mpeg4
        else:
            package['mpeg4_url'] = mpeg4
            package['thumb_url'] = thumb_url
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_sticker(self, sticker_file_id, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': "sticker",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time()),
            'sticker_file_id': sticker_file_id
        }
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_video(self, title, video, mime_type=None, thumb_url=None, cached=False, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': "video",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time()),
            'title': title
        }
        if cached:
            package['video_file_id'] = video
        else:
            package['video_url'] = video,
            package['mime_type'] = mime_type,
            package['thumb_url'] = thumb_url
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_audio(self, audio, title, cached=False, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': "audio",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time()),
            'title': title
        }
        if cached:
            package['audio_file_id'] = audio
        else:
            package['audio_url'] = audio
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_voice(self, voice, title, cached=False, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': 'voice',
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time()),
            'title': title
        }
        if cached:
            package['voice_file_id'] = voice
        else:
            package['voice_url'] = voice,
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_result_document(self, title, document, mime_type=None, cached=False, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': "document",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time()),
            'title': title
        }
        if cached:
            package['document_file_id'] = document
        else:
            package['document_url'] = document
            document['mime_type'] = mime_type
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_location(self, latitude, longitude, title, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': 'location',
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time()),
            'latitude': latitude,
            'longitude': longitude,
            'title': title
        }
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_result_venue(self, latitude, longitude, title, address, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': 'venue',
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time()),
            'latitude': latitude,
            'longitude': longitude,
            'title': title,
            'address': address
        }
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_query_result_contact(self, phone_number, first_name, **kwargs):
        cursor = self.database.cursor()
        package = {
            'type': "contact",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name, time.time()),
            'phone_number': phone_number,
            'first_name': first_name
        }
        package.update(kwargs)
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)", (self.plugin_name, package['id']))
        cursor.close()
        return package

    def inline_keyboard_markup(self, list_of_list_of_buttons, plugin_data=None):
        cursor = self.database.cursor()
        plugin_data = json.dumps(plugin_data)
        for button_list in list_of_list_of_buttons:
            for button in button_list:
                if 'text' not in button:
                    return "Error: Text not found in button object"
                if 'callback_data' in button:
                    try:
                        cursor.execute("INSERT INTO callback_queries VALUES(%s, %s, %s)",
                                            (self.plugin_name, button['callback_data'], plugin_data))
                    except _mysql_exceptions.IntegrityError:
                        continue
        package = {
            'inline_keyboard': list_of_list_of_buttons
        }
        cursor.close()
        return package

    def input_text_message_content(self, message_text, parse_mode=0, disable_web_page_preview=False):
        if parse_mode == 0:
            parse_mode = self.config['BOT_CONFIG']['default_parse_mode']
        return {'message_text': message_text, 'parse_mode': parse_mode,
                'disable_web_page_preview': disable_web_page_preview}


def input_location_message_content(latitude, longitude):
    return {'latitude': latitude, 'longitude': longitude}


def input_venue_message_content(latitude, longitude, title, address, foursquare_id=None):
    package = {
        'latitude': latitude,
        'longitude': longitude,
        'title': title,
        'address': address
    }
    if foursquare_id:
        package['foursquare_id'] = foursquare_id
    return package


def input_contact_message_content(phone_number, first_name, last_name=None):
    package = {
        'phone_number': phone_number,
        'first_name': first_name
    }
    if last_name:
        package['last_name'] = last_name
    return package

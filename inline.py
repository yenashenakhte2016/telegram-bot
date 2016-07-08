# -*- coding: utf-8 -*-

import json
import time
import uuid

import MySQLdb
import _mysql_exceptions


class TelegramInlineAPI:
    def __init__(self, database, get_me, plugin_name, config, http,
                 inline_query):
        self.database = database
        self.cursor = self.database.cursor()
        self.get_me = get_me
        self.plugin_name = plugin_name
        self.config = config
        self.inline_query = inline_query
        self.http = http
        self.token = self.config['BOT_CONFIG']['token']
        self.message = self.callback_query = None
        self.input_location_message_content = input_location_message_content
        self.input_venue_message_content = input_venue_message_content
        self.input_contact_message_content = input_contact_message_content

    def answer_inline_query(self, results, **kwargs):
        url = "https://api.telegram.org/bot{}/answerInlineQuery".format(
            self.token)
        if type(results) is not list:
            results = [results]
        package = {
            'inline_query_id': self.inline_query['id'],
            'results': json.dumps(results)
        }
        package.update(kwargs)
        if 'switch_pm_parameter' in kwargs:
            database = MySQLdb.connect(**self.config['DATABASE'])
            parameter = kwargs['switch_pm_parameter']
            cursor = database.cursor()
            try:
                cursor.execute("INSERT INTO pm_parameters VALUES(%s, %s);",
                               (self.plugin_name, parameter))
                database.commit()
            except _mysql_exceptions.IntegrityError:
                pass
            database.close()
        post = self.http.request_encode_body('POST', url, fields=package).data
        return json.loads(post.decode('UTF-8'))

    def inline_query_result_article(self, title, input_message_content,
                                    **kwargs):
        package = {
            'type': 'article',
            'id': str(uuid.uuid4()),
            'title': title,
            'input_message_content': input_message_content
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_photo(self,
                                  photo,
                                  thumb_url=None,
                                  cached=False,
                                  **kwargs):
        package = {
            'type': "photo",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name,
                                  time.time())
        }
        if cached:
            package['photo_file_id'] = photo
        else:
            package['photo_url'] = photo
            package['thumb_url'] = thumb_url or photo
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_gif(self,
                                gif,
                                thumb_url=None,
                                cached=False,
                                **kwargs):
        package = {'type': "gif", 'id': str(uuid.uuid4())}
        if cached:
            package['gif_file_id'] = gif
        else:
            package['gif_url'] = gif
            package['thumb_url'] = thumb_url or gif
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_mpeg4_gif(self,
                                      mpeg4,
                                      thumb_url=None,
                                      cached=False,
                                      **kwargs):
        package = {
            'type': "mpeg4_gif",
            'id': "{}{}{}".format(self.inline_query['id'], self.plugin_name,
                                  time.time())
        }
        if cached:
            package['mpeg4_file_id'] = mpeg4
        else:
            package['mpeg4_url'] = mpeg4
            package['thumb_url'] = thumb_url
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_sticker(self, sticker_file_id, **kwargs):
        package = {
            'type': "sticker",
            'id': str(uuid.uuid4()),
            'sticker_file_id': sticker_file_id
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_video(self,
                                  title,
                                  video,
                                  mime_type=None,
                                  thumb_url=None,
                                  cached=False,
                                  **kwargs):
        package = {'type': "video", 'id': str(uuid.uuid4()), 'title': title}
        if cached:
            package['video_file_id'] = video
        else:
            package['video_url'] = video,
            package['mime_type'] = mime_type,
            package['thumb_url'] = thumb_url
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_audio(self, audio, title, cached=False, **kwargs):
        package = {'type': "audio", 'id': str(uuid.uuid4()), 'title': title}
        if cached:
            package['audio_file_id'] = audio
        else:
            package['audio_url'] = audio
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_voice(self, voice, title, cached=False, **kwargs):
        package = {'type': 'voice', 'id': str(uuid.uuid4()), 'title': title}
        if cached:
            package['voice_file_id'] = voice
        else:
            package['voice_url'] = voice,
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_result_document(self,
                               title,
                               document,
                               mime_type=None,
                               cached=False,
                               **kwargs):
        package = {'type': "document", 'id': str(uuid.uuid4()), 'title': title}
        if cached:
            package['document_file_id'] = document
        else:
            package['document_url'] = document
            document['mime_type'] = mime_type
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_location(self, latitude, longitude, title,
                                     **kwargs):
        package = {
            'type': 'location',
            'id': str(uuid.uuid4()),
            'latitude': latitude,
            'longitude': longitude,
            'title': title
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_result_venue(self, latitude, longitude, title, address,
                            **kwargs):
        package = {
            'type': 'venue',
            'id': str(uuid.uuid4()),
            'latitude': latitude,
            'longitude': longitude,
            'title': title,
            'address': address
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_contact(self, phone_number, first_name, **kwargs):
        package = {
            'type': "contact",
            'id': str(uuid.uuid4()),
            'phone_number': phone_number,
            'first_name': first_name
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_keyboard_markup(self,
                               list_of_list_of_buttons,
                               plugin_data=None):
        cursor = self.database.cursor()
        plugin_data = json.dumps(plugin_data)
        for button_list in list_of_list_of_buttons:
            for button in button_list:
                if 'text' not in button:
                    return "Error: Text not found in button object"
                if 'callback_data' in button:
                    try:
                        cursor.execute(
                            "INSERT INTO callback_queries VALUES(%s, %s, %s)",
                            (self.plugin_name, button['callback_data'],
                             plugin_data))
                    except _mysql_exceptions.IntegrityError:
                        continue
        package = {'inline_keyboard': list_of_list_of_buttons}
        cursor.close()
        return package

    def input_text_message_content(self,
                                   message_text,
                                   parse_mode=0,
                                   disable_web_page_preview=False):
        if parse_mode == 0:
            parse_mode = self.config['MESSAGE_OPTIONS']['PARSE_MODE']
        return {'message_text': message_text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_web_page_preview}

    def add_inline_query(self, query_id):
        database = MySQLdb.connect(**self.config['DATABASE'])
        cursor = database.cursor()
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)",
                       (self.plugin_name, query_id))
        cursor.close()
        database.commit()
        database.close()

    def pm_parameter(self, parameter):
        database = MySQLdb.connect(**self.config['DATABASE'])
        cursor = database.cursor()
        try:
            cursor.execute("INSERT INTO pm_parameters VALUES(%s, %s);",
                           (self.plugin_name, parameter))
        except _mysql_exceptions.IntegrityError:
            pass
        url = "https://telegram.me/{}?start={}"
        bot_name = self.get_me['result']['username']
        cursor.close()
        database.commit()
        database.close()
        return url.format(bot_name, parameter)


def input_location_message_content(latitude, longitude):
    return {'latitude': latitude, 'longitude': longitude}


def input_venue_message_content(latitude,
                                longitude,
                                title,
                                address,
                                foursquare_id=None):
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
    package = {'phone_number': phone_number, 'first_name': first_name}
    if last_name:
        package['last_name'] = last_name
    return package


class InlineCallbackQuery:
    def __init__(self, database, config, http, callback_query):
        self.config = config
        self.token = self.config['BOT_CONFIG']['token']
        self.http = http
        self.callback_query = callback_query
        self.database = database
        self.message = self.inline_query = None

    def answer_callback_query(self,
                              text=None,
                              callback_query_id=None,
                              show_alert=False):
        arguments = locals()
        del arguments['self']
        if not callback_query_id:
            try:
                arguments.update(
                    {'callback_query_id': int(self.callback_query['id'])})
            except KeyError:
                return "Callback query ID not found!"
        if text is None:
            del arguments['text']
        url = "https://api.telegram.org/bot{}/{}".format(self.token,
                                                         'answerCallbackQuery')
        post = self.http.request_encode_body('POST',
                                             url, fields=arguments).data
        return json.loads(post.decode('UTF-8'))

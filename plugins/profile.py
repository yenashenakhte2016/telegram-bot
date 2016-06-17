# -*- coding: utf-8 -*-


import json
import os

import _mysql_exceptions

user_id = None
entries = None
try:
    JSONDecodeError = json.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError


def main(tg):
    global user_id, entries
    if not os.path.exists('data/profile'):
        os.makedirs('data/profile')
    tg.send_chat_action('typing')
    user_id = tg.message['reply_to_message']['from']['id'] if 'reply_to_message' in tg.message else \
        tg.message['from']['id']
    with open('data/entries.json', 'r') as json_file:
        entries = json.load(json_file)
    if tg.message['matched_regex'] == arguments['text'][0]:
        return_profile(tg)
    elif tg.message['matched_regex'] == arguments['text'][1]:
        if tg.message['match'][0] == 'delete' or tg.message['match'][0] == 'del':
            delete_entry(tg)
        else:
            add_entry(tg)


def return_profile(tg):
    global user_id
    tg.send_chat_action("Typing")
    first_name = tg.message['reply_to_message']['from']['first_name'] if 'reply_to_message' in tg.message else \
        tg.message['from']['first_name']
    try:
        with open('data/profile/{}.json'.format(user_id)) as json_file:
            profile = json.load(json_file)
    except (JSONDecodeError, FileNotFoundError):
        profile = dict()
    message = "<b>{}'s Profile</b>".format(first_name.title())
    keyboard = make_keyboard(profile)
    stats = get_stats(tg)
    if stats:
        message += "\n<b>Total Messages:</b> {:,} ({})".format(stats['user_total'], stats['percentage'])
    playing = last_fm(tg.http, profile)
    if playing:
        message += u"\n\U0001F3B6 <b>Currently listening to:</b>\n{} - {}".format(playing['song'], playing['artist'])
    if len(message.split('\n')) == 1 and not keyboard:
        message = "\nYour profile seems empty. You can add entries using:\n<code>/profile website username</code>"
    tg.send_message(message, reply_markup=tg.inline_keyboard_markup(keyboard), parse_mode="HTML")


def make_keyboard(profile):
    remaining = len(profile)
    keyboard = []
    for name, username in profile.items():
        row_length = 3 if remaining >= 3 or remaining == 1 else 2
        pretty_name = entries[name]['pretty_name']
        url = entries[name]['url'].format(username)
        button = {'text': pretty_name, 'url': url}
        if keyboard and len(keyboard[-1]) < row_length:
            keyboard[-1].append(button)
        else:
            keyboard.append([button])
        remaining -= 1
    return keyboard


def last_fm(http, profile):
    if 'lastfm' in profile:
        from plugins import lastfm
        last_track = lastfm.get_recently_played(http, profile['lastfm'], 1)
        if last_track and last_track[0]['now_playing']:
            last_track = last_track.pop()
            return last_track


def get_stats(tg):
    try:
        from plugins import chat_stats
    except AttributeError:
        return
    chat_id = tg.message['chat']['id']
    try:
        tg.database.query("SELECT COUNT(*) FROM `{}stats`;".format(chat_id))
    except _mysql_exceptions.ProgrammingError:
        return
    query = tg.database.store_result()
    chat_total = query.fetch_row()
    if chat_total[0][0] < 100:
        return
    tg.database.query("SELECT COUNT(*) FROM `{}stats` WHERE user_id={}".format(chat_id, user_id))
    query = tg.database.store_result()
    user_total = query.fetch_row()
    percentage = "{:.2%}".format(user_total[0][0] / chat_total[0][0])
    return {'user_total': user_total[0][0], 'percentage': percentage}


def add_entry(tg):
    try:
        with open('data/profile/{}.json'.format(user_id)) as file:
            profile = json.load(file)
    except (JSONDecodeError, FileNotFoundError):
        open('data/profile/{}.json'.format(user_id), 'w')
        profile = dict()
    site = tg.message['match'][0]
    user_name = tg.message['match'][1]
    for key, value in entries.items():
        if site.lower() == key or site.lower() in value['aliases']:
            if key in profile:
                message = "Updated your {}!".format(value['pretty_name'])
            else:
                message = "Successfully set your {}!".format(value['pretty_name'])
            profile.update({key: user_name})
            with open('data/profile/{}.json'.format(user_id), 'w') as file:
                json.dump(profile, file, sort_keys=True, indent=4)
            tg.send_message(message)
            return
    else:
        tg.send_message("This entry doesn't seem to be an option")


def delete_entry(tg):
    try:
        with open('data/profile/{}.json'.format(user_id)) as file:
            profile = json.load(file)
    except (JSONDecodeError, FileNotFoundError):
        tg.send_message(
            "You don't seem to have anything to delete :(\nAdd entries using <code>/profile website username</code>")
        return
    site = tg.message['match'][1].lower()
    for key, value in entries.items():
        if site.lower() == key or site.lower() in value['aliases']:
            try:
                del profile[key]
            except KeyError:
                tg.send_message("You haven't seemed to link a {}".format(value['pretty_name']))
                return
            tg.send_message("Successfully removed {}".format(value['pretty_name']))
            with open('data/profile/{}.json'.format(user_id), 'w') as file:
                json.dump(profile, file, sort_keys=True, indent=4)
            return
    tg.send_message("Invalid field")


def list_of_options():
    fields = list()
    with open('data/entries.json', 'r') as json_file:
        sites = json.load(json_file)
    for site in sites.values():
        fields.append(site['pretty_name'])
    return ", ".join(fields)


parameters = {
    'name': "Profile",
    'short_description': "Display information about yourself",
    'long_description': "The profile plugin allows you to share various details about yourself. You can add a field "
                        "using <code>/profile website username</code>\n\n<b>List of fields:</b>\n{}".format(
                                                                                                list_of_options()),
    'permissions': True
}

arguments = {
    'text': [
        "^/profile$",
        "^/profile (.*) (.*)$"
    ]
}
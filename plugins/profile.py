import json
import os

user_id = None
entries = None
try:
    JSONDecodeError = json.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError


def main(tg):
    global user_id, entries
    if not os.path.exists('data/me'):
        os.makedirs('data/me')
    tg.send_chat_action('typing')
    user_id = tg.message['from']['id']
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
    sent_message = tg.send_message("Loading...")
    if 'reply_to_message' in tg.message:
        user_id = tg.message['reply_to_message']['from']['id']
        first_name = tg.message['reply_to_message']['from']['first_name']
        error = "This profile seems empty. You can add entries using:\n<code>/me field username</code>"
    else:
        first_name = tg.message['from']['first_name']
        error = "Your profile seems empty. Add entries using <code>/me field username</code>"
    try:
        with open('data/me/{}.json'.format(user_id)) as json_file:
            profile = json.load(json_file)
    except (JSONDecodeError, FileNotFoundError):
        tg.edit_message_text(error, message_id=sent_message['result']['message_id'])
        return
    keyboard = []
    remaining = len(profile)
    message = "{}'s Profile:".format(first_name.title()) if remaining else error
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
    inline_keyboard = tg.inline_keyboard_markup(keyboard)
    if 'lastfm' in profile:
        from plugins import lastfm
        last_track = lastfm.get_recently_played(profile['lastfm'], 1)
        if last_track and last_track[0]['now_playing']:
            last_track = last_track.pop()
            message += "\n🎶 {} - {} 🎶".format(last_track['song'], last_track['artist'])
    tg.edit_message_text(message, message_id=sent_message['result']['message_id'], reply_markup=inline_keyboard,
                         parse_mode="HTML")


def add_entry(tg):
    try:
        with open('data/me/{}.json'.format(user_id)) as file:
            profile = json.load(file)
    except (JSONDecodeError, FileNotFoundError):
        open('data/me/{}.json'.format(user_id), 'w')
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
            with open('data/me/{}.json'.format(user_id), 'w') as file:
                json.dump(profile, file, sort_keys=True, indent=4)
            tg.send_message(message)
            return
    else:
        tg.send_message("This entry doesn't seem to be an option")


def delete_entry(tg):
    try:
        with open('data/me/{}.json'.format(user_id)) as file:
            profile = json.load(file)
    except (JSONDecodeError, FileNotFoundError):
        tg.send_message(
            "You don't seem to have anything to delete :(\nAdd entries using <code>/me website username</code>")
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
            with open('data/me/{}.json'.format(user_id), 'w') as file:
                json.dump(profile, file, sort_keys=True, indent=4)
            return
    tg.send_message("Invalid field")


plugin_parameters = {
    'name': "Profile",
    'desc': "Display information about yourself",
    'extended_desc': "The profile plugin allows you to share various details about yourself. You can add a field using"
                     "/me website username. Plugins such as LastFM will integrate with this for a seamless experience.",
    'permissions': True
}

arguments = {
    'text': [
        "^/me$",
        "^/me (.*) (.*)$"
    ]
}

#dont look at this
def main(msg, text_file):
    log = "[%s(%s)] - " % (msg['chat']['type'].title(), msg['chat']['id'])
    log += "%s" % msg['from']['first_name']
    if 'last_name' in msg['from']:
        log += " %s" % msg['from']['last_name']
    if 'username' in msg['from']:
        log += "(@%s)" % msg['from']['username']
    if 'text' in msg:
        log += " - '%s'" % msg['text']
    elif 'audio' in msg:
        log += " - Audio Message"
    elif 'document' in msg:
        log += " - Document"
    elif 'photo' in msg:
        log += " - Photo"
        if 'caption' in msg:
            log += ": %s" % msg['caption']
    elif 'sticker' in msg:
        log += " - Sticker"
    elif 'video' in msg:
        log += ' - Video'
        if 'caption' in msg:
            log += ": %s" % msg['caption']
    elif 'voice' in msg:
        log += ' - Voice'
    elif 'contact' in msg:
        log += ' - Contact'
    elif 'location' in msg:
        log += ' - Locaton'
    elif 'new_chat_participant' in msg:
        log += " added %s" % msg['new_chat_participant']['first_name']
        if 'last_name' in msg['new_chat_participant']:
            log += " %s" % msg['new_chat_participant']['last_name']
        if 'username' in msg['new_chat_participant']:
            log += "(@%s)" % msg['new_chat_participant']['username']
    elif 'left_chat_participant' in msg:
        if msg['left_chat_participant']['id'] == msg['from']['id']:
            log += " has left"
        else:
            log += " removed %s" % msg['left_chat_participant']['first_name']
            if 'last_name' in msg['left_chat_participant']:
                log += " %s" % msg['left_chat_participant']['last_name']
            if 'username' in msg['left_chat_participant']:
                log += "(@%s)" % msg['left_chat_participant']['username']
    elif 'new_chat_title' in msg:
        log += " has changed the name to '%s'" % msg['new_chat_title']
    elif 'new_chat_photo' in msg:
        log += " has changed the chat photo"
    elif 'delete_chat_photo' in msg:
        log += " has deleted the chat photo"
    elif 'group_chat_created' in msg or 'supergroup_chat_created' in msg:
        log += " has created the chat %s" % msg['chat']['title']
    elif 'channel_chat_created' in msg:
        log += " has created the channel %s" % msg['chat']['title']
    elif 'migrate_to_chat_id' in msg:
        log += " %s has migrated to ID %s" % (msg['chat']['title'],msg['migrate_to_chat_id'])
    text_file.write("%s\n" % log)
    print(log)

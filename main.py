import config
import json
import requests
import re
import sys
import tgrequest

getUpdateObj = tgrequest.TelegramRequest("getUpdates")
getMeObj = tgrequest.TelegramRequest("getMe")


plugins = {}
update_id = 0
run = True
baseurl = "https://api.telegram.org/bot%s" % config.API
text_file = open("output.txt", "a", encoding="utf-8")
session = requests.Session()

print("####BOT####")
getMe = getMeObj.fetch()
if getMe['ok']:
    print("{0}[{1}]".format(getMe['result']['first_name'], getMe['result']['username']))
    print("ID: {0}".format(getMe['result']['id']))
else:
    print("[✖] There seems to be something wrong with your api key in config.py :(")
    sys.exit(0)
print("####ADMINS####")
for admin in config.admins:
    print("[✓] {0}".format(str(admin)))
print("####PLUGINS####")
for plugin in config.plugins:
    sys.path.append("./plugins")
    plugins[plugin] = __import__(plugin)
    if plugins[plugin].main and plugins[plugin].regex and plugins[plugin].pluginname:
        print("[✓] {0}".format(plugins[plugin].pluginname))
    else:
        print("[✖] {0}".format(plugin))
        del plugins[plugin]


def sendmessage(sendmessageObject):
    response = session.post(
        url=baseurl + "/sendMessage",
        data=sendmessageObject
    ).json()
    return response


def sendmessagedefault(chatid, text, replyid):
    response = session.post(
        url=baseurl + "/sendMessage",
        data={'chat_id': chatid, 'text': text, 'reply_to_message_id': replyid, 'parse_mode': "Markdown"}
    ).json()
    return response


def checktrigger(msg):
    for x in plugins:
        for regex in plugins[x].regex:
            msg['rawtext'] = msg['text']
            msg['text'] = msg['text'].replace("@{0}".format(botinfo['result']['username']), "")
            match = re.search(regex, msg['text'])
            if match is not None:
                rval = plugins[x].main(msg)
                if isinstance(rval, str):
                    sendmessagedefault(msg['chat']['id'], rval, msg['message_id'])
                elif isinstance(rval, dict):
                    sendmessage(rval)
                return


while run:
    getUpdate = getUpdateObj.fetch("?offset={0}".format(update_id))
    for i in range(len(getUpdate['result'])):
        msg = getUpdate['result'][i]['message']
        if 'text' in msg:
            checktrigger(msg)
        if i == len(getUpdate['result']) - 1:
            update_id = getUpdate['result'][i]['update_id'] + 1


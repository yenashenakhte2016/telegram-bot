import config
import log
import json
import requests
import re
plugins = {}
update_id = 0
run = True
baseurl = "https://api.telegram.org/bot%s" % config.API
text_file = open("output.txt", "a")

print("####ADMINS####")
for admin in config.admins:
    print(admin)
print("####PLUGINS####")
for plugin in config.plugins:
    plugins[plugin] = __import__(plugin)
    print("Imported %s" % plugins[plugin].pluginname)

def shutdown():
    run = False
    text_file.close()
    print("Shutting down for now :(")

def sendMessage(sendMessageObject):
    response = requests.post(
    url= baseurl + "/sendMessage",
    data=sendMessageObject
).json()
    return response

def sendMessageDefault(chatid, text, replyid):
    response = requests.post(
    url= baseurl + "/sendMessage",
    data={'chat_id': chatid, 'text': text, 'reply_to_message_id': replyid, 'parse_mode': "Markdown"}
).json()
    return response

while run:
    update = requests.get(baseurl + "/getUpdates?offset=%s" % update_id)
    getupdate = json.loads(update.text)
    for i in range(len(getupdate['result'])):
        msg = getupdate['result'][i]['message']
        log.main(msg, text_file)
        if 'text' in msg:
            for x in plugins:
                for regex in plugins[x].regex:
                    trigger = re.search(regex, msg['text'])
                    if trigger != None:
                        sendMessageDefault(msg['chat']['id'],plugins[x].main(msg),msg['message_id'])
                        break
        if i == len(getupdate['result']) - 1:
            update_id = getupdate['result'][i]['update_id'] + 1

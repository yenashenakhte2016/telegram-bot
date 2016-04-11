# Hitagibot

Hitagibot is a plugin based Telegram bot written in python 3 and licensed under the GNU Affero General Public License V3. Currently functionality is very barebones. The bot focuses on providing a lightweight modular environment for bot creation.

###Setup
```bash
git clone https://github.com/TopBakuhatsu/nanobotpython.git
```
In config.py add your bots API key and add your ID to admins.
```python
API = "131440568:Gosaahfeyvla4Jvkt5Cirybksingh1pu42I" #Add your key here (This one won't work)
admins = [
123456789, #Add admin(s) here
]
```

After that you can run the bot!
```bash
cd hitagibot
python3 main.py
```
###Plugins
Plugins are simple to make. Every plugin will need: 

**`plugin_info`**

Here is where you should place plugin information. This includes a pretty name, short description, and list of commands.

**`regex`**

regex should be a list containing all "triggers" for your plugin. Use [regex101](https://regex101.com/) to create and test them.

**`main`** 

main will always be the function where you recieve the [msg](https://core.telegram.org/bots/api#message) object and
return your bots reply. Returning only a string is the equivalent of a sendMessage object which replies with HTML
parsing. While dictionaries allow you to modify api methods and parameters. Example:

```python
def main(msg):
    photo = {'photo':open('example.png', 'rb')}
    example_dict = {
        'method': 'sendPhoto',
        'data': {
            'caption': 'Example of sendPhoto',
            'reply_to_message_id': msg['message_id']
        },
        'file': photo  #
    }
    return example_dict
```

###What can it do?
| Method               | Status |
| -------------------- | ------ |
| getMe                | ✔      |
| sendMessage          | ✔      |
| forwardMessage       | ✔      |
| sendPhoto            | ✔      |
| sendAudio            | ✔      |
| sendDocument         | ✔      |
| sendSticker          | ✔      |
| sendVideo            | ✔      |
| sendVoice            | ✔      |
| sendLocation         | ✔      |
| sendChatActions      | ✔      |
| getUpdates           | ✔      |
| getUserProfilePhotos | ✖      |
| getFile              | ✖      |
| setWebhook           | ✖      |
| answerInlineQuery    | ✖      |

###To Do
- Support full telegram API
- Better config
- Async
- Database

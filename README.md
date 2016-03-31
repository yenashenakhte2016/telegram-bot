# Hitagibot

Hitagibot is a plugin based Telegram bot written in python 3 and licensed under the GNU Affero General Public License V3. Currently functionality is very barebones (ie. inline support is non-existant).

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

**`pluginname`**

pluginname should be a string which contains exactly whats implied. Note that it is only temporary and will be replaced with something more comprehensive with the release of a help plugin.

**`regex`**

regex should be a list containing all "triggers" for your plugin. Use [regex101](https://regex101.com/) to create and test them.

**`main`** 

main should always be the function where you recieve the [msg](https://core.telegram.org/bots/api#message) object and return your bots reply. Returning just a string replies to the command using markup formatting. Returning a dictionary with the parameters located [here](https://core.telegram.org/bots/api#sendmessage) allows for finer control.

####[Example plugin](https://github.com/TopBakuhatsu/hitagibot/blob/master/plugins/example.py)


###To Do
- Fully support telegram bot api
- Implement some kind of database
- Clean up the logging if chains
- Help plugin

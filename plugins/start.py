def main(tg_api):
    tg_api.send_chat_action('typing')
    first_name = tg_api.get_me()['first_name']
    message = "Hi, I'm {}! A multipurpose telegram bot written in python.\n".format(first_name)
    message += 'View my source code <a href="https://github.com/TopBakuhatsu/hitagibot">here!</a>'
    tg_api.send_message(message, disable_web_page_preview=True, reply_to_message_id=None)


plugin_info = {
    'name': "Start Plugin",
    'desc': "Introduces the bot!",
    'arguments': {
        'text': [
            "^[/]start$"
        ]
    }
}

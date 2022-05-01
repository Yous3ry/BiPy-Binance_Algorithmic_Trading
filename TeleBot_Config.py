# Open the telegram app and search for @BotFather.
# Click on the start button or send “/start”.
# Then send “/newbot” message to set up a name and a username.
# After setting name and username BotFather will give you an API token which is your bot token.

# https://docs.telethon.dev/en/latest/basic/quick-start.html
# pip install telethon
from telethon import TelegramClient

# Bot Name: BiPy
# Bot Username : BiPy_Bot

bot_token = "Enter Bot Token Here"

# Log into the telegram core: https://my.telegram.org
# Go to ‘API development tools’ and fill out the form.
# You will get the api_id and api_hash parameters required for user authorization.

# my phone number
phone = "Enter Phone Number Here"

api_id = 123456789  # API ID as integers
api_hash = "Enter API Hash Here"

# creating a telegram session
# We have to manually call "start" if we want an explicit bot token
bot = TelegramClient("BiPy_Bot", api_id, api_hash).start(bot_token=bot_token)

# list of usernames to send messages to
users = ["user1", "user2"]


# define a asyncio operation for telegram
async def bot_main(message_to_send):
    # connecting and building the session
    await bot.connect()
    # sends message by username for all users
    for user in users:
        await bot.send_message(user, message_to_send, parse_mode='html')


# defines message to send
message = "Welcome to BiPy"
# calls bot to send message
bot.loop.run_until_complete(bot_main(message))

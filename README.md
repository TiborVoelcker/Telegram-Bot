# Telegram-Utils
An Interface to a Telegram Bot to send and receive messages from.

## Quickstart
### Setup
To use the package, you first have to have a Telegram Bot. To create one, send
a message to the [@BotFather](https://t.me/BotFather). You will then get a
token, which you will have to give to the `telegram_utils.TelegramBot`:
```python
bot = TelegramBot()
bot.set_bot_token("<insert your token here>")
```
To send and receive messages, you will have to also register the clients. These
will most likely be you. To do that, you can add your `client_id` directly, or
send a password to your Telegram Bot:
```python
# add your client_id directly:
bot.add_client({<your client id>: "<your name>"})

# use the register service:
bot.register_client()
```
You will then see an 8-digit password in your console, which you will have to send to 
your Telegram Bot. The `TelegramBot` will save your token and IDs, so you will
not have to do that again.
### Usage
#### Sending
Once the Bot is all set up, you can use it. To send a message simply do:
```python
import telegram

bot.send_message("Hello World!")

# send a message to a specific client:
bot.send_message("Hello <strong><em>you!</em></strong>&#128522;", 
                 client_ids={123456789: "Me"}, parse_mode=telegram.ParseMode.HTML)
```
#### Receiving
To receive a message, you can use the `get_message` decorator. The decorated
function should take a ``telegram.message.Message`` as first argument.
You can return `False` if the message is not what you wanted. The Bot will then
keep listening for messages, until the decorated function returns `True` or 
`None`.
```python
hello = "Hallo!"
@bot.get_message
def get_greeting(msg, greeting):
    if msg.text == greeting:
        return True
    else:
        return False

get_greeting(hello)
```
The decorated function will return the Chat ID and the accepted message:
```python
print(get_greeting(hello))
# output: {123456788: 'Hallo!'}
```
#### Logging Handler
The `telegram_utils` package also includes a logging Handler. You can use it 
just like any other Handler. Just be aware you will have to set up the
Handler in the same way you have set up the `TelegramBot`. But if you already
have a config file (by setting up a `TelegramBot` for example), the Handler
will use the same configuration.
```python
logger = logging.getLogger()
th = TelegramHandler()
logger.addHandler(th)

logger.warning("Let's test the TelegramHandler!")
```
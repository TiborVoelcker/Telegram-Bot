import logging
import signal
from collections.abc import Iterable
from pathlib import Path
from random import randint
from typing import Union, Callable

import telegram
from config import Config
from errors import NoTokenError, NoClientIdsError
from telegram.ext import Updater, MessageHandler, Filters


class TelegramBot:
    def __init__(self, config_filepath: Union[Path, str] = None) -> None:
        """Class to handle Telegram Bot operations.

        Before sending or receiving messages, you need to first add a token
        with `set_bot_token` and then add clients with `add_client`.

        Args:
            config_filepath: Filepath to configuration pickle file.

        Raises:
            NoTokenError: If no token was added before using the bot.
            NoClientIdsError: If no client id was added before sending a
                message.
        """
        self.logger = logging.getLogger(__name__)
        if config_filepath:
            self.config = Config(config_filepath)
        else:
            self.config = Config()

    def set_bot_token(self, token: str = None) -> None:
        """Add a Telegram Bot token returned by the BotFather."""
        self.config.token = token or input(
            "Please enter your Telegram Bot token: ")
        self.config.write_config()

    def add_client(self, client: dict) -> None:
        """Add a client to send messages to or get messages from.

        Args:
            client: The client to be added. Should be in following form:
                {<client_id>: <client_name>}.
                Can also add multiple clients at once.
        """
        self.config.client_ids.update(client)
        self.config.write_config()

    def get_message(self, f: Callable) -> Callable:
        """Decorator to listen for messages.

        Args:
            f: Function to be decorated.

                - Should have a ``telegram.message.Message`` as first argument.
                - Should return True if the correct message was received. The
                  Bot will then stop listening for messages.
                - Should return False if message was invalid. The Bot will
                  keep listening for messages.
                - `f` will return the last received message.

        Returns:
            The decorated function.
        """
        if not self.config.token:
            raise NoTokenError(
                "No Token found! Use `set_bot_token` to add a token first.")

        def wrapper(*args, **kwargs):
            updater = Updater(token=self.config.token)
            dispatcher = updater.dispatcher

            def handle_msg(update, context):
                context.chat_data.update(msg=update.message.text)
                res = f(update.message, *args, **kwargs)
                if res is False:
                    update.message.reply_text("Invalid!")
                    return False
                else:
                    update.message.reply_text("Accepted.")
                    signal.raise_signal(signal.SIGTERM)
                    return True

            dispatcher.add_handler(
                MessageHandler(Filters.text, handle_msg)
            )

            updater.start_polling(timeout=1)
            updater.idle([signal.SIGTERM])
            return dispatcher.chat_data

        return wrapper

    def register_client(self) -> None:
        """Registers a new client.

        You will be asked to send a password shown in the command line to the
        Telegram Bot. The chat were the password was send from will then be
        added to the Bots Client list.
        """
        password = "".join([str(randint(0, 9)) for _ in range(8)])
        self.logger.warning(
            f"Please send the password '{password}' to your bot."
        )

        @self.get_message
        def handle_passwd(msg):
            if msg.text == password:
                self.config.client_ids.update(
                    {msg.chat.id: msg.chat.full_name})
                self.config.write_config()
                return True
            else:
                return False

        handle_passwd()

    def send_message(
            self, message: str, parse_mode: telegram.ParseMode = None,
            client_ids: Iterable[int] = None) -> None:
        """Send a message to all (specified) clients.

        Args:
            message: The message to be send.
            parse_mode: The mode the message should be parsed.
            client_ids: A list of clients to send the message to. If none are
                specified, the message will be send to all registered clients.
        """
        if not client_ids:
            client_ids = self.config.client_ids
        if not self.config.token:
            raise NoTokenError(
                "No Token found! Use `set_bot_token` to add a token first.")
        if not client_ids:
            raise NoClientIdsError(
                "No Token found! Use `add_client` to add a clients first.")

        bot = telegram.Bot(self.config.token)

        for chat_id in client_ids:
            bot.send_message(
                chat_id=chat_id, text=message, parse_mode=parse_mode)


class TelegramHandler(logging.StreamHandler):
    def __init__(
            self, config_filepath: Union[Path, str] = None, *args, **kwargs):
        """A Handler which sends all message via a Telegram Bot."""
        super().__init__(*args, **kwargs)
        self.bot = TelegramBot(config_filepath=config_filepath)

    def emit(self, record):
        """Sends a message."""
        msg = self.format(record)
        self.bot.send_message(msg)


if __name__ == '__main__':
    b = TelegramBot()

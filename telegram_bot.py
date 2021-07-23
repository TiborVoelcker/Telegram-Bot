import logging
import os
import pickle
import signal
from collections.abc import Iterable
from pathlib import Path
from random import randint
from typing import Union, Callable

import telegram
from telegram.ext import Updater, MessageHandler, Filters

basedir = Path(__file__).parent


class ConfigError(Exception):
    """Raised when invalid configuration file."""
    pass


class NoTokenError(ConfigError):
    """Raised when no token was found."""
    pass


class NoClientIdsError(ConfigError):
    """Raised when no Client IDs were found."""
    pass


class Config:
    def __init__(
            self,
            filepath: Union[Path, str] = basedir / "telegram_config.pickle"
    ) -> None:
        """Configuration class for a telegram bot class.

        Args:
            filepath: Filepath to configuration pickle file.

        Raises:
            ConfigError: If config file could not be read.
        """
        self.filepath = Path(filepath)
        try:
            with open(self.filepath, "rb") as f:
                config = pickle.load(f)
            self.token = config.get("token")
            self.client_ids = config.get("client_ids")
        except FileNotFoundError:
            self.token = None
            self.client_ids = dict()
        except pickle.UnpicklingError as e:
            raise ConfigError("Invalid configuration file!") from e

    def write_config(self) -> None:
        """Write token and client_ids to config file."""
        config = {"token": self.token, "client_ids": self.client_ids}
        try:
            with open(self.filepath, "wb") as f:
                pickle.dump(config, f)
        except FileNotFoundError:
            os.makedirs(self.filepath.parent)
            with open(self.filepath, "wb") as f:
                pickle.dump(config, f)


class TelegramBot:
    def __init__(self, config_filepath: Union[Path, str] = None) -> None:
        """Class to handle Telegram Bot operations.

        Before sending or recieving messages, you need to first add a token
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

    def add_client(self, client: dict = None) -> None:
        """Add a client to send messages to or get messages from.

        Args:
            client: The client to be added. Should be in following form:
                {<client_id>: <client_name>}.
                Can also add multiple clients at once.
        """
        if client:
            self.config.client_ids.update(client)
            self.config.write_config()

        else:
            self.__register_client()

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
        if not self.config.client_ids:
            raise NoClientIdsError(
                "No Token found! Use `add_client` to add a clients first.")

        def wrapper(*args, **kwargs):
            updater = Updater(token=self.config.token)
            dispatcher = updater.dispatcher

            def handle_msg(update, context):
                if update.message.chat.id not in self.config.client_ids:
                    return False
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

    def __register_client(self) -> None:
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
    b.set_bot_token("1880935920:AAFW9hVOh2kzzcEpBf7ad7g-gnCBy_e6HLM")
    b.add_client()

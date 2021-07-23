import os
import pickle
from pathlib import Path
from typing import Union

from errors import ConfigError

basedir = Path(__file__).parent


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

class ConfigError(Exception):
    """Raised when invalid configuration file."""
    pass


class NoTokenError(ConfigError):
    """Raised when no token was found."""
    pass


class NoClientIdsError(ConfigError):
    """Raised when no Client IDs were found."""
    pass

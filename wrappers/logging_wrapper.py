import logging

from utils.config import dict

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

_logger = logging.getLogger("tbh_bot")

if not _logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _logger.addHandler(handler)


def apply_log_level():
    level_name = dict["log_lvl"].get()
    _logger.setLevel(_LOG_LEVELS.get(level_name, logging.INFO))


apply_log_level()


def debug(message):
    _logger.debug(message)


def info(message):
    _logger.info(message)


def warning(message):
    _logger.warning(message)


def error(message):
    _logger.error(message)

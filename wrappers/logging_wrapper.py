import logging
from datetime import datetime
from pathlib import Path

from utils.config import dict
from utils.global_variables import APP_LOGGER_NAME, BASE_DIR

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

_logger = logging.getLogger(APP_LOGGER_NAME)
_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

if not _logger.handlers:
    _console = logging.StreamHandler()
    _console.setFormatter(_formatter)
    _logger.addHandler(_console)


def apply_log_level():
    level_name = dict["log_lvl"].get()
    _logger.setLevel(_LOG_LEVELS.get(level_name, logging.INFO))


def enable_file_logging() -> str:
    """Abre um arquivo de log em logs/ com nível DEBUG. Retorna o caminho do arquivo."""
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Remove handlers de arquivo anteriores para não acumular
    for h in list(_logger.handlers):
        if isinstance(h, logging.FileHandler):
            h.close()
            _logger.removeHandler(h)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = logs_dir / f"map_runner_{ts}.log"

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_formatter)
    _logger.addHandler(fh)

    # Garante que o logger aceite DEBUG independente da config de UI
    if _logger.level > logging.DEBUG:
        _logger.setLevel(logging.DEBUG)

    return str(log_path)


apply_log_level()


def debug(message):
    _logger.debug(message)


def info(message):
    _logger.info(message)


def warning(message):
    _logger.warning(message)


def error(message):
    _logger.error(message)

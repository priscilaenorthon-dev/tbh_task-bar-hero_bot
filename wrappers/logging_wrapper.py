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
_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(module)s: %(message)s")

if not _logger.handlers:
    _console = logging.StreamHandler()
    _console.setFormatter(_formatter)
    _logger.addHandler(_console)


def apply_log_level():
    level_name = dict["log_lvl"].get()
    _logger.setLevel(_LOG_LEVELS.get(level_name, logging.INFO))


def _rotate_logs(logs_dir: Path, prefix: str, max_files: int = 10):
    """Delete oldest log files, keeping only the most recent max_files for this prefix."""
    files = sorted(logs_dir.glob(f"{prefix}_*.log"), key=lambda f: f.stat().st_mtime)
    for old_file in files[:-max_files]:
        try:
            old_file.unlink()
        except OSError:
            pass


def enable_file_logging(prefix: str = "stash") -> str:
    """Opens a timestamped log file in logs/ with DEBUG level. Returns the file path."""
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Remove existing file handlers to avoid accumulation
    for h in list(_logger.handlers):
        if isinstance(h, logging.FileHandler):
            h.close()
            _logger.removeHandler(h)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = logs_dir / f"{prefix}_{ts}.log"

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_formatter)
    _logger.addHandler(fh)

    if _logger.level > logging.DEBUG:
        _logger.setLevel(logging.DEBUG)

    _rotate_logs(logs_dir, prefix, max_files=10)
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

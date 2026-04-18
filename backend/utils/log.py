import logging
import sys
from typing import Dict


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # If already configured, return as-is to avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            # Standard record attributes to ignore when collecting extras
            standard_keys = {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "asctime", "extra_fields",
            }
            extras: Dict[str, object] = {
                k: v for k, v in record.__dict__.items() if k not in standard_keys
            }
            extra_str = ""
            if extras:
                # Escape quotes in values to keep JSON-like output safe
                parts = []
                for k, v in extras.items():
                    val = str(v).replace('"', '\\"')
                    parts.append(f'"{k}": "{val}"')
                extra_str = ", " + ", ".join(parts)
            record.extra_fields = extra_str
            # Use the parent class to format the base message with our injected extra_fields
            return super().format(record)

    formatter = JsonFormatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": "%(message)s"%(extra_fields)s}'
    )
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.propagate = False

    return logger

import logging
import os
from logging.handlers import RotatingFileHandler

import structlog
from structlog.stdlib import ProcessorFormatter

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_BUS = None


def _ws_processor(logger, method_name, event_dict):
    if _LOG_BUS is not None:
        try:
            _LOG_BUS.publish({
                "type": "log",
                "level": method_name,
                "event": event_dict.get("event", ""),
                "ts": event_dict.get("timestamp", ""),
            })
        except Exception:
            pass
    return event_dict


def setup_logging(event_bus=None):
    global _LOG_BUS
    _LOG_BUS = event_bus

    lib_logger = logging.getLogger()
    lib_logger.setLevel(LOG_LEVEL)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)

    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "cryp.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setLevel(LOG_LEVEL)

    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "cryp-error.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    error_handler.setLevel(logging.WARNING)

    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _ws_processor,
    ]

    formatter = ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(),
        ],
    )
    console_handler.setFormatter(formatter)

    json_formatter = ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    file_handler.setFormatter(json_formatter)
    error_handler.setFormatter(json_formatter)

    lib_logger.addHandler(console_handler)
    lib_logger.addHandler(file_handler)
    lib_logger.addHandler(error_handler)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


get_logger = structlog.get_logger

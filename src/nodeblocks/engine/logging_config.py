import logging
import logging.config
from typing import Optional, Union

def setup_logging(default_level: Union[int, str] = logging.INFO, debug_modules: Optional[list[str]] = None):
    debug_modules = debug_modules or []

    def get_module_level(name: str) -> int | str:
        return logging.DEBUG if name in debug_modules else default_level

    LOGGING_CONFIG: logging.config._DictConfigArgs = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simpleFormatter": {
                "format": "%(asctime)s | %(name)s:%(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "consoleHandler": {
                "class": "logging.StreamHandler",
                "level": default_level,
                "formatter": "simpleFormatter",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "nds": {
                "level": default_level,
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.benchmark": {
                "level": get_module_level("nds.benchmark"),
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.engine": {
                "level": get_module_level("nds.engine"),
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.server": {
                "level": get_module_level("nds.server"),
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.spec": {
                "level": get_module_level("nds.spec"),
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.plugins": {
                "level": get_module_level("nds.plugins"),
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.worker": {
                "level": get_module_level("nds.worker"),
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "aiohttp.access": {
                "level": logging.WARNING if default_level != logging.DEBUG else logging.INFO,
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
        },
        "root": {
            "level": default_level,
            "handlers": ["consoleHandler"],
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)

import logging
import logging.config

def setup_logging(default_level=logging.INFO):
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
            "nds.benchmark": {
                "level": "DEBUG",
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.engine": {
                "level": "INFO",
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.server": {
                "level": "INFO",
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.spec": {
                "level": "INFO",
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.plugins": {
                "level": "INFO",
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
            "nds.worker": {
                "level": "DEBUG",
                "handlers": ["consoleHandler"],
                "propagate": False,
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["consoleHandler"],
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)

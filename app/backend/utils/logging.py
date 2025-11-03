"""Implement for kafka log."""

import logging
import sys
from logging.config import dictConfig
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def _init_config():
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.NullHandler",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.NullHandler",
                },
            },
            "loggers": {
                "uvicorn.error": {
                    "level": "INFO",
                    "handlers": ["default"],
                    "propagate": True,
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["access"],
                    "propagate": True,
                },
            },
        },
    )


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """Drop duplicated color message.

    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def remove_processors_meta(_, __, event_dict: EventDict) -> EventDict:
    """Override structlog.Processors.remove_processors_meta."""
    if "_record" in event_dict:
        del event_dict["_record"]

    if "_from_structlog" in event_dict:
        del event_dict["_from_structlog"]

    return event_dict


def _get_shared_processors(*, enable_json: bool = False) -> list[Processor]:
    """Get shared processors.

    Parameters
    ----------
    enable_json : bool, optional
        is json logging enabled?, by default False
    """
    if enable_json:
        return [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.PATHNAME,
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.THREAD,
                    structlog.processors.CallsiteParameter.THREAD_NAME,
                    structlog.processors.CallsiteParameter.PROCESS,
                    structlog.processors.CallsiteParameter.PROCESS_NAME,
                },
            ),
            structlog.stdlib.ExtraAdder(),
            drop_color_message_key,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            # We rename the `event` key to `message` only in JSON logs, as Datadog looks for the
            # `message` key but the pretty ConsoleRenderer looks for `event`
            structlog.processors.EventRenamer(to="message"),
            # Format the exception only for JSON logs, as we want to pretty-print them when
            # using the ConsoleRenderer
            structlog.processors.format_exc_info,
        ]

    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        drop_color_message_key,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]


def configure_logging(*, debug: bool = False, enable_json: bool = False):
    """Configure logging.

    Parameters
    ----------
    debug : bool, optional
        is debug mode enabled ?, by default False
    enable_json : bool, optional
        is json log enabled ?, by default False
    """
    _init_config()

    shared_processors: list[Processor] = _get_shared_processors(enable_json=enable_json)

    structlog.configure(
        # Prepare event dict for `ProcessorFormatter`.
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log_renderer: Any = structlog.processors.JSONRenderer() if enable_json else structlog.dev.ConsoleRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            remove_processors_meta,
            log_renderer,
        ],
    )

    log_level = "DEBUG" if debug else "INFO"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    logging.getLogger("celery.bootsteps").setLevel(logging.WARNING)
    logging.getLogger("ddtrace.internal.processor").setLevel(logging.WARNING)
    logging.getLogger("kombu").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
    logging.getLogger("circus").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers.SentenceTransformer").setLevel(logging.WARNING)

    for _log in ["uvicorn", "uvicorn.error", "bentoml"]:
        logger = logging.getLogger(_log)
        logger.handlers.clear()
        logger.propagate = True

    # Since we re-create the access logs ourselves, to add all information
    # in the structured log (see the `logging_middleware` in main.py), we clear
    # the handlers and prevent the logs to propagate to a logger higher up in the
    # hierarchy (effectively rendering them silent).
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False

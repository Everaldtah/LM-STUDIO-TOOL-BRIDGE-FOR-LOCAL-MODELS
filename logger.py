"""
Logging module for LM Studio Terminal Bridge.

Provides centralized logging functionality for all modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from config import LOG_DIR, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL


class BridgeLogger:
    """
    Custom logger class for the LM Studio Terminal Bridge.

    Provides both file and console logging with consistent formatting.
    """

    _loggers = {}

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger instance with the specified name.

        Args:
            name: The name of the logger (typically __name__ of the module)

        Returns:
            A configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LOG_LEVEL))

        # Avoid adding handlers multiple times
        if logger.handlers:
            return logger

        # Create formatters
        formatter = logging.Formatter(
            fmt=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)

        # File handler
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def log_command_execution(
        cls,
        command: str,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        logger_name: str = "bridge.executor"
    ) -> None:
        """
        Log a command execution with all relevant details.

        Args:
            command: The executed command
            stdout: Standard output from the command
            stderr: Standard error from the command
            return_code: The process return code
            execution_time: Time taken to execute in seconds
            logger_name: Name of the logger to use
        """
        logger = cls.get_logger(logger_name)

        logger.info(f"Command executed: {command}")
        logger.debug(f"Return code: {return_code}")
        logger.debug(f"Execution time: {execution_time:.3f}s")

        if stdout:
            logger.debug(f"stdout: {stdout[:500]}{'...' if len(stdout) > 500 else ''}")
        if stderr:
            logger.warning(f"stderr: {stderr[:500]}{'...' if len(stderr) > 500 else ''}")

        if return_code != 0:
            logger.error(f"Command failed with return code: {return_code}")

    @classmethod
    def log_tool_call(
        cls,
        tool_name: str,
        arguments: dict,
        logger_name: str = "bridge.router"
    ) -> None:
        """
        Log a tool call invocation.

        Args:
            tool_name: Name of the tool being called
            arguments: Arguments passed to the tool
            logger_name: Name of the logger to use
        """
        logger = cls.get_logger(logger_name)
        logger.info(f"Tool called: {tool_name} with args: {arguments}")

    @classmethod
    def log_security_event(
        cls,
        event_type: str,
        details: str,
        logger_name: str = "bridge.security"
    ) -> None:
        """
        Log a security-related event.

        Args:
            event_type: Type of security event (blocked, allowed, warning)
            details: Details of the event
            logger_name: Name of the logger to use
        """
        logger = cls.get_logger(logger_name)
        if event_type == "blocked":
            logger.error(f"Security BLOCK: {details}")
        elif event_type == "warning":
            logger.warning(f"Security WARNING: {details}")
        else:
            logger.info(f"Security: {details}")


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds ANSI colors to log levels.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        formatted = super().format(record)
        # Reset levelname for other handlers
        record.levelname = levelname
        return formatted


# Convenience function for easy import
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return BridgeLogger.get_logger(name)

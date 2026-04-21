"""
Logging utilities for Personal AI Employee.

Provides consistent logging across all components with timestamp,
level, component name, and message formatting.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class VaultLogger:
    """Logger that writes to both console and vault log files."""

    def __init__(self, vault_path: str, component_name: str, log_level: str = "INFO"):
        """
        Initialize logger for a component.

        Args:
            vault_path: Path to Obsidian vault
            component_name: Name of the component (e.g., "FileWatcher")
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.vault_path = Path(vault_path)
        self.component_name = component_name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)

        # Create logger
        self.logger = logging.getLogger(component_name)
        self.logger.setLevel(self.log_level)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (vault logs)
        self._setup_file_handler()

    def _setup_file_handler(self):
        """Setup file handler for vault logs."""
        logs_dir = self.vault_path / "Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Log file: YYYY-MM-DD.log
        log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False):
        """Log error message with optional exception info."""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False):
        """Log critical message with optional exception info."""
        self.logger.critical(message, exc_info=exc_info)


def create_logger(vault_path: str, component_name: str, log_level: str = "INFO") -> VaultLogger:
    """
    Factory function to create a VaultLogger instance.

    Args:
        vault_path: Path to Obsidian vault
        component_name: Name of the component
        log_level: Logging level

    Returns:
        VaultLogger instance
    """
    return VaultLogger(vault_path, component_name, log_level)

"""
Centralized logging configuration for repo-app.

Author: Automated Software Engineering Team
Date: February 2026
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis for terminal output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    # Emoji icons for each level
    ICONS = {
        'DEBUG': '🔍',
        'INFO': '📝',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }
    
    def __init__(self, use_colors: bool = True, use_icons: bool = True):
        super().__init__()
        self.use_colors = use_colors
        self.use_icons = use_icons
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and icons"""
        # Build the message
        icon = self.ICONS.get(record.levelname, '') if self.use_icons else ''
        color = self.COLORS.get(record.levelname, '') if self.use_colors else ''
        reset = self.COLORS['RESET'] if self.use_colors else ''
        
        # Format: [LEVEL] icon message
        if record.levelno >= logging.WARNING:
            # For warnings and errors, include more context
            formatted = f"{color}[{record.levelname}]{reset} {icon} {record.getMessage()}"
            if record.exc_info:
                formatted += f"\n{self.formatException(record.exc_info)}"
        else:
            # For info and debug, simpler format
            formatted = f"{icon} {record.getMessage()}"
        
        return formatted


class RepoAppLogger:
    """Centralized logger for repo-app with configurable levels and output"""
    
    _instance: Optional['RepoAppLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern to ensure one logger instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger (only once)"""
        if not RepoAppLogger._initialized:
            self.logger = logging.getLogger('repo-app')
            self._setup_logger()
            RepoAppLogger._initialized = True
    
    def _setup_logger(self):
        """Setup logger with handlers and formatters"""
        # Get log level from environment or default to INFO
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        self.logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Determine if we should use colors (check if terminal supports it)
        use_colors = self._supports_color()
        console_formatter = ColoredFormatter(use_colors=use_colors, use_icons=True)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
        
        # File handler (optional, based on environment variable)
        log_file = os.getenv('LOG_FILE')
        if log_file:
            try:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_path)
                file_handler.setLevel(log_level)
                
                # File handler uses plain format without colors
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Failed to setup file logging: {e}")
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _supports_color(self) -> bool:
        """Check if terminal supports color output"""
        # Check if output is a terminal
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check for NO_COLOR environment variable
        if os.getenv('NO_COLOR'):
            return False
        
        # Check TERM variable
        term = os.getenv('TERM', '')
        if term in ('dumb', ''):
            return False
        
        return True
    
    def set_level(self, level: str):
        """Set logging level dynamically"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self.logger


# Global logger instance
_logger_instance = RepoAppLogger()


def get_logger() -> logging.Logger:
    """
    Get the repo-app logger instance.
    
    Returns:
        logging.Logger: Configured logger for repo-app
    
    Usage:
        from logger import get_logger
        logger = get_logger()
        logger.info("Processing repository")
        logger.debug("Detailed debug information")
        logger.warning("Something to watch out for")
        logger.error("An error occurred", exc_info=True)
    """
    return _logger_instance.get_logger()


def set_log_level(level: str):
    """
    Set the logging level for repo-app.
    
    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    
    Usage:
        from logger import set_log_level
        set_log_level('DEBUG')
    """
    _logger_instance.set_level(level)


# Convenience functions for common logging patterns
def log_repo_analysis_start(repo_name: str):
    """Log start of repository analysis"""
    logger = get_logger()
    logger.info("")  # Blank line for readability
    logger.info(f"{'='*60}")
    logger.info(f"Analyzing: {repo_name}")
    logger.info(f"{'='*60}")


def log_repo_analysis_end(repo_name: str, success: bool):
    """Log end of repository analysis"""
    logger = get_logger()
    if success:
        logger.info(f"✅ Analysis complete: {repo_name}")
    else:
        logger.error(f"❌ Analysis failed: {repo_name}")
    logger.info("")  # Blank line for readability


def log_metric(label: str, value: any):
    """Log a metric in a consistent format"""
    logger = get_logger()
    logger.info(f"   {label}: {value}")


def log_section(title: str):
    """Log a section header"""
    logger = get_logger()
    logger.debug(f"\n--- {title} ---")

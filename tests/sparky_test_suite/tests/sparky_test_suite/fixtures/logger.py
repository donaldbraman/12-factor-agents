#!/usr/bin/env python3
"""
Logger module for error handling
"""

import logging


def setup_logger():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


def log_error(error):
    logger = setup_logger()
    logger.error(f"Error occurred: {error}")

import logging
import os
import sys
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure the logger
log_filename = f"logs/code_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Set up the root logger
logger = logging.getLogger("code_graph")
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)

def get_logger(name):
    """Get a logger with the given name."""
    return logging.getLogger(f"code_graph.{name}")

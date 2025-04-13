import logging
import sys
from datetime import datetime

# Set up the root logger
logger = logging.getLogger("code_graph")
logger.setLevel(logging.INFO)

# Use NullHandler to prevent any logging output
logger.addHandler(logging.NullHandler())

# Optional: Uncomment below to log to console instead of files
# console_handler = logging.StreamHandler(sys.stdout)
# console_handler.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)

def get_logger(name):
    """Get a logger with the given name."""
    child_logger = logging.getLogger(f"code_graph.{name}")
    # Ensure this logger also doesn't create any output
    child_logger.addHandler(logging.NullHandler())
    return child_logger

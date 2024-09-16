import os
import logging


def setup_shared_logger(site_name: str) -> logging.Logger:
    """
    Sets up a shared logger for multiple scrapers, creating directories for logging.

    Args:
        site_name (str): The name of the site (e.g., 'shared_log').

    Returns:
        logging.Logger: Configured shared logger instance.
    """
    # Define the log directory structure
    log_dir = os.path.join("logs", site_name)
    os.makedirs(log_dir, exist_ok=True)

    # Create a log file name for shared logging
    log_file_name = f"{site_name}.log"
    log_file_path = os.path.join(log_dir, log_file_name)

    # Create a shared logger for multiple scrapers
    logger = logging.getLogger(site_name)
    logger.setLevel(logging.INFO)

    # Create a file handler that logs to a specific file
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)

    # Create a stream handler to output logs to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    # Create a logging format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add the handlers to the logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

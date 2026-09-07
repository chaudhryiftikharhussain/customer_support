import logging

LOG_FILE = "app.log"

logger = logging.getLogger("customer_support_app")
logger.setLevel(logging.DEBUG)

# Prevent duplicate logs if this module is reloaded
if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Uvicorn, access logger
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.setLevel(logging.INFO)
uvicorn_access_logger.addHandler(file_handler)
uvicorn_access_logger.addHandler(console_handler)

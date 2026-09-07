import json
from config.logging_config import logger as app_logger


def read_tickets_json_file():
    try:
        with open("tickets.json", "r", encoding="utf-8") as file:
            tickets = json.load(file)
            app_logger.info("file read ok")
        return True, tickets, "ok"
    except FileNotFoundError as e:
        app_logger.exception(f"file not found error {e}")
        return False, None, "file_not_found_error"
    except Exception:
        app_logger.exception("file reading error server error")
        return False, None, "file_read_error"


def write_tickets_json_file(tickets):
    try:
        with open("tickets.json", "w", encoding="utf-8") as file:
            json.dump(tickets, file, indent=4)
            file.write("\n")
        return True, "ok"
    except Exception:
        return False, "file_write_error"

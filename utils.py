import json


def read_tickets_json_file():
    try:
        with open("tickets.json", "r", encoding="utf-8") as file:
            tickets = json.load(file)
        return True, tickets, "ok"
    except FileNotFoundError:
        return False, None, "file_not_found_error"
    except Exception:
        return False, None, "file_read_error"


def write_tickets_json_file(tickets):
    try:
        with open("tickets.json", "w", encoding="utf-8") as file:
            json.dump(tickets, file, indent=4)
            file.write("\n")
        return True, "ok"
    except Exception:
        return False, "file_write_error"

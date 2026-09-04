# Customer Support API

FastAPI service for customer support tickets. Data is stored in `tickets.json` (no database).

```
customer_support/
├── main.py
├── schemas.py
├── utils.py
├── tickets.json
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
fastapi dev main.py
```

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/tickets` | List tickets with optional filters, search, sort, and pagination |
| `GET` | `/tickets/{ticket_id}` | Get one ticket (`404` if missing) |
| `POST` | `/tickets` | Create a ticket (ID, `created_at`, and status are generated) |
| `GET` | `/tickets/statistics` | Live ticket counts by status and priority |
| `GET` | `/tickets/statistics/categories` | Ticket counts by category |
| `GET` | `/tickets/high-priority` | Tickets with priority `high` or `urgent` |
| `GET` | `/customers/{customer_name}/tickets` | Tickets for a customer (empty list if none) |

### `GET /tickets` query parameters

| Parameter | Example | Notes |
| --- | --- | --- |
| `status` | `open` | Exact match |
| `priority` | `urgent` | Exact match |
| `category` | `payment` | Exact match |
| `customer_name` | `Ali` | Matches names containing `Ali` as a word |
| `search` | `login` | Searches `subject` and `description` |
| `created_after` | `2026-09-01` | Tickets created at or after this date/time |
| `sort` | `priority` or `-created_at` | Prefix `-` for descending |
| `page` | `1` | Used with `limit` |
| `limit` | `10` | Page size |

Multiple filters apply together (AND):

```
/tickets?category=payment&priority=urgent&status=open
```

Combined example:

```
/tickets?category=technical&status=open&sort=created_at&page=1&limit=10
```

### `POST /tickets` body

The client sends customer and issue details only:

```json
{
  "customer_name": "Ali Khan",
  "email": "ali.khan@example.com",
  "subject": "Unable to login",
  "description": "I cannot sign in with my current password.",
  "category": "authentication",
  "priority": "high"
}
```

The API sets `id`, `created_at`, and `status` (`open`).

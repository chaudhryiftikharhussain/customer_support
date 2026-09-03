"""
Cursor generated code

"""

import json
import re
from datetime import datetime
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

TICKETS_FILE = Path(__file__).parent / "tickets.json"

PRIORITY_RANK = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
ALLOWED_SORT_FIELDS = {"id", "priority", "status", "category", "created_at", "customer_name"}


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TicketCategory(str, Enum):
    authentication = "authentication"
    payment = "payment"
    technical = "technical"
    account = "account"
    billing = "billing"
    other = "other"


class TicketCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, examples=["Ali Khan"])
    email: EmailStr = Field(..., examples=["ali.khan@example.com"])
    subject: str = Field(..., min_length=1, examples=["Unable to login"])
    description: str = Field(..., min_length=1, examples=["I cannot sign in with my current password."])
    category: TicketCategory
    priority: TicketPriority

class TicketUpdate(BaseModel):
    id: str = Field(..., min_length=1, examples=["Ali Khan"])
    customer_name: str = Field(..., min_length=1, examples=["Ali Khan"])
    email: EmailStr = Field(..., examples=["ali.khan@example.com"])
    subject: str = Field(..., min_length=1, examples=["Unable to login"])
    description: str = Field(..., min_length=1, examples=["I cannot sign in with my current password."])
    category: TicketCategory
    priority: TicketPriority


class Ticket(TicketCreate):
    id: int
    status: TicketStatus
    created_at: str


class TicketStatistics(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    urgent_tickets: int
    high_priority_tickets: int


def load_tickets() -> list[dict]:
    with TICKETS_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def save_tickets(tickets: list[dict]) -> None:
    with TICKETS_FILE.open("w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4)
        file.write("\n")


def next_ticket_id(tickets: list[dict]) -> int:
    if not tickets:
        return 1
    return max(ticket["id"] for ticket in tickets) + 1


def add_ticket(payload: TicketCreate) -> dict:
    tickets = load_tickets()
    ticket = {
        "id": next_ticket_id(tickets),
        "customer_name": payload.customer_name,
        "email": str(payload.email),
        "subject": payload.subject,
        "description": payload.description,
        "category": payload.category.value,
        "priority": payload.priority.value,
        "status": TicketStatus.open.value,
        "created_at": datetime.now().replace(microsecond=0).isoformat(),
    }
    tickets.append(ticket)
    save_tickets(tickets)
    return ticket


def filter_tickets(
    tickets: list[dict],
    *,
    status_filter: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    customer_name: str | None = None,
    search: str | None = None,
    created_after: datetime | None = None,
) -> list[dict]:
    if status_filter is not None:
        tickets = [ticket for ticket in tickets if ticket["status"].lower() == status_filter.lower()]
    if priority is not None:
        tickets = [ticket for ticket in tickets if ticket["priority"].lower() == priority.lower()]
    if category is not None:
        tickets = [ticket for ticket in tickets if ticket["category"].lower() == category.lower()]
    if customer_name is not None:
        name_pattern = re.compile(rf"\b{re.escape(customer_name)}", re.IGNORECASE)
        tickets = [ticket for ticket in tickets if name_pattern.search(ticket["customer_name"])]
    if search is not None:
        query = search.lower()
        tickets = [
            ticket
            for ticket in tickets
            if query in ticket["subject"].lower() or query in ticket["description"].lower()
        ]
    if created_after is not None:
        tickets = [
            ticket
            for ticket in tickets
            if datetime.fromisoformat(ticket["created_at"]) >= created_after
        ]
    return tickets


def sort_tickets(tickets: list[dict], sort: str | None) -> list[dict]:
    if sort is None:
        return tickets

    descending = sort.startswith("-")
    field = sort[1:] if descending else sort
    if field not in ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort field '{sort}'. Allowed: {', '.join(sorted(ALLOWED_SORT_FIELDS))}",
        )

    def sort_key(ticket: dict):
        value = ticket[field]
        if field == "priority":
            return PRIORITY_RANK.get(str(value).lower(), 99)
        return value

    return sorted(tickets, key=sort_key, reverse=descending)


def paginate_tickets(tickets: list[dict], page: int, limit: int | None) -> list[dict]:
    if limit is None:
        return tickets
    start = (page - 1) * limit
    return tickets[start : start + limit]


app = FastAPI(
    title="Customer Support API",
    description="REST API for managing customer support tickets stored in tickets.json.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Tickets", "description": "Create, list, filter, and retrieve support tickets."},
        {"name": "Statistics", "description": "Dynamic summaries calculated from tickets.json."},
        {"name": "Customers", "description": "Look up tickets by customer name."},
    ],
)


@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Customer Support API. Open /docs for Swagger UI."}


@app.get(
    "/tickets",
    response_model=list[Ticket],
    tags=["Tickets"],
    summary="List support tickets",
    description=(
        "Retrieve all support tickets. Optional query parameters can filter, search, "
        "sort, and paginate results. Multiple filters are combined with AND."
    ),
)
def get_tickets(
    status_filter: str | None = Query(None, alias="status", description="Filter by ticket status"),
    priority: str | None = Query(None, description="Filter by ticket priority"),
    category: str | None = Query(None, description="Filter by ticket category"),
    customer_name: str | None = Query(None, description="Filter by customer name (partial match)"),
    search: str | None = Query(None, description="Search in subject and description"),
    created_after: datetime | None = Query(None, description="Only tickets created at or after this date/time"),
    sort: str | None = Query(None, description="Sort field. Prefix with '-' for descending, e.g. -created_at"),
    page: int = Query(1, ge=1, description="Page number (used with limit)"),
    limit: int | None = Query(None, ge=1, le=100, description="Page size"),
):
    tickets = load_tickets()
    tickets = filter_tickets(
        tickets,
        status_filter=status_filter,
        priority=priority,
        category=category,
        customer_name=customer_name,
        search=search,
        created_after=created_after,
    )
    tickets = sort_tickets(tickets, sort)
    return paginate_tickets(tickets, page, limit)


@app.post(
    "/tickets",
    response_model=Ticket,
    status_code=status.HTTP_201_CREATED,
    tags=["Tickets"],
    summary="Create a support ticket",
    description=(
        "Create a new ticket from customer and issue details. "
        "Ticket ID, creation time, and initial status (open) are generated by the API."
    ),
)
def create_ticket(payload: TicketCreate):
    return add_ticket(payload)

@app.put(
    "/tickets",
    response_model=Ticket,
    status_code=status.HTTP_201_CREATED,
    tags=["Tickets"],
    summary="Create a support ticket",
    description=(
        "Create a new ticket from customer and issue details. "
        "Ticket ID, creation time, and initial status (open) are generated by the API."
    ),
)
def create_ticket(payload: TicketCreate):
    return add_ticket(payload)

@app.patch(
    "/tickets",
    response_model=Ticket,
    status_code=status.HTTP_201_CREATED,
    tags=["Tickets"],
    summary="Create a support ticket",
    description=(
        "Create a new ticket from customer and issue details. "
        "Ticket ID, creation time, and initial status (open) are generated by the API."
    ),
)
def create_ticket(payload: TicketCreate):
    return add_ticket(payload)


@app.get(
    "/tickets/statistics",
    response_model=TicketStatistics,
    tags=["Statistics"],
    summary="Get ticket statistics",
    description="Return a live summary of ticket counts by status and high/urgent priority.",
)
def get_statistics():
    tickets = load_tickets()
    return TicketStatistics(
        total_tickets=len(tickets),
        open_tickets=sum(ticket["status"] == "open" for ticket in tickets),
        in_progress_tickets=sum(ticket["status"] == "in_progress" for ticket in tickets),
        resolved_tickets=sum(ticket["status"] == "resolved" for ticket in tickets),
        closed_tickets=sum(ticket["status"] == "closed" for ticket in tickets),
        urgent_tickets=sum(ticket["priority"] == "urgent" for ticket in tickets),
        high_priority_tickets=sum(ticket["priority"] == "high" for ticket in tickets),
    )


@app.get(
    "/tickets/statistics/categories",
    response_model=dict[str, int],
    tags=["Statistics"],
    summary="Get ticket counts by category",
    description="Return the number of tickets in each category, calculated from tickets.json.",
)
def get_category_statistics():
    tickets = load_tickets()
    counts = {category.value: 0 for category in TicketCategory}
    for ticket in tickets:
        category = ticket["category"]
        counts[category] = counts.get(category, 0) + 1
    return counts


@app.get(
    "/tickets/high-priority",
    response_model=list[Ticket],
    tags=["Tickets", "Urgent"],
    summary="List high-priority tickets",
    description="Retrieve all tickets whose priority is high or urgent.",
)
def get_high_priority_tickets():
    tickets = load_tickets()
    return [ticket for ticket in tickets if ticket["priority"] in {"high", "urgent"}]


@app.delete(
    "/tickets/{ticket_id}",
    response_model=Ticket,
    tags=["Tickets"],
    summary="Get a ticket by ID",
    description="Retrieve a single support ticket. Returns 404 if the ticket does not exist.",
    responses={404: {"description": "Ticket not found"}},
)
def get_ticket(ticket_id: int):
    for ticket in load_tickets():
        if ticket["id"] == ticket_id:
            return ticket
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket {ticket_id} not found")


@app.get(
    "/customers/{customer_name}/tickets",
    response_model=list[Ticket],
    tags=["Customers"],
    summary="List tickets for a customer",
    description="Retrieve all tickets for the given customer name. Returns an empty list if none exist.",
)
def get_customer_tickets(customer_name: str):
    tickets = load_tickets()
    return [
        ticket
        for ticket in tickets
        if ticket["customer_name"].lower() == customer_name.lower()
    ]

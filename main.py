from datetime import datetime

from fastapi import FastAPI, status as http_status

from starlette.requests import Request
from starlette.responses import JSONResponse

from schemas import TicketInput, TicketPatchInput, TicketPutInput
from utils import read_tickets_json_file, write_tickets_json_file

from config.static_config import mount_static_files  # import static
from config.templates_config import templates as project_templates  # import template


app = FastAPI(
    title="Customer Support API",
    description="Customer support tickets stored in tickets.json.",
)

# Mount the static files
mount_static_files(app)


def file_error_response(message):
    if message == "file_not_found_error":
        return JSONResponse(
            status_code=http_status.HTTP_404_NOT_FOUND,
            content={"message": "file does not exist"},
        )
    return JSONResponse(
        status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"message": "file read issue"},
    )

@app.get("/dashboard")
async def dashboard(request: Request):
    print("test_html_page api is called")
    # json read krain tickets.json or table me show kr dein
    tickets = []
    return project_templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "ticket": tickets
        },
    )


@app.get(
    "/tickets",
    tags=["Tickets"],
    summary="Retrieve all support tickets",
)
def get_tickets(
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    customer_name: str | None = None,
    search: str | None = None,
    created_after: str | None = None,
    sort: str | None = None,
    page: int | None = None,
    limit: int | None = None,
):
    print("/tickets api is called")
    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    filtered_tickets = tickets

    if status:
        filtered_tickets = [
            ticket for ticket in filtered_tickets if ticket["status"].lower() == status.lower()
        ]

    if priority:
        filtered_tickets = [
            ticket for ticket in filtered_tickets if ticket["priority"].lower() == priority.lower()
        ]

    if category:
        filtered_tickets = [
            ticket for ticket in filtered_tickets if ticket["category"].lower() == category.lower()
        ]

    if customer_name:
        filtered_tickets = [
            ticket
            for ticket in filtered_tickets
            if customer_name.lower() in ticket["customer_name"].lower()
        ]

    if search:
        filtered_tickets = [
            ticket
            for ticket in filtered_tickets
            if search.lower() in ticket["subject"].lower()
            or search.lower() in ticket["description"].lower()
        ]

    if created_after:
        filtered_tickets = [
            ticket for ticket in filtered_tickets if ticket["created_at"] >= created_after
        ]

    if sort:
        if sort == "priority" or sort == "-priority":
            rank = {"urgent": 1, "high": 2, "medium": 3, "low": 4}
            reverse = sort.startswith("-")
            filtered_tickets = sorted(
                filtered_tickets,
                key=lambda ticket: rank.get(ticket["priority"], 99),
                reverse=reverse,
            )
        else:
            reverse = sort.startswith("-")
            field = sort[1:] if reverse else sort
            filtered_tickets = sorted(
                filtered_tickets,
                key=lambda ticket: ticket.get(field, ""),
                reverse=reverse,
            )

    if page and limit:
        start = (page - 1) * limit
        filtered_tickets = filtered_tickets[start:start + limit]

    print("now returning tickets")
    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content={
            "message": "tickets found",
            "tickets": filtered_tickets,
        },
    )


@app.get(
    "/tickets/statistics",
    tags=["Statistics"],
    summary="Return a summary of the support tickets",
)
def get_ticket_statistics():
    print("/tickets/statistics api is called")
    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    total_tickets = 0
    open_tickets = 0
    in_progress_tickets = 0
    resolved_tickets = 0
    closed_tickets = 0
    urgent_tickets = 0
    high_priority_tickets = 0

    for ticket in tickets:
        total_tickets += 1
        if ticket["status"] == "open":
            open_tickets += 1
        elif ticket["status"] == "in_progress":
            in_progress_tickets += 1
        elif ticket["status"] == "resolved":
            resolved_tickets += 1
        elif ticket["status"] == "closed":
            closed_tickets += 1

        if ticket["priority"] == "urgent":
            urgent_tickets += 1
        elif ticket["priority"] == "high":
            high_priority_tickets += 1

    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content={
            "message": "statistics calculated",
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": closed_tickets,
            "urgent_tickets": urgent_tickets,
            "high_priority_tickets": high_priority_tickets,
        },
    )


@app.get(
    "/tickets/statistics/categories",
    tags=["Statistics"],
    summary="Return the number of tickets for each category",
)
def get_ticket_statistics_by_category():
    print("/tickets/statistics/categories api is called")
    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    category_counts = {}
    for ticket in tickets:
        ticket_category = ticket["category"]
        if ticket_category in category_counts:
            category_counts[ticket_category] += 1
        else:
            category_counts[ticket_category] = 1

    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content=category_counts,
    )


@app.get(
    "/tickets/high-priority",
    tags=["Tickets"],
    summary="Retrieve all high-priority support tickets",
)
def get_high_priority_tickets():
    print("/tickets/high-priority api is called")
    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    high_priority_tickets = []
    for ticket in tickets:
        if ticket["priority"] == "high" or ticket["priority"] == "urgent":
            high_priority_tickets.append(ticket)

    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content={
            "message": "high priority tickets found",
            "tickets": high_priority_tickets,
        },
    )


@app.get(
    "/tickets/{ticket_id}",
    tags=["Tickets"],
    summary="Retrieve a single support ticket",
)
def get_ticket(ticket_id: int):
    print(f"/tickets/{ticket_id} api is called")
    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    for ticket in tickets:
        if ticket["id"] == ticket_id:
            print("ticket found")
            return JSONResponse(
                status_code=http_status.HTTP_200_OK,
                content={
                    "message": "ticket found",
                    "ticket": ticket,
                },
            )

    print("ticket does not exist")
    return JSONResponse(
        status_code=http_status.HTTP_404_NOT_FOUND,
        content={
            "message": "ticket not found",
        },
    )


@app.post(
    "/tickets",
    tags=["Tickets"],
    summary="Create a new customer support ticket",
)
def create_ticket(ticket: TicketInput):
    print("/tickets post api is called")
    print(ticket)

    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    if tickets:
        new_id = tickets[-1]["id"] + 1
    else:
        new_id = 1

    new_ticket = ticket.model_dump(mode="json")
    new_ticket["id"] = new_id
    new_ticket["status"] = "open"
    new_ticket["created_at"] = datetime.now().replace(microsecond=0).isoformat()

    tickets.append(new_ticket)

    file_write_ok, write_message = write_tickets_json_file(tickets)
    if not file_write_ok:
        print("file write not ok")
        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "file write issue"},
        )

    print("ticket created")
    return JSONResponse(
        status_code=http_status.HTTP_201_CREATED,
        content={
            "message": "ticket created",
            "ticket": new_ticket,
        },
    )


@app.put(
    "/tickets",
    tags=["Tickets"],
    summary="Replace an existing support ticket",
)
def replace_ticket(ticket: TicketPutInput):
    print("/tickets put api is called")
    print(ticket)

    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    ticket_found = False
    updated_ticket = None
    for index in range(len(tickets)):
        if tickets[index]["id"] == ticket.id:
            print("ticket found for put")
            ticket_found = True
            created_at = tickets[index]["created_at"]
            updated_ticket = ticket.model_dump(mode="json")
            updated_ticket["created_at"] = created_at
            tickets[index] = updated_ticket
            break

    if not ticket_found:
        print("ticket does not exist")
        return JSONResponse(
            status_code=http_status.HTTP_404_NOT_FOUND,
            content={"message": "ticket not found"},
        )

    file_write_ok, write_message = write_tickets_json_file(tickets)
    if not file_write_ok:
        print("file write not ok")
        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "file write issue"},
        )

    print("ticket replaced")
    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content={
            "message": "ticket replaced",
            "ticket": updated_ticket,
        },
    )


@app.patch(
    "/tickets",
    tags=["Tickets"],
    summary="Partially update an existing support ticket",
)
def update_ticket(ticket: TicketPatchInput):
    print("/tickets patch api is called")
    print(ticket)

    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    ticket_found = False
    updated_ticket = None
    for index in range(len(tickets)):
        if tickets[index]["id"] == ticket.id:
            print("ticket found for patch")
            ticket_found = True
            updated_ticket = tickets[index]
            updates = ticket.model_dump(mode="json", exclude_unset=True)
            for key in updates:
                if key != "id":
                    updated_ticket[key] = updates[key]
            tickets[index] = updated_ticket
            break

    if not ticket_found:
        print("ticket does not exist")
        return JSONResponse(
            status_code=http_status.HTTP_404_NOT_FOUND,
            content={"message": "ticket not found"},
        )

    file_write_ok, write_message = write_tickets_json_file(tickets)
    if not file_write_ok:
        print("file write not ok")
        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "file write issue"},
        )

    print("ticket updated")
    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content={
            "message": "ticket updated",
            "ticket": updated_ticket,
        },
    )


@app.get(
    "/customers/{customer_name}/tickets",
    tags=["Customers"],
    summary="Retrieve all tickets belonging to a specific customer",
)
def get_customer_tickets(customer_name: str):
    print(f"/customers/{customer_name}/tickets api is called")
    file_read_ok, tickets, message = read_tickets_json_file()
    if not file_read_ok:
        print("file read not ok")
        return file_error_response(message)

    customer_tickets = []
    for ticket in tickets:
        if ticket["customer_name"].lower() == customer_name.lower():
            customer_tickets.append(ticket)

    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content={
            "message": "customer tickets found",
            "tickets": customer_tickets,
        },
    )

from pydantic import BaseModel, EmailStr


class TicketInput(BaseModel):
    customer_name: str
    email: EmailStr
    subject: str
    description: str
    category: str
    priority: str


class TicketPutInput(BaseModel):
    id: int
    customer_name: str
    email: EmailStr
    subject: str
    description: str
    category: str
    priority: str
    status: str


class TicketPatchInput(BaseModel):
    id: int
    customer_name: str | None = None
    email: EmailStr | None = None
    subject: str | None = None
    description: str | None = None
    category: str | None = None
    priority: str | None = None
    status: str | None = None

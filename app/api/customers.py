from fastapi import APIRouter
from fastapi import status
from pydantic import BaseModel
from pydantic import Field

from database.operations import create_customer


router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


class CustomerCreateRequest(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=50,
    )

    last_name: str = Field(
        min_length=1,
        max_length=50,
    )


class CustomerCreatedResponse(BaseModel):
    customer_id: int
    first_name: str
    last_name: str


@router.post(
    "",
    response_model=CustomerCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_endpoint(
    request: CustomerCreateRequest,
):
    customer = create_customer(
        first_name=request.first_name,
        last_name=request.last_name,
    )

    return CustomerCreatedResponse(
        customer_id=customer[0],
        first_name=request.first_name,
        last_name=request.last_name,
    )
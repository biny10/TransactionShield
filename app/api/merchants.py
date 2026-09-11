from fastapi import APIRouter
from fastapi import status
from pydantic import BaseModel
from pydantic import Field

from database.operations import create_merchant


router = APIRouter(
    prefix="/merchants",
    tags=["merchants"],
)


class MerchantCreateRequest(BaseModel):
    merchant_code: str = Field(
        min_length=1,
        max_length=20,
    )


class MerchantCreatedResponse(BaseModel):
    merchant_id: int
    merchant_code: str


@router.post(
    "",
    response_model=MerchantCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_merchant_endpoint(
    request: MerchantCreateRequest,
):
    merchant = create_merchant(
        merchant_code=request.merchant_code,
    )

    return MerchantCreatedResponse(
        merchant_id=merchant[0],
        merchant_code=request.merchant_code,
    )
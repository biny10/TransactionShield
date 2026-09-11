from decimal import Decimal

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from pydantic import Field

from app.services.transaction_service import (
    cash_in,
    cash_out,
    make_payment,
    debit_account,
    transfer_money,
)
from datetime import datetime

from database.connection import get_connection

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
)
class CashInRequest(BaseModel):
    account_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)
class DebitRequest(BaseModel):
    account_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)

    destination_code: str = Field(
        default="EXTERNAL_DEBIT",
        min_length=1,
        max_length=20,
    )

class PaymentRequest(BaseModel):
    account_id: int = Field(gt=0)
    merchant_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)

class TransferRequest(BaseModel):
    sender_account_id: int = Field(gt=0)
    receiver_account_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)

class CashOutRequest(BaseModel):
    account_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)

class TransactionCreatedResponse(BaseModel):
    transaction_id: int


@router.post(
    "/transfer",
    response_model=TransactionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)

def create_transfer(
    request: TransferRequest,
):
    try:
        transaction_id = transfer_money(
            sender_account_id=(
                request.sender_account_id
            ),
            receiver_account_id=(
                request.receiver_account_id
            ),
            amount=request.amount,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return TransactionCreatedResponse(
        transaction_id=transaction_id,
    )

class TransactionDetailResponse(BaseModel):
    transaction_id: int
    transaction_type: str
    amount: Decimal
    transaction_status: str

    origin_account_id: int | None
    destination_account_id: int | None
    merchant_id: int | None

    fraud_probability: Decimal | None
    predicted_fraud: bool | None
    model_version: str | None

    created_at: datetime

@router.post(
    "/cash-out",
    response_model=TransactionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cash_out(
    request: CashOutRequest,
):
    try:
        transaction_id = cash_out(
            account_id=request.account_id,
            amount=request.amount,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return TransactionCreatedResponse(
        transaction_id=transaction_id,
    )
@router.post(
    "/payment",
    response_model=TransactionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    request: PaymentRequest,
):
    try:
        transaction_id = make_payment(
            account_id=request.account_id,
            merchant_id=request.merchant_id,
            amount=request.amount,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return TransactionCreatedResponse(
        transaction_id=transaction_id,
    )
@router.post(
    "/debit",
    response_model=TransactionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_debit(
    request: DebitRequest,
):
    try:
        transaction_id = debit_account(
            account_id=request.account_id,
            amount=request.amount,
            destination_code=(
                request.destination_code
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return TransactionCreatedResponse(
        transaction_id=transaction_id,
    )
@router.post(
    "/cash-in",
    response_model=TransactionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cash_in(
    request: CashInRequest,
):
    try:
        transaction_id = cash_in(
            account_id=request.account_id,
            amount=request.amount,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return TransactionCreatedResponse(
        transaction_id=transaction_id,
    )
@router.get(
    "/{transaction_id}",
    response_model=TransactionDetailResponse,
)
def get_transaction(transaction_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    t.transaction_id,
                    t.transaction_type,
                    t.amount,
                    t.transaction_status,
                    t.origin_account_id,
                    t.destination_account_id,
                    t.merchant_id,
                    fp.fraud_probability,
                    fp.predicted_fraud,
                    fp.model_version,
                    t.created_at
                FROM transactions AS t
                LEFT JOIN fraud_predictions AS fp
                    ON fp.transaction_id =
                        t.transaction_id
                WHERE t.transaction_id = %s
                ORDER BY fp.created_at DESC NULLS LAST
                LIMIT 1;
                """,
                (transaction_id,),
            )

            transaction = cursor.fetchone()

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return TransactionDetailResponse(
        transaction_id=transaction[0],
        transaction_type=transaction[1],
        amount=transaction[2],
        transaction_status=transaction[3],
        origin_account_id=transaction[4],
        destination_account_id=transaction[5],
        merchant_id=transaction[6],
        fraud_probability=transaction[7],
        predicted_fraud=transaction[8],
        model_version=transaction[9],
        created_at=transaction[10],
    )
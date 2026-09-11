from decimal import Decimal
from typing import Literal

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from pydantic import Field
from fastapi import Query

from database.operations import create_account

from datetime import datetime

from database.connection import get_connection

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)


class AccountCreateRequest(BaseModel):
    customer_id: int = Field(gt=0)

    account_type: Literal[
        "checking",
        "savings",
    ]

    starting_balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )


class AccountCreatedResponse(BaseModel):
    account_id: int
    customer_id: int
    account_type: str
    balance: Decimal


@router.post(
    "",
    response_model=AccountCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account_endpoint(
    request: AccountCreateRequest,
):
    try:
        account = create_account(
            customer_id=request.customer_id,
            account_type=request.account_type,
            starting_balance=(
                request.starting_balance
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return AccountCreatedResponse(
        account_id=account[0],
        customer_id=request.customer_id,
        account_type=request.account_type,
        balance=request.starting_balance,
    )
class AccountDetailResponse(BaseModel):
    account_id: int
    customer_id: int
    account_type: str
    balance: Decimal
    interest_rate: Decimal
    account_status: str
    created_at: datetime

@router.get(
    "/{account_id}",
    response_model=AccountDetailResponse,
)
def get_account(account_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    account_id,
                    customer_id,
                    account_type,
                    balance,
                    interest_rate,
                    account_status,
                    created_at
                FROM accounts
                WHERE account_id = %s;
                """,
                (account_id,),
            )

            account = cursor.fetchone()

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return AccountDetailResponse(
        account_id=account[0],
        customer_id=account[1],
        account_type=account[2],
        balance=account[3],
        interest_rate=account[4],
        account_status=account[5],
        created_at=account[6],
    )   

class AccountTransactionResponse(BaseModel):
    transaction_id: int
    transaction_type: str
    amount: Decimal
    direction: str
    transaction_status: str
    predicted_fraud: bool | None
    created_at: datetime


@router.get(
    "/{account_id}/transactions",
    response_model=list[AccountTransactionResponse],
)
def get_account_transactions(
    account_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM accounts
                WHERE account_id = %s;
                """,
                (account_id,),
            )

            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail="Account not found",
                )

            cursor.execute(
                """
                SELECT
                    t.transaction_id,
                    t.transaction_type,
                    t.amount,
                    CASE
                        WHEN (
                            t.transaction_type =
                                'CASH_IN'
                        )
                        THEN 'incoming'

                        WHEN (
                            t.destination_account_id =
                                %s
                        )
                        THEN 'incoming'

                        ELSE 'outgoing'
                    END AS direction,
                    t.transaction_status,
                    prediction.predicted_fraud,
                    t.created_at
                FROM transactions AS t

                LEFT JOIN LATERAL (
                    SELECT
                        fp.predicted_fraud
                    FROM fraud_predictions AS fp
                    WHERE fp.transaction_id =
                        t.transaction_id
                    ORDER BY fp.created_at DESC
                    LIMIT 1
                ) AS prediction
                    ON TRUE

                WHERE (
                    t.origin_account_id = %s
                    OR t.destination_account_id = %s
                )

                ORDER BY t.created_at DESC
                LIMIT %s;
                """,
                (
                    account_id,
                    account_id,
                    account_id,
                    limit,
                ),
            )

            transactions = cursor.fetchall()

    return [
        AccountTransactionResponse(
            transaction_id=row[0],
            transaction_type=row[1],
            amount=row[2],
            direction=row[3],
            transaction_status=row[4],
            predicted_fraud=row[5],
            created_at=row[6],
        )
        for row in transactions
    ]

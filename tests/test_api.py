from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "TransactionShield",
    }


def test_transfer_returns_transaction_id():
    with patch(
        "app.api.transactions.transfer_money",
        return_value=12345,
    ):
        response = client.post(
            "/transactions/transfer",
            json={
                "sender_account_id": 1,
                "receiver_account_id": 2,
                "amount": 25.00,
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "transaction_id": 12345,
    }


def test_transfer_service_error_becomes_400():
    with patch(
        "app.api.transactions.transfer_money",
        side_effect=ValueError(
            "Insufficient funds"
        ),
    ):
        response = client.post(
            "/transactions/transfer",
            json={
                "sender_account_id": 1,
                "receiver_account_id": 2,
                "amount": 500.00,
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Insufficient funds",
    }


def test_transfer_rejects_zero_amount():
    response = client.post(
        "/transactions/transfer",
        json={
            "sender_account_id": 1,
            "receiver_account_id": 2,
            "amount": 0,
        },
    )

    assert response.status_code == 422
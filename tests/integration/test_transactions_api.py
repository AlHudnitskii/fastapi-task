"""Integration tests for Transactions API endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.models.enums import CurrencyEnumDB, TransactionStatusEnumDB, UserStatusEnumDB


class TestTransactionsAPI:
    """Test suite for Transactions API endpoints."""

    def test_create_deposit_transaction_success(self, client: TestClient) -> None:
        """Test successful deposit transaction creation via API."""
        user_response = client.post("/users", json={"email": "deposit_api@example.com"})
        user_id = user_response.json()["id"]

        response = client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("100.50"))},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user_id
        assert data["currency"] == CurrencyEnumDB.USD
        assert Decimal(data["amount"]) == Decimal("100.50")
        assert data["status"] == TransactionStatusEnumDB.POSTED

    def test_create_withdrawal_transaction_success(self, client: TestClient) -> None:
        """Test successful withdrawal transaction creation via API."""
        user_response = client.post("/users", json={"email": "withdraw_api@example.com"})
        user_id = user_response.json()["id"]

        client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("200"))},
        )

        response = client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("-50.25"))},
        )

        assert response.status_code == 201
        data = response.json()
        assert Decimal(data["amount"]) == Decimal("-50.25")

    def test_create_transaction_user_not_found(self, client: TestClient) -> None:
        """Test creating transaction for non-existent user returns 404."""
        response = client.post(
            "/transactions/users/99999",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("100"))},
        )

        assert response.status_code == 404

    def test_create_transaction_user_blocked(self, client: TestClient) -> None:
        """Test creating transaction for blocked user returns 403."""
        user_response = client.post("/users", json={"email": "blocked_transaction@example.com"})
        user_id = user_response.json()["id"]
        client.patch(f"/users/{user_id}", json={"status": UserStatusEnumDB.BLOCKED})

        response = client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("100"))},
        )

        assert response.status_code == 403
        assert "blocked" in response.json()["detail"].lower()

    def test_create_transaction_negative_balance(self, client: TestClient) -> None:
        """Test creating transaction that would result in negative balance returns 400."""
        user_response = client.post("/users", json={"email": "negative_balance@example.com"})
        user_id = user_response.json()["id"]

        response = client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("-100"))},
        )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower() or "balance" in response.json()["detail"].lower()

    def test_get_transactions_all(self, client: TestClient) -> None:
        """Test getting all transactions."""
        user1_response = client.post("/users", json={"email": "user1_tx@example.com"})
        user2_response = client.post("/users", json={"email": "user2_tx@example.com"})

        client.post(
            f"/transactions/users/{user1_response.json()['id']}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("100"))},
        )
        client.post(
            f"/transactions/users/{user2_response.json()['id']}",
            json={"currency": CurrencyEnumDB.EUR, "amount": str(Decimal("50"))},
        )

        response = client.get("/transactions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_transactions_filter_by_user(self, client: TestClient) -> None:
        """Test getting transactions filtered by user."""
        user1_response = client.post("/users", json={"email": "filter_user1@example.com"})
        user2_response = client.post("/users", json={"email": "filter_user2@example.com"})

        user1_id = user1_response.json()["id"]
        user2_id = user2_response.json()["id"]

        client.post(
            f"/transactions/users/{user1_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("100"))},
        )
        client.post(
            f"/transactions/users/{user2_id}",
            json={"currency": CurrencyEnumDB.EUR, "amount": str(Decimal("50"))},
        )

        response = client.get(f"/transactions?user_id={user1_id}")

        assert response.status_code == 200
        data = response.json()
        assert all(tx["user_id"] == user1_id for tx in data)

    def test_get_transactions_pagination(self, client: TestClient) -> None:
        """Test getting transactions with pagination."""
        user_response = client.post("/users", json={"email": "pagination@example.com"})
        user_id = user_response.json()["id"]

        for i in range(5):
            client.post(
                f"/transactions/users/{user_id}",
                json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("10"))},
            )

        response = client.get("/transactions?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_rollback_transaction_success(self, client: TestClient) -> None:
        """Test successful transaction rollback via API."""
        user_response = client.post("/users", json={"email": "rollback_api@example.com"})
        user_id = user_response.json()["id"]

        tx_response = client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("100"))},
        )
        transaction_id = tx_response.json()["id"]

        response = client.patch(f"/transactions/users/{user_id}/transactions/{transaction_id}/rollback")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == TransactionStatusEnumDB.REVERSED
        assert data["id"] == transaction_id

    def test_rollback_transaction_user_not_found(self, client: TestClient) -> None:
        """Test rolling back transaction for non-existent user returns 404."""
        response = client.patch("/transactions/users/99999/transactions/1/rollback")

        assert response.status_code == 404

    def test_rollback_transaction_not_found(self, client: TestClient) -> None:
        """Test rolling back non-existent transaction returns 404."""
        user_response = client.post("/users", json={"email": "notfound_rollback@example.com"})
        user_id = user_response.json()["id"]

        response = client.patch(f"/transactions/users/{user_id}/transactions/99999/rollback")

        assert response.status_code == 404

    def test_rollback_transaction_wrong_user(self, client: TestClient) -> None:
        """Test rolling back transaction that doesn't belong to user returns 403."""
        user1_response = client.post("/users", json={"email": "user1_rollback@example.com"})
        user2_response = client.post("/users", json={"email": "user2_rollback@example.com"})

        user1_id = user1_response.json()["id"]
        user2_id = user2_response.json()["id"]

        tx_response = client.post(
            f"/transactions/users/{user1_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("100"))},
        )
        transaction_id = tx_response.json()["id"]

        response = client.patch(f"/transactions/users/{user2_id}/transactions/{transaction_id}/rollback")

        assert response.status_code == 403

    def test_rollback_transaction_already_rollbacked(self, client: TestClient) -> None:
        """Test rolling back already rollbacked transaction returns 400."""
        user_response = client.post("/users", json={"email": "doublerollback_api@example.com"})
        user_id = user_response.json()["id"]

        tx_response = client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal("100"))},
        )
        transaction_id = tx_response.json()["id"]

        client.patch(f"/transactions/users/{user_id}/transactions/{transaction_id}/rollback")

        response = client.patch(f"/transactions/users/{user_id}/transactions/{transaction_id}/rollback")

        assert response.status_code == 400
        assert "already reversed" in response.json()["detail"].lower()

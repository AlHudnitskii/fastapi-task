"""Integration tests for Reports API endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.models.enums import CurrencyEnumDB


class TestReportsAPI:
    """Test suite for Reports API endpoints."""

    def test_get_weekly_report_success(self, client: TestClient) -> None:
        """Test getting weekly report via API."""
        response = client.get("/reports/weekly?weeks=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_weekly_report_with_transactions(self, client: TestClient) -> None:
        """Test getting weekly report with transactions."""
        user_response = client.post("/users", json={"email": "report_user@example.com"})
        user_id = user_response.json()["id"]

        client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.USD, "amount": str(Decimal(100))},
        )
        client.post(
            f"/transactions/users/{user_id}",
            json={"currency": CurrencyEnumDB.EUR, "amount": str(Decimal(50))},
        )

        response = client.get("/reports/weekly?weeks=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_weekly_report_multiple_weeks(self, client: TestClient) -> None:
        """Test getting weekly report for multiple weeks."""
        response = client.get("/reports/weekly?weeks=4")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data

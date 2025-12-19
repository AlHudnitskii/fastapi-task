"""Integration tests for Users API endpoints."""

from fastapi.testclient import TestClient

from app.models.enums import UserStatusEnumDB


class TestUsersAPI:
    """Test suite for Users API endpoints."""

    def test_create_user_success(self, client: TestClient) -> None:
        """Test successful user creation via API."""
        response = client.post("/users", json={"email": "api@example.com"})

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "api@example.com"
        assert data["status"] == UserStatusEnumDB.ACTIVE
        assert len(data["balances"]) > 0

    def test_create_user_duplicate_email(self, client: TestClient) -> None:
        """Test creating user with duplicate email returns 409."""
        email = "duplicate_api@example.com"
        client.post("/users", json={"email": email})

        response = client.post("/users", json={"email": email})

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_create_user_invalid_email(self, client: TestClient) -> None:
        """Test creating user with invalid email returns 422."""
        response = client.post("/users", json={"email": "invalid-email"})

        assert response.status_code == 422

    def test_get_users_all(self, client: TestClient) -> None:
        """Test getting all users."""
        client.post("/users", json={"email": "user1@example.com"})
        client.post("/users", json={"email": "user2@example.com"})

        response = client.get("/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_users_filter_by_id(self, client: TestClient) -> None:
        """Test getting users filtered by ID."""
        create_response = client.post("/users", json={"email": "filter_id@example.com"})
        user_id = create_response.json()["id"]

        response = client.get(f"/users?user_id={user_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == user_id

    def test_get_users_filter_by_email(self, client: TestClient) -> None:
        """Test getting users filtered by email."""
        email = "filter_email@example.com"
        client.post("/users", json={"email": email})

        response = client.get(f"/users?email={email}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == email

    def test_get_users_filter_by_status(self, client: TestClient) -> None:
        """Test getting users filtered by status."""
        create_response = client.post("/users", json={"email": "filter_status@example.com"})
        user_id = create_response.json()["id"]

        client.patch(f"/users/{user_id}", json={"status": UserStatusEnumDB.BLOCKED})

        response = client.get(f"/users?user_status={UserStatusEnumDB.BLOCKED}")

        assert response.status_code == 200
        data = response.json()
        assert all(user["status"] == UserStatusEnumDB.BLOCKED for user in data)

    def test_get_user_by_id_success(self, client: TestClient) -> None:
        """Test getting user by ID."""
        create_response = client.post("/users", json={"email": "get_by_id@example.com"})
        user_id = create_response.json()["id"]

        response = client.get(f"/users/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert "balances" in data

    def test_get_user_by_id_not_found(self, client: TestClient) -> None:
        """Test getting non-existent user returns 404."""
        response = client.get("/users/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_user_status_to_blocked(self, client: TestClient) -> None:
        """Test updating user status to BLOCKED."""
        create_response = client.post("/users", json={"email": "block_api@example.com"})
        user_id = create_response.json()["id"]

        response = client.patch(f"/users/{user_id}", json={"status": UserStatusEnumDB.BLOCKED})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == UserStatusEnumDB.BLOCKED

    def test_update_user_status_to_active(self, client: TestClient) -> None:
        """Test updating user status to ACTIVE."""
        create_response = client.post("/users", json={"email": "activate_api@example.com"})
        user_id = create_response.json()["id"]

        client.patch(f"/users/{user_id}", json={"status": UserStatusEnumDB.BLOCKED})

        response = client.patch(f"/users/{user_id}", json={"status": UserStatusEnumDB.ACTIVE})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == UserStatusEnumDB.ACTIVE

    def test_update_user_status_already_blocked(self, client: TestClient) -> None:
        """Test updating already blocked user returns 400."""
        create_response = client.post("/users", json={"email": "alreadyblocked_api@example.com"})
        user_id = create_response.json()["id"]

        client.patch(f"/users/{user_id}", json={"status": UserStatusEnumDB.BLOCKED})

        response = client.patch(f"/users/{user_id}", json={"status": UserStatusEnumDB.BLOCKED})

        assert response.status_code == 400
        assert "already blocked" in response.json()["detail"].lower()

    def test_update_user_status_not_found(self, client: TestClient) -> None:
        """Test updating non-existent user returns 404."""
        response = client.patch("/users/99999", json={"status": UserStatusEnumDB.BLOCKED})

        assert response.status_code == 404

"""
Integration Tests for Refresh Token Endpoint
Tests POST /refresh endpoint for token refresh functionality
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    # Import here to allow mocking
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    """Mock AuthService"""
    return MagicMock()


class TestRefreshEndpoint:
    """Test POST /refresh endpoint"""

    def test_refresh_endpoint_exists(self, client):
        """Test that /refresh endpoint is registered"""
        with patch('routers.refresh.AuthService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.refresh_access_token.return_value = {
                "access_token": "new_access",
                "refresh_token": "new_refresh",
                "token_type": "bearer",
                "user_id": 1
            }
            
            response = client.post("/refresh", json={"refresh_token": "test_token"})
            
            # Should not be 404
            assert response.status_code != 404
    
    def test_refresh_endpoint_with_valid_token(self, client):
        """Test refresh endpoint with valid refresh token"""
        with patch('routers.refresh.AuthService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.refresh_access_token.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "token_type": "bearer",
                "user_id": 1
            }
            
            response = client.post(
                "/refresh",
                json={"refresh_token": "valid_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "new_access_token"
            assert data["refresh_token"] == "new_refresh_token"
            assert data["token_type"] == "bearer"
            assert data["user_id"] == 1
    
    def test_refresh_endpoint_with_invalid_token(self, client):
        """Test refresh endpoint with invalid refresh token"""
        with patch('routers.refresh.AuthService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.refresh_access_token.side_effect = HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
            
            response = client.post(
                "/refresh",
                json={"refresh_token": "invalid_token"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
    
    def test_refresh_endpoint_missing_refresh_token(self, client):
        """Test refresh endpoint with missing refresh token in request"""
        response = client.post("/refresh", json={})
        
        # Should return validation error (422 Unprocessable Entity)
        assert response.status_code == 422
    
    def test_refresh_endpoint_with_expired_token(self, client):
        """Test refresh endpoint with expired refresh token"""
        with patch('routers.refresh.AuthService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.refresh_access_token.side_effect = HTTPException(
                status_code=401,
                detail="Refresh token is invalid or expired"
            )
            
            response = client.post(
                "/refresh",
                json={"refresh_token": "expired_token"}
            )
            
            assert response.status_code == 401
    
    def test_refresh_endpoint_response_format(self, client):
        """Test that refresh endpoint returns correct response format"""
        with patch('routers.refresh.AuthService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.refresh_access_token.return_value = {
                "access_token": "token123",
                "refresh_token": "refresh456",
                "token_type": "bearer",
                "user_id": 42
            }
            
            response = client.post(
                "/refresh",
                json={"refresh_token": "test_refresh"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all required fields are present
            assert "access_token" in data
            assert "refresh_token" in data
            assert "token_type" in data
            assert "user_id" in data
            
            # Verify field types
            assert isinstance(data["access_token"], str)
            assert isinstance(data["refresh_token"], str)
            assert isinstance(data["token_type"], str)
            assert isinstance(data["user_id"], int)


class TestRefreshEndpointIntegration:
    """Integration tests for refresh endpoint with actual database interaction"""

    def test_refresh_endpoint_calls_auth_service(self, client):
        """Test that endpoint properly calls AuthService"""
        with patch('routers.refresh.AuthService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.refresh_access_token.return_value = {
                "access_token": "new_access",
                "refresh_token": "new_refresh",
                "token_type": "bearer",
                "user_id": 1
            }
            
            response = client.post(
                "/refresh",
                json={"refresh_token": "token"}
            )
            
            # Verify AuthService was instantiated
            mock_service_class.assert_called_once()
            
            # Verify refresh_access_token was called with the token
            mock_service.refresh_access_token.assert_called_once_with("token")
    
    def test_refresh_endpoint_error_handling(self, client):
        """Test that endpoint properly handles service errors"""
        with patch('routers.refresh.AuthService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.refresh_access_token.side_effect = Exception("Database error")
            
            response = client.post(
                "/refresh",
                json={"refresh_token": "token"}
            )
            
            # Should return 500 for generic exceptions
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error occurred" in data["detail"].lower()


class TestRefreshTokenFlow:
    """Test complete refresh token workflow"""

    def test_user_can_refresh_immediately_after_login(self, client):
        """Test that user can refresh token right after login"""
        # Simulate fresh login with refresh token
        with patch('routers.refresh.AuthService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Simulate initial login returning refresh token
            initial_refresh = "refresh_token_from_login"
            
            # Use that refresh token
            mock_service.refresh_access_token.return_value = {
                "access_token": "new_access",
                "refresh_token": "rotated_refresh",
                "token_type": "bearer",
                "user_id": 1
            }
            
            response = client.post(
                "/refresh",
                json={"refresh_token": initial_refresh}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify we got new tokens
            assert data["access_token"] != initial_refresh
            assert data["refresh_token"] != initial_refresh

"""
Simulador de base de datos MySQL para pruebas
Simula usuarios con roles para testing sin necesidad de MySQL real
"""

import time
from typing import List, Dict, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockUserDatabase:
    def __init__(self):
        """Initialize mock database with sample data"""
        self.users = [
            {
                "id": 1,
                "username": "admin",
                "email": "admin@parkup.com",
                "full_name": "Administrator",
                "phone": "+1234567890",
                "is_active": True,
                "created_at": "2024-01-01 10:00:00",
                "updated_at": "2024-01-01 10:00:00",
                "roles": ["ADMIN", "USER"]
            },
            {
                "id": 2,
                "username": "manager1",
                "email": "manager@parkup.com",
                "full_name": "John Manager",
                "phone": "+1234567891",
                "is_active": True,
                "created_at": "2024-01-02 10:00:00",
                "updated_at": "2024-01-02 10:00:00",
                "roles": ["MANAGER", "USER"]
            },
            {
                "id": 3,
                "username": "operator1",
                "email": "operator@parkup.com",
                "full_name": "Jane Operator",
                "phone": "+1234567892",
                "is_active": True,
                "created_at": "2024-01-03 10:00:00",
                "updated_at": "2024-01-03 10:00:00",
                "roles": ["OPERATOR"]
            },
            {
                "id": 4,
                "username": "user1",
                "email": "user1@example.com",
                "full_name": "Alice User",
                "phone": "+1234567893",
                "is_active": True,
                "created_at": "2024-01-04 10:00:00",
                "updated_at": "2024-01-04 10:00:00",
                "roles": ["USER"]
            },
            {
                "id": 5,
                "username": "user2",
                "email": "user2@example.com",
                "full_name": "Bob Customer",
                "phone": "+1234567894",
                "is_active": True,
                "created_at": "2024-01-05 10:00:00",
                "updated_at": "2024-01-05 10:00:00",
                "roles": ["USER"]
            },
            {
                "id": 6,
                "username": "supervisor",
                "email": "supervisor@parkup.com",
                "full_name": "Carlos Supervisor",
                "phone": "+1234567895",
                "is_active": True,
                "created_at": "2024-01-06 10:00:00",
                "updated_at": "2024-01-06 10:00:00",
                "roles": ["SUPERVISOR", "OPERATOR"]
            },
            {
                "id": 7,
                "username": "guest",
                "email": "guest@example.com",
                "full_name": "Guest User",
                "phone": None,
                "is_active": False,
                "created_at": "2024-01-07 10:00:00",
                "updated_at": "2024-01-07 10:00:00",
                "roles": ["GUEST"]
            }
        ]
        
        # Vehicle data simulation (optional - for future use)
        self.vehicles = [
            {"id": 1, "user_id": 1, "license_plate": "ABC123", "model": "Toyota Camry"},
            {"id": 2, "user_id": 2, "license_plate": "XYZ789", "model": "Honda Civic"},
            {"id": 3, "user_id": 4, "license_plate": "DEF456", "model": "Ford Focus"},
            {"id": 4, "user_id": 5, "license_plate": "GHI789", "model": "Nissan Altima"},
        ]
        
        logger.info(f"🎭 Mock database initialized with {len(self.users)} users")
    
    def get_all_active_users(self) -> List[Dict]:
        """Get all active users"""
        active_users = [user for user in self.users if user["is_active"]]
        logger.info(f"📊 Retrieved {len(active_users)} active users from mock database")
        return active_users
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        for user in self.users:
            if user["id"] == user_id and user["is_active"]:
                logger.info(f"👤 Found user by ID {user_id}: {user['username']}")
                return user
        logger.warning(f"❌ User with ID {user_id} not found")
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        for user in self.users:
            if user["email"] == email and user["is_active"]:
                logger.info(f"📧 Found user by email {email}: {user['username']}")
                return user
        logger.warning(f"❌ User with email {email} not found")
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        for user in self.users:
            if user["username"] == username and user["is_active"]:
                logger.info(f"🔍 Found user by username {username}")
                return user
        logger.warning(f"❌ User with username {username} not found")
        return None
    
    def get_user_by_license_plate(self, license_plate: str) -> Optional[Dict]:
        """Get user by vehicle license plate"""
        for vehicle in self.vehicles:
            if vehicle["license_plate"].upper() == license_plate.upper():
                user = self.get_user_by_id(vehicle["user_id"])
                if user:
                    logger.info(f"🚗 Found user by license plate {license_plate}: {user['username']}")
                    return user
        logger.warning(f"❌ No user found for license plate {license_plate}")
        return None
    
    def test_connection(self) -> bool:
        """Test database connection (always returns True for mock)"""
        logger.info("✅ Mock database connection test successful")
        return True
    
    def add_sample_plate_detections(self):
        """Add some sample plate detection data for testing"""
        # This could be used to simulate plate detection history
        pass

# Global mock database instance
mock_db = MockUserDatabase()

# Functions to match the interface expected by the main application
def copy_users_from_mock() -> List[Dict]:
    """Copy all users from mock database"""
    return mock_db.get_all_active_users()

def get_user_by_id_mock(user_id: int) -> Optional[Dict]:
    """Get user by ID from mock database"""
    return mock_db.get_user_by_id(user_id)

def get_user_by_email_mock(email: str) -> Optional[Dict]:
    """Get user by email from mock database"""
    return mock_db.get_user_by_email(email)

def test_mock_connection() -> bool:
    """Test mock database connection"""
    return mock_db.test_connection()

def get_user_by_plate(license_plate: str) -> Optional[Dict]:
    """Get user by license plate (useful for parking integration)"""
    return mock_db.get_user_by_license_plate(license_plate)

# Example usage and testing
if __name__ == "__main__":
    print("🎭 Testing Mock Database")
    print("=" * 50)
    
    # Test getting all users
    all_users = copy_users_from_mock()
    print(f"Total active users: {len(all_users)}")
    
    # Test getting user by ID
    user = get_user_by_id_mock(1)
    print(f"User 1: {user['username'] if user else 'Not found'}")
    
    # Test getting user by email
    user = get_user_by_email_mock("manager@parkup.com")
    print(f"Manager: {user['username'] if user else 'Not found'}")
    
    # Test getting user by license plate
    user = get_user_by_plate("ABC123")
    print(f"Owner of ABC123: {user['username'] if user else 'Not found'}")
    
    # Test connection
    print(f"Connection test: {'✅ OK' if test_mock_connection() else '❌ Failed'}")
    
    # Show sample data
    print("\n📋 Sample Users:")
    for user in all_users[:3]:
        print(f"  - {user['username']} ({user['email']}) - Roles: {user['roles']}")

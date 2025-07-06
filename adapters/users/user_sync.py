import os
import requests
import pymysql
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from typing import List, Dict, Optional
import logging

load_dotenv()

# Configuration from environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "park_up")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserSynchronizer:
    def __init__(self):
        self.mysql_connection_string = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        self.engine = None
        self.users_cache = []
        
    def connect_to_mysql(self):
        """Establish connection to MySQL database"""
        try:
            self.engine = create_engine(self.mysql_connection_string)
            # Test connection
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("✅ Successfully connected to MySQL database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MySQL: {str(e)}")
            return False
    
    def copy_users_from_mysql(self) -> List[Dict]:
        """Copy all users from MySQL database"""
        if not self.engine:
            if not self.connect_to_mysql():
                return []
        
        try:
            with self.engine.connect() as connection:
                # Query to get users with their roles
                query = text("""
                    SELECT 
                        u.id,
                        u.username,
                        u.email,
                        u.full_name,
                        u.phone,
                        u.is_active,
                        u.created_at,
                        u.updated_at,
                        GROUP_CONCAT(r.role_name) as roles
                    FROM users u 
                    LEFT JOIN user_roles ur ON u.id = ur.user_id
                    LEFT JOIN roles r ON ur.role_id = r.id
                    WHERE u.is_active = 1
                    GROUP BY u.id, u.username, u.email, u.full_name, u.phone, u.is_active, u.created_at, u.updated_at
                """)
                
                result = connection.execute(query)
                users = []
                
                for row in result:
                    # Parse roles - convert comma-separated string to list
                    roles_str = row.roles if row.roles else ""
                    roles_list = [role.strip() for role in roles_str.split(",")] if roles_str else ["user"]
                    
                    user = {
                        "id": row.id,
                        "username": row.username,
                        "email": row.email,
                        "full_name": row.full_name,
                        "phone": row.phone,
                        "is_active": row.is_active,
                        "created_at": str(row.created_at),
                        "updated_at": str(row.updated_at),
                        "roles": roles_list
                    }
                    users.append(user)
                
                self.users_cache = users
                logger.info(f"✅ Successfully copied {len(users)} users from MySQL")
                return users
                
        except Exception as e:
            logger.error(f"❌ Error copying users from MySQL: {str(e)}")
            # Fallback to simple query if the complex one fails
            try:
                with self.engine.connect() as connection:
                    simple_query = text("""
                        SELECT 
                            id,
                            username,
                            email,
                            full_name,
                            phone,
                            is_active,
                            created_at,
                            updated_at,
                            'user' as role
                        FROM users 
                        WHERE is_active = 1
                    """)
                    
                    result = connection.execute(simple_query)
                    users = []
                    
                    for row in result:
                        user = {
                            "id": row.id,
                            "username": row.username,
                            "email": row.email,
                            "full_name": row.full_name,
                            "phone": row.phone,
                            "is_active": row.is_active,
                            "created_at": str(row.created_at),
                            "updated_at": str(row.updated_at),
                            "roles": [row.role]  # Default role as list
                        }
                        users.append(user)
                    
                    self.users_cache = users
                    logger.info(f"✅ Successfully copied {len(users)} users from MySQL (simple query)")
                    return users
                    
            except Exception as e2:
                logger.error(f"❌ Error with fallback query: {str(e2)}")
                return []
    
    def sync_users_to_backend(self, users: List[Dict]) -> bool:
        """Send users to backend for synchronization"""
        if not users:
            logger.warning("⚠️ No users to sync")
            return False
        
        try:
            # Transform users to match Java backend UserResource format
            backend_users = []
            for user in users:
                backend_user = {
                    "id": user["id"],
                    "username": user["username"],
                    "roles": user.get("roles", ["user"])  # Ensure roles is a list
                }
                backend_users.append(backend_user)
            
            # Send users to backend
            response = requests.post(
                f"{BACKEND_URL}/api/users/sync",
                json={"users": backend_users},
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Successfully synced {len(backend_users)} users to backend")
                return True
            else:
                logger.error(f"❌ Backend sync failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"❌ Error syncing users to backend: {str(e)}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get specific user by ID from cache or database"""
        # First check cache
        for user in self.users_cache:
            if user["id"] == user_id:
                return user
        
        # If not in cache, query database
        if not self.engine:
            if not self.connect_to_mysql():
                return None
        
        try:
            with self.engine.connect() as connection:
                query = text("SELECT * FROM users WHERE id = :user_id AND is_active = 1")
                result = connection.execute(query, {"user_id": user_id})
                row = result.fetchone()
                
                if row:
                    # Get roles for this user
                    roles_query = text("""
                        SELECT r.role_name 
                        FROM user_roles ur 
                        JOIN roles r ON ur.role_id = r.id 
                        WHERE ur.user_id = :user_id
                    """)
                    roles_result = connection.execute(roles_query, {"user_id": user_id})
                    roles = [role.role_name for role in roles_result.fetchall()]
                    if not roles:
                        roles = ["user"]  # Default role
                    
                    user = {
                        "id": row.id,
                        "username": row.username,
                        "email": row.email,
                        "full_name": row.full_name,
                        "phone": row.phone,
                        "is_active": row.is_active,
                        "created_at": str(row.created_at),
                        "updated_at": str(row.updated_at),
                        "roles": roles
                    }
                    return user
                
        except Exception as e:
            logger.error(f"❌ Error getting user by ID: {str(e)}")
        
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get specific user by email from cache or database"""
        # First check cache
        for user in self.users_cache:
            if user["email"] == email:
                return user
        
        # If not in cache, query database
        if not self.engine:
            if not self.connect_to_mysql():
                return None
        
        try:
            with self.engine.connect() as connection:
                query = text("SELECT * FROM users WHERE email = :email AND is_active = 1")
                result = connection.execute(query, {"email": email})
                row = result.fetchone()
                
                if row:
                    # Get roles for this user
                    roles_query = text("""
                        SELECT r.role_name 
                        FROM user_roles ur 
                        JOIN roles r ON ur.role_id = r.id 
                        WHERE ur.user_id = :user_id
                    """)
                    roles_result = connection.execute(roles_query, {"user_id": row.id})
                    roles = [role.role_name for role in roles_result.fetchall()]
                    if not roles:
                        roles = ["user"]  # Default role
                    
                    user = {
                        "id": row.id,
                        "username": row.username,
                        "email": row.email,
                        "full_name": row.full_name,
                        "phone": row.phone,
                        "is_active": row.is_active,
                        "created_at": str(row.created_at),
                        "updated_at": str(row.updated_at),
                        "roles": roles
                    }
                    return user
                
        except Exception as e:
            logger.error(f"❌ Error getting user by email: {str(e)}")
        
        return None
    
    def full_sync(self) -> Dict:
        """Perform a full user synchronization"""
        logger.info("🔄 Starting full user synchronization...")
        
        # Step 1: Copy users from MySQL
        users = self.copy_users_from_mysql()
        
        if not users:
            return {
                "success": False,
                "message": "Failed to copy users from MySQL",
                "users_count": 0
            }
        
        # Step 2: Sync to backend
        sync_success = self.sync_users_to_backend(users)
        
        return {
            "success": sync_success,
            "message": f"Synchronized {len(users)} users" if sync_success else "Failed to sync users to backend",
            "users_count": len(users),
            "users": users if sync_success else []
        }

# Global instance
user_synchronizer = UserSynchronizer()

def copy_users() -> Dict:
    """Main function to copy users from MySQL"""
    return user_synchronizer.full_sync()

def get_cached_users() -> List[Dict]:
    """Get cached users"""
    return user_synchronizer.users_cache

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    return user_synchronizer.get_user_by_id(user_id)

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    return user_synchronizer.get_user_by_email(email)

def test_mysql_connection() -> bool:
    """Test MySQL connection"""
    return user_synchronizer.connect_to_mysql()

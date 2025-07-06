# User Synchronization Documentation

## Overview

The edge node includes user synchronization functionality that connects to a MySQL database to copy user information and sync it with the Java backend system. The system is compatible with the Java backend `UserResource(Long id, String username, List<String> roles)` interface.

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=park_up

# Backend Configuration
BACKEND_URL=http://localhost:8000
```

### Database Schema

The system expects the following database structure to support the Java backend UserResource format:

```sql
-- Users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Roles table
CREATE TABLE roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Roles junction table (many-to-many)
CREATE TABLE user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_role (user_id, role_id)
);
```

**Note:** You can use the provided `database_schema.sql` file to create the complete database structure.

## API Endpoints

### 1. Test MySQL Connection
```http
GET /edge/users/test/mysql
```
Tests the connection to the MySQL database.

**Response:**
```json
{
    "success": true,
    "message": "MySQL connection successful"
}
```

### 2. Sync Users from MySQL
```http
POST /edge/users/sync
Content-Type: application/json

{
    "force_sync": true
}
```

Synchronizes users from MySQL to the edge node cache and backend.

**Parameters:**
- `force_sync` (boolean): If true, forces a fresh sync. If false, uses cached data if available.

**Response:**
```json
{
    "success": true,
    "message": "Synchronized 50 users",
    "users_count": 50,
    "users": [...]
}
```

### 3. Get Cached Users
```http
GET /edge/users/cached
```

Returns all users currently cached in the edge node.

**Response:**
```json
{
    "success": true,
    "users_count": 50,
    "users": [
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "phone": "+1234567890",
            "is_active": true,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00",
            "roles": ["USER", "MANAGER"]
        }
    ]
}
```

### 4. Get User by ID
```http
GET /edge/users/{user_id}
```

Retrieves a specific user by their ID. Returns only the fields compatible with Java UserResource.

**Response:**
```json
{
    "id": 1,
    "username": "john_doe",
    "roles": ["USER", "MANAGER"]
}
```

### 5. Get User by Email
```http
GET /edge/users/email/{email}
```

Retrieves a specific user by their email address. Returns only the fields compatible with Java UserResource.

**Response:**
```json
{
    "id": 1,
    "username": "john_doe",
    "roles": ["USER", "MANAGER"]
}
```

## Usage Examples

### Basic User Sync Workflow

1. **Test Connection:**
```bash
curl http://localhost:8000/edge/users/test/mysql
```

2. **Sync Users:**
```bash
curl -X POST http://localhost:8000/edge/users/sync \
     -H "Content-Type: application/json" \
     -d '{"force_sync": true}'
```

3. **Get Cached Users:**
```bash
curl http://localhost:8000/edge/users/cached
```

### Integration with Plate Recognition

When a license plate is detected, you can now:

1. Look up the vehicle owner by license plate
2. Get user information from the cached users
3. Log parking events with user details
4. Send notifications to specific users

### Error Handling

The system includes comprehensive error handling:

- **Database Connection Errors**: Logged and returned in API responses
- **Invalid User Queries**: Return 404 status codes
- **Sync Failures**: Detailed error messages in responses

## Security Considerations

1. **Database Credentials**: Store MySQL credentials securely in environment variables
2. **Network Security**: Ensure MySQL server is properly secured
3. **Data Privacy**: User data is cached temporarily and should be handled according to privacy policies

## Troubleshooting

### Common Issues

1. **MySQL Connection Failed**
   - Check database credentials in `.env` file
   - Verify MySQL server is running
   - Check network connectivity

2. **No Users Found**
   - Verify users table exists and has data
   - Check `is_active` column values
   - Review database schema compatibility

3. **Backend Sync Failed**
   - Check backend URL configuration
   - Verify backend `/api/users/sync` endpoint exists
   - Check network connectivity to backend

### Logs

The system uses Python logging. Check console output for detailed information:

```
✅ Successfully connected to MySQL database
✅ Successfully copied 50 users from MySQL
✅ Successfully synced 50 users to backend
```

## Performance Considerations

- Users are cached in memory for fast access
- Database queries are optimized with indexes
- Sync operations can handle large user datasets
- Background sync can be implemented for automatic updates

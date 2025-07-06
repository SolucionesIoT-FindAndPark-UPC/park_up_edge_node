-- Database schema for user synchronization
-- Compatible with Java backend UserResource(Long id, String username, List<String> roles)

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_roles junction table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_role (user_id, role_id)
);

-- Insert default roles
INSERT IGNORE INTO roles (role_name, description) VALUES 
('ADMIN', 'Administrator with full access'),
('USER', 'Regular user with limited access'),
('MANAGER', 'Manager with extended permissions'),
('OPERATOR', 'Parking operator');

-- Example: Insert sample users
INSERT IGNORE INTO users (username, email, full_name, phone) VALUES 
('admin', 'admin@parkup.com', 'System Administrator', '+1234567890'),
('user1', 'user1@example.com', 'John Doe', '+1234567891'),
('manager1', 'manager@parkup.com', 'Jane Manager', '+1234567892');

-- Example: Assign roles to users
-- Get user and role IDs and assign them
INSERT IGNORE INTO user_roles (user_id, role_id) 
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'admin' AND r.role_name = 'ADMIN';

INSERT IGNORE INTO user_roles (user_id, role_id) 
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'user1' AND r.role_name = 'USER';

INSERT IGNORE INTO user_roles (user_id, role_id) 
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'manager1' AND r.role_name = 'MANAGER';

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- View to easily see users with their roles
CREATE OR REPLACE VIEW user_roles_view AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.phone,
    u.is_active,
    u.created_at,
    u.updated_at,
    GROUP_CONCAT(r.role_name ORDER BY r.role_name) as roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.is_active = 1
GROUP BY u.id, u.username, u.email, u.full_name, u.phone, u.is_active, u.created_at, u.updated_at;

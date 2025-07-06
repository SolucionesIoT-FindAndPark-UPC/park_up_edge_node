#!/usr/bin/env python3
"""
Script de debugging para verificar el mock database
Resuelve problema de código 400 en búsqueda por ID
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from adapters.users.mock_user_database import (
    copy_users_from_mock,
    get_user_by_id_mock,
    get_user_by_email_mock,
    test_mock_connection,
    get_user_by_plate,
    mock_db
)

def test_mock_functions():
    """Test all mock database functions directly"""
    print("🔧 DEBUGGING MOCK DATABASE FUNCTIONS")
    print("=" * 50)
    
    # Test 1: Connection
    print("\n1. Testing mock connection...")
    try:
        result = test_mock_connection()
        print(f"✅ Connection: {result}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Test 2: Copy all users
    print("\n2. Testing copy_users_from_mock()...")
    try:
        users = copy_users_from_mock()
        print(f"✅ Users copied: {len(users)}")
        for user in users[:3]:  # Show first 3
            print(f"   - ID {user['id']}: {user['username']} ({user['email']})")
    except Exception as e:
        print(f"❌ Copy users error: {e}")
    
    # Test 3: Get user by ID
    print("\n3. Testing get_user_by_id_mock()...")
    test_ids = [1, 2, 4, 999]
    for user_id in test_ids:
        try:
            user = get_user_by_id_mock(user_id)
            if user:
                print(f"✅ ID {user_id}: {user['username']} - {user['roles']}")
            else:
                print(f"❌ ID {user_id}: Not found")
        except Exception as e:
            print(f"❌ ID {user_id} error: {e}")
    
    # Test 4: Get user by email
    print("\n4. Testing get_user_by_email_mock()...")
    test_emails = ["admin@parkup.com", "manager@parkup.com", "noexiste@test.com"]
    for email in test_emails:
        try:
            user = get_user_by_email_mock(email)
            if user:
                print(f"✅ Email {email}: {user['username']}")
            else:
                print(f"❌ Email {email}: Not found")
        except Exception as e:
            print(f"❌ Email {email} error: {e}")
    
    # Test 5: Get user by plate
    print("\n5. Testing get_user_by_plate()...")
    test_plates = ["ABC123", "XYZ789", "UNKNOWN999"]
    for plate in test_plates:
        try:
            user = get_user_by_plate(plate)
            if user:
                print(f"✅ Plate {plate}: {user['username']}")
            else:
                print(f"❌ Plate {plate}: Not found")
        except Exception as e:
            print(f"❌ Plate {plate} error: {e}")
    
    # Test 6: Direct access to mock_db
    print("\n6. Testing direct mock_db access...")
    try:
        print(f"✅ Total users in mock_db: {len(mock_db.users)}")
        print(f"✅ Total vehicles in mock_db: {len(mock_db.vehicles)}")
        
        # Show user structure
        if mock_db.users:
            first_user = mock_db.users[0]
            print(f"✅ First user structure: {list(first_user.keys())}")
            print(f"   - ID: {first_user['id']}")
            print(f"   - Username: {first_user['username']}")
            print(f"   - Roles: {first_user['roles']}")
            print(f"   - Active: {first_user['is_active']}")
            
    except Exception as e:
        print(f"❌ Direct access error: {e}")

def test_hybrid_function():
    """Test the hybrid function from main.py"""
    print("\n\n🔧 TESTING HYBRID FUNCTION")
    print("=" * 50)
    
    # Import the hybrid function
    try:
        # We'll simulate it here since it's in main.py
        def get_user_hybrid_local(user_id=None, email=None, use_mock=True):
            if use_mock:
                try:
                    if user_id:
                        return get_user_by_id_mock(user_id)
                    elif email:
                        return get_user_by_email_mock(email)
                except Exception as e:
                    print(f"Mock failed: {e}")
            return None
        
        # Test hybrid function
        test_cases = [
            (1, None, "admin"),
            (2, None, "manager1"),
            (None, "admin@parkup.com", "admin"),
            (999, None, None),  # Should not be found
        ]
        
        for user_id, email, expected in test_cases:
            try:
                user = get_user_hybrid_local(user_id=user_id, email=email, use_mock=True)
                if user and expected:
                    actual = user['username']
                    success = actual == expected
                    print(f"{'✅' if success else '❌'} Hybrid test (ID:{user_id}, Email:{email}): {actual}")
                elif not user and not expected:
                    print(f"✅ Hybrid test (ID:{user_id}, Email:{email}): Not found (expected)")
                else:
                    print(f"❌ Hybrid test (ID:{user_id}, Email:{email}): Unexpected result")
            except Exception as e:
                print(f"❌ Hybrid test error: {e}")
                
    except Exception as e:
        print(f"❌ Hybrid function error: {e}")

def verify_user_structure():
    """Verify that users have the correct structure for the API"""
    print("\n\n🔧 VERIFYING USER STRUCTURE")
    print("=" * 50)
    
    try:
        users = copy_users_from_mock()
        if not users:
            print("❌ No users found")
            return
        
        # Check first user structure
        user = users[0]
        required_fields = ['id', 'username', 'roles']
        optional_fields = ['email', 'full_name', 'phone', 'is_active', 'created_at', 'updated_at']
        
        print(f"Checking user: {user.get('username', 'Unknown')}")
        
        # Check required fields
        for field in required_fields:
            if field in user:
                print(f"✅ Required field '{field}': {user[field]}")
            else:
                print(f"❌ Missing required field '{field}'")
        
        # Check optional fields
        for field in optional_fields:
            if field in user:
                print(f"✅ Optional field '{field}': {user[field]}")
            else:
                print(f"⚠️  Optional field '{field}': Not present")
        
        # Check roles format
        roles = user.get('roles', [])
        if isinstance(roles, list):
            print(f"✅ Roles are list: {roles}")
        else:
            print(f"❌ Roles are not list: {type(roles)} - {roles}")
            
    except Exception as e:
        print(f"❌ Structure verification error: {e}")

if __name__ == "__main__":
    print("🚀 MOCK DATABASE DEBUGGING SCRIPT")
    print("🎯 Resolving Code 400 issue in user search")
    
    try:
        test_mock_functions()
        test_hybrid_function()
        verify_user_structure()
        
        print("\n\n🎉 DEBUGGING COMPLETED")
        print("If all tests pass, the mock database should work correctly.")
        print("\nNext steps:")
        print("1. Start the server: uvicorn main:app --reload")
        print("2. Test endpoint: GET http://localhost:8000/edge/users/1")
        print("3. Check server logs for any errors")
        
    except Exception as e:
        print(f"\n❌ DEBUGGING FAILED: {e}")
        print("Check the mock database implementation.")
        sys.exit(1)

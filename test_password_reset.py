#!/usr/bin/env python3
"""
Simple test script to verify password reset functionality works correctly.
"""

from werkzeug.security import generate_password_hash, check_password_hash

def test_password_hashing():
    """Test that password hashing and verification works correctly"""
    
    # Test password
    test_password = "mypassword123"
    
    # Hash the password
    password_hash = generate_password_hash(test_password)
    print(f"Original password: {test_password}")
    print(f"Hashed password: {password_hash}")
    
    # Verify the password
    is_valid = check_password_hash(password_hash, test_password)
    print(f"Password verification: {is_valid}")
    
    # Test with wrong password
    wrong_password = "wrongpassword"
    is_invalid = check_password_hash(password_hash, wrong_password)
    print(f"Wrong password verification: {is_invalid}")
    
    if is_valid and not is_invalid:
        print("✅ Password hashing and verification works correctly!")
        return True
    else:
        print("❌ Password hashing or verification failed!")
        return False

if __name__ == '__main__':
    test_password_hashing()


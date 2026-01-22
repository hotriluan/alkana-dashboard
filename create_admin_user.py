#!/usr/bin/env python3
"""
Create Admin User Script

Creates default admin user: admin/admin123
Run on production server after database import.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.connection import get_db_session
from src.db.auth_models import User, Role
import bcrypt


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_admin_user():
    """Create default admin user if not exists."""
    with get_db_session() as db:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("✓ Admin user already exists")
            print(f"  Username: {admin.username}")
            print(f"  Email: {admin.email}")
            print(f"  Active: {admin.is_active}")
            return
        
        # Create admin role if not exists
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if not admin_role:
            admin_role = Role(
                name="Admin",
                description="Full system access"
            )
            db.add(admin_role)
            db.commit()
            print("✓ Created Admin role")
        
        # Create admin user
        hashed_pwd = hash_password("admin123")
        admin_user = User(
            username="admin",
            email="admin@alkana.com",
            hashed_password=hashed_pwd,
            full_name="System Administrator",
            is_active=True
        )
        admin_user.roles.append(admin_role)
        
        db.add(admin_user)
        db.commit()
        
        print("✓ Admin user created successfully!")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Email: admin@alkana.com")
        print("\n⚠️  Please change password after first login!")


if __name__ == "__main__":
    try:
        create_admin_user()
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

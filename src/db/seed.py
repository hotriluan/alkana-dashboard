"""
Seed Database with Initial Data

Creates default roles, permissions, and admin user.
Run: python -m src.db.seed

Follows CLAUDE.md: KISS principle, clear structure.
"""
from sqlalchemy.orm import Session
import bcrypt

from src.db.connection import SessionLocal, engine
from src.db.auth_models import User, Role, Permission, Base


def hash_password(password: str) -> str:
    """Hash password with bcrypt (cost=12)"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def seed_permissions(db: Session):
    """Create default permissions"""
    permissions_data = [
        # Dashboard permissions
        {"resource": "dashboards", "action": "read", "description": "View dashboards"},
        {"resource": "dashboards", "action": "write", "description": "Edit dashboard settings"},
        
        # Alert permissions
        {"resource": "alerts", "action": "read", "description": "View alerts"},
        {"resource": "alerts", "action": "manage", "description": "Acknowledge/resolve alerts"},
        
        # Export permissions
        {"resource": "exports", "action": "create", "description": "Export data to Excel"},
        
        # User management
        {"resource": "users", "action": "read", "description": "View users"},
        {"resource": "users", "action": "manage", "description": "Create/edit/delete users"},
        
        # System
        {"resource": "system", "action": "admin", "description": "Full system access"},
    ]
    
    created = []
    for perm_data in permissions_data:
        # Check if exists
        existing = db.query(Permission).filter(
            Permission.resource == perm_data["resource"],
            Permission.action == perm_data["action"]
        ).first()
        
        if not existing:
            perm = Permission(**perm_data)
            db.add(perm)
            created.append(f"{perm_data['resource']}:{perm_data['action']}")
    
    db.commit()
    return created


def seed_roles(db: Session):
    """Create default roles with permissions"""
    # Get permissions
    perms = {
        f"{p.resource}:{p.action}": p 
        for p in db.query(Permission).all()
    }
    
    roles_data = [
        {
            "name": "admin",
            "description": "Full system access",
            "permissions": list(perms.values())  # All permissions
        },
        {
            "name": "analyst",
            "description": "Read/write dashboards, manage alerts",
            "permissions": [
                perms.get("dashboards:read"),
                perms.get("dashboards:write"),
                perms.get("alerts:read"),
                perms.get("alerts:manage"),
                perms.get("exports:create"),
            ]
        },
        {
            "name": "viewer",
            "description": "Read-only access",
            "permissions": [
                perms.get("dashboards:read"),
                perms.get("alerts:read"),
            ]
        }
    ]
    
    created = []
    for role_data in roles_data:
        # Check if exists
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        
        if not existing:
            permissions = [p for p in role_data["permissions"] if p is not None]
            role = Role(
                name=role_data["name"],
                description=role_data["description"]
            )
            role.permissions = permissions
            db.add(role)
            created.append(role_data["name"])
    
    db.commit()
    return created


def seed_admin_user(db: Session):
    """Create default admin user"""
    # Check if admin exists
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        return None
    
    # Get admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        raise Exception("Admin role not found. Run seed_roles first.")
    
    # Create admin user (password max 72 bytes for bcrypt)
    password = "admin123"
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    
    admin_user = User(
        username="admin",
        email="admin@alkana.local",
        hashed_password=hash_password(password),
        full_name="System Administrator",
        is_active=True
    )
    admin_user.roles.append(admin_role)
    
    db.add(admin_user)
    db.commit()
    
    return "admin"


def seed_all():
    """Run all seed operations"""
    print("\n" + "="*60)
    print("SEEDING DATABASE")
    print("="*60)
    
    # Create tables if not exist
    print("\n📋 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("  ✓ Tables ready")
    
    db = SessionLocal()
    
    try:
        # Seed permissions
        print("\n🔐 Seeding permissions...")
        created_perms = seed_permissions(db)
        if created_perms:
            for perm in created_perms:
                print(f"  ✓ {perm}")
        else:
            print("  ⚠ All permissions already exist")
        
        # Seed roles
        print("\n👥 Seeding roles...")
        created_roles = seed_roles(db)
        if created_roles:
            for role in created_roles:
                print(f"  ✓ {role}")
        else:
            print("  ⚠ All roles already exist")
        
        # Seed admin user
        print("\n👤 Seeding admin user...")
        admin = seed_admin_user(db)
        if admin:
            print(f"  ✓ Created user: {admin}")
            print(f"  ℹ Default password: admin123")
            print(f"  ⚠ CHANGE PASSWORD IN PRODUCTION!")
        else:
            print("  ⚠ Admin user already exists")
        
        print("\n" + "="*60)
        print("✓ SEEDING COMPLETE")
        print("="*60)
        print("\nDefault Login:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    seed_all()

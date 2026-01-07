"""
User Authentication Models

Provides User, Role, Permission models for RBAC.
Follows CLAUDE.md: KISS, DRY, file <200 lines
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    ForeignKey, Table
)
from sqlalchemy.orm import relationship
from src.db.connection import Base


# Association table for many-to-many User-Role
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many Role-Permission
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    """
    User account for dashboard access.
    
    Password hashed with bcrypt (cost=12).
    JWT tokens expire in 8 hours.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    def __repr__(self):
        return f"<User {self.username}>"


class Role(Base):
    """
    Role for RBAC.
    
    Default roles:
    - admin: Full access
    - analyst: Read/write dashboards
    - viewer: Read-only
    """
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base):
    """
    Fine-grained permissions.
    
    Format: resource:action
    Examples:
    - dashboards:read
    - dashboards:write
    - alerts:manage
    - exports:create
    """
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    resource = Column(String(50), nullable=False)  # dashboards, alerts, exports
    action = Column(String(50), nullable=False)    # read, write, manage
    description = Column(String(200))
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission {self.resource}:{self.action}>"

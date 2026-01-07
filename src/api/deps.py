"""
FastAPI Dependencies

Provides DB session and authentication dependencies.
Follows CLAUDE.md: Clean dependency injection.
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.auth_models import User
from src.api.auth import verify_token


# OAuth2 scheme for JWT tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    
    Yields:
        SQLAlchemy session
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
    
    Returns:
        User object
    
    Raises:
        HTTPException: 401 if invalid credentials
    
    Usage:
        @app.get("/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    username = verify_token(token)
    if username is None:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def require_permission(resource: str, action: str):
    """
    Permission check dependency factory.
    
    Args:
        resource: Resource name (dashboards, alerts, etc.)
        action: Action name (read, write, manage)
    
    Returns:
        Dependency function
    
    Usage:
        @app.get("/admin")
        def admin_panel(
            user: User = Depends(require_permission("system", "admin"))
        ):
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Check if user has required permission
        for role in current_user.roles:
            for perm in role.permissions:
                if perm.resource == resource and perm.action == action:
                    return current_user
                # Admin has all permissions
                if perm.resource == "system" and perm.action == "admin":
                    return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {resource}:{action}"
        )
    
    return permission_checker

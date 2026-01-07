# Security Guide

Security best practices and guidelines for the Alkana Dashboard.

## Table of Contents

- [Overview](#overview)
- [Authentication & Authorization](#authentication--authorization)
- [Credential Management](#credential-management)
- [Database Security](#database-security)
- [API Security](#api-security)
- [Frontend Security](#frontend-security)
- [Infrastructure Security](#infrastructure-security)
- [Security Audit Checklist](#security-audit-checklist)
- [Incident Response](#incident-response)
- [Compliance](#compliance)

## Overview

### Security Principles

1. **Defense in Depth** - Multiple layers of security controls
2. **Least Privilege** - Minimum necessary access rights
3. **Secure by Default** - Security-first configuration
4. **Regular Updates** - Keep dependencies current
5. **Audit Everything** - Comprehensive logging

### Threat Model

**Primary Threats:**
- Unauthorized data access
- SQL injection attacks
- Cross-site scripting (XSS)
- Cross-site request forgery (CSRF)
- Man-in-the-middle attacks
- Credential theft
- Denial of service (DoS)

**Assets to Protect:**
- Customer financial data (AR aging)
- Sales performance data
- Production metrics
- User credentials
- Database access

## Authentication & Authorization

### JWT Token Security

**Configuration** (`.env`):

```bash
# Strong secret key (min 32 characters)
SECRET_KEY=your-very-long-and-random-secret-key-here-min-32-chars

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS=7     # 1 week

# Algorithm
ALGORITHM=HS256
```

**Generate secure secret key:**

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

**Token implementation** (`backend/app/core/security.py`):

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())  # Unique token ID
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### Password Policy

**Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

**Validation** (`backend/app/schemas/auth.py`):

```python
import re
from pydantic import validator

class UserCreate(BaseModel):
    username: str
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain a number')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        
        return v
```

### Role-Based Access Control (RBAC)

**User roles:**

```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"           # Full access
    MANAGER = "manager"       # Read + Export
    VIEWER = "viewer"         # Read only
```

**Permission decorator:**

```python
from fastapi import HTTPException, Depends

def require_role(allowed_roles: list[UserRole]):
    def decorator(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        return current_user
    return decorator

# Usage
@router.get("/admin/users")
async def list_users(
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    # Only admins can access
    pass
```

### Session Management

**Logout/token revocation:**

```python
# Store revoked tokens (use Redis in production)
revoked_tokens = set()

def revoke_token(token: str):
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    jti = payload.get("jti")
    revoked_tokens.add(jti)

def is_token_revoked(token: str) -> bool:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    jti = payload.get("jti")
    return jti in revoked_tokens
```

## Credential Management

### Environment Variables

**DO NOT commit secrets to git:**

```bash
# .gitignore
.env
.env.local
.env.production
*.key
*.pem
```

**Use environment variables:**

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str
    CORS_ORIGINS: list[str]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Secrets Management (Production)

**Options:**

1. **AWS Secrets Manager**
   ```python
   import boto3
   
   def get_secret(secret_name):
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId=secret_name)
       return response['SecretString']
   ```

2. **HashiCorp Vault**
   ```python
   import hvac
   
   client = hvac.Client(url='https://vault.example.com')
   secret = client.secrets.kv.v2.read_secret_version(path='alkana/db')
   db_password = secret['data']['data']['password']
   ```

3. **Azure Key Vault**
   ```python
   from azure.keyvault.secrets import SecretClient
   from azure.identity import DefaultAzureCredential
   
   credential = DefaultAzureCredential()
   client = SecretClient(vault_url="https://myvault.vault.azure.net/", credential=credential)
   secret = client.get_secret("db-password")
   ```

### Database Credentials

**Separate users for different access levels:**

```sql
-- Read-only user for reporting
CREATE USER dashboard_readonly WITH PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE alkana_dashboard TO dashboard_readonly;
GRANT USAGE ON SCHEMA public TO dashboard_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dashboard_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO dashboard_readonly;

-- Application user (read/write)
CREATE USER dashboard_app WITH PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE alkana_dashboard TO dashboard_app;
GRANT USAGE, CREATE ON SCHEMA public TO dashboard_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dashboard_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO dashboard_app;

-- Admin user (DDL operations)
CREATE USER dashboard_admin WITH PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE alkana_dashboard TO dashboard_admin;
```

## Database Security

### SQL Injection Prevention

**Always use parameterized queries:**

✅ **SAFE** (SQLAlchemy ORM):
```python
# ORM query (safe)
batches = db.query(ProductionChain).filter(
    ProductionChain.batch_id == batch_id
).all()

# Raw query with parameters (safe)
result = db.execute(
    text("SELECT * FROM production_chain WHERE batch_id = :batch_id"),
    {"batch_id": batch_id}
)
```

❌ **UNSAFE** (String concatenation):
```python
# NEVER DO THIS!
query = f"SELECT * FROM production_chain WHERE batch_id = '{batch_id}'"
result = db.execute(text(query))
```

### Connection Security

**SSL/TLS for database connections:**

```python
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/alkana_dashboard?sslmode=require

# For self-signed certificates
DATABASE_URL=postgresql://user:password@localhost:5432/alkana_dashboard?sslmode=verify-ca&sslrootcert=/path/to/ca.crt
```

**Connection pooling limits:**

```python
# backend/app/db/session.py
from sqlalchemy import create_engine

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,          # Max connections
    max_overflow=20,       # Additional connections
    pool_timeout=30,       # Connection timeout
    pool_pre_ping=True,    # Verify connection before use
    echo=False
)
```

### Database Encryption

**Encrypt sensitive columns:**

```python
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    
    # Encrypted field
    email = Column(
        EncryptedType(String, settings.SECRET_KEY, AesEngine, 'pkcs5')
    )
```

**Encrypt backups:**

```bash
# Encrypted backup
pg_dump alkana_dashboard | gpg --encrypt --recipient admin@yourcompany.com > backup.sql.gpg

# Decrypt restore
gpg --decrypt backup.sql.gpg | psql alkana_dashboard
```

## API Security

### CORS Configuration

**Restrictive CORS settings:**

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dashboard.yourcompany.com",  # Production
        "http://localhost:5173"                # Development only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600
)
```

### Rate Limiting

**Prevent abuse with rate limiting:**

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@router.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(request: Request, credentials: LoginRequest):
    # Login logic
    pass

@router.get("/inventory")
@limiter.limit("100/minute")  # Max 100 requests per minute
async def get_inventory(request: Request):
    # Inventory logic
    pass
```

### Input Validation

**Validate all inputs with Pydantic:**

```python
from pydantic import BaseModel, validator, Field
from datetime import date

class InventoryQuery(BaseModel):
    material_id: str = Field(..., max_length=18)
    start_date: date
    end_date: date
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    @validator('material_id')
    def valid_material_format(cls, v):
        if not v.isalnum():
            raise ValueError('material_id must be alphanumeric')
        return v
```

### Security Headers

**Add security headers:**

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["dashboard.yourcompany.com", "localhost"]
)

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response
```

## Frontend Security

### XSS Prevention

**React automatically escapes content, but be careful with:**

❌ **Dangerous:**
```typescript
// NEVER use dangerouslySetInnerHTML with user input
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

✅ **Safe:**
```typescript
// React automatically escapes
<div>{userInput}</div>
```

### Token Storage

**Store JWT securely:**

```typescript
// services/auth.ts

// ✅ GOOD: Use httpOnly cookies (if backend supports)
// Set via backend: Set-Cookie: token=...; HttpOnly; Secure; SameSite=Strict

// ⚠️ ACCEPTABLE: localStorage (client-side apps)
export const setToken = (token: string) => {
  localStorage.setItem('token', token);
};

export const getToken = (): string | null => {
  return localStorage.getItem('token');
};

export const removeToken = () => {
  localStorage.removeItem('token');
};

// ❌ NEVER: Global variables or sessionStorage for sensitive tokens
```

### CSRF Protection

**Include CSRF token in state-changing requests:**

```typescript
// Add to axios config
axios.defaults.headers.common['X-CSRF-Token'] = getCsrfToken();

// Backend validates CSRF token
from fastapi_csrf_protect import CsrfProtect

@router.post("/update-profile")
async def update_profile(
    request: Request,
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    # Update logic
```

### Content Security Policy

**Strict CSP for frontend:**

```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy" 
      content="
        default-src 'self';
        script-src 'self';
        style-src 'self' 'unsafe-inline';
        img-src 'self' data: https:;
        font-src 'self';
        connect-src 'self' https://api.dashboard.yourcompany.com;
        frame-ancestors 'none';
      ">
```

## Infrastructure Security

### HTTPS/TLS

**Always use HTTPS in production:**

**nginx configuration:**

```nginx
server {
    listen 443 ssl http2;
    server_name dashboard.yourcompany.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/dashboard.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.yourcompany.com/privkey.pem;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name dashboard.yourcompany.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Configuration

**Restrict access to database:**

```bash
# Allow only application server
sudo ufw allow from 10.0.1.10 to any port 5432

# Block all other database access
sudo ufw deny 5432
```

### Docker Security

**Non-root user in containers:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Read-only filesystem:**

```yaml
# docker-compose.yml
services:
  backend:
    image: alkana-dashboard-backend
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

## Security Audit Checklist

### Pre-Production Checklist

- [ ] All secrets removed from git history
- [ ] Strong `SECRET_KEY` configured
- [ ] HTTPS enabled with valid certificate
- [ ] CORS configured for production domains only
- [ ] Rate limiting enabled on sensitive endpoints
- [ ] Database uses SSL/TLS connections
- [ ] Separate database users with least privilege
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS prevention tested
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Password policy enforced
- [ ] Audit logging enabled
- [ ] Regular dependency updates scheduled
- [ ] Backup encryption enabled
- [ ] Firewall rules configured
- [ ] Non-root Docker users
- [ ] Security monitoring enabled

### Regular Security Tasks

**Weekly:**
- Review access logs for anomalies
- Check failed login attempts

**Monthly:**
- Update dependencies (`pip list --outdated`)
- Review user permissions
- Test backup restoration

**Quarterly:**
- Full security audit
- Penetration testing
- Dependency vulnerability scan

## Incident Response

### Security Incident Procedure

1. **Detect** - Identify security incident
2. **Contain** - Isolate affected systems
3. **Investigate** - Determine scope and impact
4. **Eradicate** - Remove threat
5. **Recover** - Restore normal operations
6. **Review** - Post-incident analysis

### Breach Response

**Immediate actions:**

1. **Isolate system:**
   ```bash
   # Stop application
   docker-compose down
   
   # Block network access
   sudo ufw deny from any to any
   ```

2. **Revoke all tokens:**
   ```python
   # Invalidate all existing tokens
   revoked_tokens.clear()
   
   # Force password reset
   UPDATE users SET must_reset_password = TRUE;
   ```

3. **Rotate secrets:**
   ```bash
   # Generate new SECRET_KEY
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Update .env and restart
   ```

4. **Audit logs:**
   ```bash
   # Check access logs
   grep -i "POST /login" /var/log/nginx/access.log
   
   # Check database connections
   SELECT * FROM pg_stat_activity;
   ```

5. **Notify stakeholders:**
   - Management
   - Affected users
   - Compliance team (if required)

## Compliance

### Data Privacy

**GDPR considerations:**
- User consent for data collection
- Right to access personal data
- Right to erasure (delete account)
- Data portability
- Breach notification (72 hours)

**Implementation:**

```python
@router.delete("/users/me")
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """GDPR right to erasure"""
    
    # Anonymize or delete user data
    db.query(User).filter(User.id == current_user.id).delete()
    db.commit()
    
    return {"message": "Account deleted"}
```

### Audit Logging

**Log all security-relevant events:**

```python
import logging

security_logger = logging.getLogger("security")

# Log authentication events
security_logger.info(f"Login successful: user={username}, ip={request.client.host}")
security_logger.warning(f"Login failed: user={username}, ip={request.client.host}")

# Log authorization failures
security_logger.warning(f"Unauthorized access attempt: user={username}, endpoint={request.url.path}")

# Log data access
security_logger.info(f"Data export: user={username}, table={table_name}, rows={row_count}")
```

## Related Documentation

- [API Reference](API_REFERENCE.md) - API endpoints
- [Deployment Guide](DEPLOYMENT.md) - Production setup
- [Monitoring Guide](MONITORING.md) - Security monitoring
- [Contributing Guide](CONTRIBUTING.md) - Code security standards

---

**Security is an ongoing process, not a one-time task. Stay vigilant.**

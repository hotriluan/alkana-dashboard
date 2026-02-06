# GitHub Secrets Configuration
# Add these secrets to your GitHub repository: Settings > Secrets and variables > Actions

## Required Secrets

### Server Connection
SERVER_HOST=192.168.18.35
SERVER_USER=it

### SSH Authentication
SSH_PRIVATE_KEY=
# Paste the content of your private key file (~/.ssh/alkana_deploy)
# To view: cat ~/.ssh/alkana_deploy (Linux/Mac) or Get-Content ~/.ssh/alkana_deploy (Windows)

### Database Credentials
DB_NAME=alkana_dashboard
DB_USER=alkana_user
DB_PASSWORD=
# Generate a strong password, e.g.: openssl rand -base64 32

## Optional Secrets

### Monitoring (if using)
SLACK_WEBHOOK_URL=
ALERT_EMAIL=

### SSL (if using domain)
DOMAIN=

## How to Add Secrets

1. Go to your GitHub repository
2. Click Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret above with its corresponding value

## Example: Adding SSH_PRIVATE_KEY

Windows PowerShell:
```powershell
Get-Content $env:USERPROFILE\.ssh\alkana_deploy | Set-Clipboard
# Now paste from clipboard into GitHub
```

Linux/Mac:
```bash
cat ~/.ssh/alkana_deploy
# Copy output and paste into GitHub
```

## Verify Setup

After adding all secrets, push code to trigger deployment:
```bash
git add .
git commit -m "Configure automated deployment"
git push origin main
```

Check Actions tab in GitHub to see deployment progress.

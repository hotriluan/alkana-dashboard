# Deployment Guide for Windows Users

## Recommended Approach: Use Git Bash

The easiest way to deploy on Windows is to use **Git Bash**, which comes with Git for Windows.

### Installation

1. Download and install [Git for Windows](https://git-scm.com/download/win)
2. During installation, select "Git Bash Here" context menu option

### Deployment Steps

1. Open Git Bash in your project directory:
   - Right-click in `c:\dev\alkana-dashboard` folder
   - Select "Git Bash Here"

2. Run the deployment script:
   ```bash
   bash deployment/one-click-deploy.sh
   ```

3. Follow the prompts and wait for completion

That's it! The bash script will handle everything automatically.

## Alternative: PowerShell Manual Deployment

If you cannot use Git Bash, you can use PowerShell for guided manual deployment:

```powershell
cd c:\dev\alkana-dashboard
.\deployment\one-click-deploy.ps1
```

**Note**: The PowerShell script provides step-by-step manual instructions, not full automation. For best experience, use Git Bash instead.

## Why Git Bash?

- ✅ Full automation with one command
- ✅ Better SSH/SCP support
- ✅ Bash script compatibility
- ✅ Easier debugging
- ✅ Cross-platform consistency

## Troubleshooting

### Git Bash not installed

Download from: https://git-scm.com/download/win

### SSH connection issues

Ensure the server is accessible:
```bash
ping 192.168.68.166
ssh alkana@192.168.68.166
```

### Permission denied

Check credentials in `deployment/server-config.env`:
```
SERVER_IP=192.168.68.166
SERVER_USER=alkana
SERVER_PASSWORD=alkana123
```

##Need Help?

See full documentation:
- [DEPLOY-AUTO.md](../DEPLOY-AUTO.md) - Full deployment guide
- [START-HERE.md](../START-HERE.md) - Getting started
- [DEPLOYMENT-SUMMARY.md](../DEPLOYMENT-SUMMARY.md) - Technical details

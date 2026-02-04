# Quick Fix Deployment Instructions

## Production Server Deployment

Run these commands on the production server:

```bash
cd /opt/alkana-dashboard

# Pull latest changes
sudo git pull origin main

# Rebuild and restart frontend container
sudo docker compose up -d --build frontend

# Verify containers are healthy
sudo docker compose ps
```

## What Changed

**Previous Issue:**  
- Initial fix had `left: 220px` margin and `minWidth: 600px` wrapper
- This caused ResponsiveContainer to not calculate width properly
- Charts rendered with only labels, no bars visible

**New Fix:**
- Reverted to simpler approach
- `left: 200px` margin (standard)
- `width: 180px` for YAxis (minimal needed)
- Removed `minWidth: 600px` wrapper that was breaking layout
- Removed `overflow-x-auto` container
- Height: 400px for better proportions
- Let ResponsiveContainer naturally calculate width

**Commits:**
1. **dbb6ca1** - Documentation
2. **ff5d3f1** - Simplified responsive fix (current)

## Expected Result

Charts should now:
- ✅ Display correctly at 100% zoom
- ✅ Show bars for all items
- ✅ Work at 90%, 100%, 110% zoom levels
- ✅ Render labels without cutoff
- ✅ Have proper width/height proportions

## Verification Steps

1. Pull latest on production
2. Rebuild frontend container
3. Test in browser at:
   - 90% zoom - should work
   - 100% zoom - should work (was broken before)
   - 110% zoom - should work
4. Check inventory page loads correctly
5. Verify both charts display with bars

## Rollback (if needed)

If issues persist:

```bash
# Revert to commit before changes
git revert <commit-hash>

# Rebuild
sudo docker compose up -d --build frontend
```

Latest commit hash: **ff5d3f1**
Previous commit hash: **dbb6ca1** (docs only)

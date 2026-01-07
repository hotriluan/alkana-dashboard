"""Quick test of AR aging snapshots endpoint"""
import requests

# Login
r = requests.post('http://localhost:8000/api/v1/auth/login', data={
    'username': 'admin',
    'password': 'admin123'
})
print(f"Login Status: {r.status_code}")
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    exit(1)

token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get snapshots
print('\n[1] AR Snapshots:')
r = requests.get('http://localhost:8000/api/v1/dashboards/ar-aging/snapshots', headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    snapshots = r.json()
    print(f"Snapshots count: {len(snapshots)}")
    for snap in snapshots:
        print(f"  - {snap['snapshot_date']}: {snap['row_count']} rows")
else:
    print(f"Error: {r.text}")

# Get summary (without snapshot param - should use latest)
print('\n[2] AR Summary (no snapshot param):')
r = requests.get('http://localhost:8000/api/v1/dashboards/ar-aging/summary', headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    summary = r.json()
    print(f"Total Target: {summary['total_target']:,.0f}")
    print(f"Total Realization: {summary['total_realization']:,.0f}")
    print(f"Collection Rate: {summary['collection_rate_pct']}%")
    print(f"Divisions: {len(summary.get('divisions', []))}")
    for div in summary.get('divisions', []):
        print(f"  - {div['division']}: {div['collection_rate_pct']}%")
else:
    print(f"Error: {r.text}")

# Get summary with specific snapshot
if snapshots and len(snapshots) > 0:
    snapshot_date = snapshots[0]['snapshot_date']
    print(f'\n[3] AR Summary (with snapshot={snapshot_date}):')
    r = requests.get('http://localhost:8000/api/v1/dashboards/ar-aging/summary', 
                     headers=headers, 
                     params={'snapshot_date': snapshot_date})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        summary = r.json()
        print(f"Total Target: {summary['total_target']:,.0f}")
        print(f"Total Realization: {summary['total_realization']:,.0f}")
        print(f"Collection Rate: {summary['collection_rate_pct']}%")
        print(f"Divisions: {len(summary.get('divisions', []))}")
        for div in summary.get('divisions', []):
            print(f"  - {div['division']}: {div['collection_rate_pct']}%")
    else:
        print(f"Error: {r.text}")

print('\nDone!')

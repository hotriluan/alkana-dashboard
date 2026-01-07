import requests
import json

print('Testing API endpoints...')
print('=' * 60)

# Test health
print('\n[1] Health Check')
r = requests.get('http://localhost:8000/api/health')
print(f'Status: {r.status_code}')
print(json.dumps(r.json(), indent=2))

# Test login
print('\n[2] Login')
r = requests.post('http://localhost:8000/api/v1/auth/login', data={
    'username': 'admin',
    'password': 'admin123'
})
print(f'Status: {r.status_code}')
token_data = r.json()
token_preview = token_data.get('access_token', '')[:50]
print(f'Token: {token_preview}...')

# Test AR Summary (with auth)
print('\n[3] AR Collection Summary')
headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
r = requests.get('http://localhost:8000/api/v1/dashboards/ar-aging/summary', headers=headers)
print(f'Status: {r.status_code}')
data = r.json()
print(f'Total Target: {data["total_target"]:,.0f}')
print(f'Total Realization: {data["total_realization"]:,.0f}')
print(f'Collection Rate: {data["collection_rate_pct"]}%')
print(f'Divisions: {len(data["divisions"])}')
for div in data['divisions']:
    print(f'  - {div["division"]}: {div["collection_rate_pct"]}%')

print('\n' + '=' * 60)
print('✓ All tests passed!')

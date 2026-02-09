"""
Find correct PostgreSQL user in production
"""
import subprocess

plink_path = r"C:\Program Files\PuTTY\plink.exe"

# Try common PostgreSQL users
users_to_try = [
    'postgres',
    'alkana',
    'ubuntu',
    'it',
    'admin',
    'root'
]

command = "docker exec alkana-postgres psql -U {} -d {} -t -c '\\du'"

print("🔍 Trying to find correct PostgreSQL user...\n")

# First try to see environment variables
env_cmd = "docker exec alkana-postgres env | grep -i postgres"
result = subprocess.run(
    [plink_path, "-pw", "it123", "-batch", "it@192.168.18.35", env_cmd],
    capture_output=True,
    text=True,
    timeout=15
)
print("Environment variables:")
print(result.stdout)
print()

# Check docker-compose.yml or .env files
compose_cmd = "cat /home/it/alkana-dashboard/docker-compose.yml | grep -A 5 POSTGRES"
result2 = subprocess.run(
    [plink_path, "-pw", "it123", "-batch", "it@192.168.18.35", compose_cmd],
    capture_output=True,
    text=True,
    timeout=15
)
print("Docker Compose Config:")
print(result2.stdout)
if result2.stderr:
    print("Stderr:", result2.stderr)

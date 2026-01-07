from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
inspector = inspect(engine)

print("fact_lead_time columns:")
for col in inspector.get_columns('fact_lead_time'):
    print(f"  {col['name']}: {col['type']}")

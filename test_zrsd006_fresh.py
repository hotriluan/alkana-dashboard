"""
Fresh process to reload models and test zrsd006 loader
"""
import subprocess
import sys

script = """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

sys.path.insert(0, 'src')
from src.etl.loaders import Zrsd006Loader

session = Session()
loader = Zrsd006Loader(session, mode='insert')
result = loader.load()

print(f"\\nLoaded: {result['loaded']} rows")
print(f"Errors: {result['errors']}")

if loader.errors:
    print("\\nFirst 5 errors:")
    for err in loader.errors[:5]:
        print(f"  {err}")

# Validate
from sqlalchemy import text
count = session.execute(text("SELECT COUNT(*) FROM raw_zrsd006")).scalar()
print(f"\\nraw_zrsd006 now has: {count:,} rows")

session.close()
"""

# Run in fresh Python process
result = subprocess.run([sys.executable, '-c', script], 
                       capture_output=True, text=True, cwd='.')

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

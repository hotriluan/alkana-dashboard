"""
Debug loader to see what exceptions are being raised
"""
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

from src.etl.loaders import CooispiLoader

session = Session()

loader = CooispiLoader(session, mode='insert')

# Monkey patch to print errors
original_load = loader.load

def debug_load():
    result = original_load()
    
    if loader.errors:
        print("\n❌ ERRORS FOUND:")
        print(f"Total errors: {len(loader.errors)}")
        print("\nFirst 10 errors:")
        for error in loader.errors[:10]:
            print(f"  {error}")
    
    return result

loader.load = debug_load
loader.load()

session.close()

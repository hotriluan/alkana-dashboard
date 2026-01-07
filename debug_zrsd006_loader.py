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

# Monkey patch to show errors
original_load = loader.load

def debug_load():
    result = original_load()
    
    if loader.errors:
        print(f"\nTotal errors: {len(loader.errors)}")
        print("\nFirst 10 errors:")
        for error in loader.errors[:10]:
            print(f"  {error}")
    
    return result

loader.load = debug_load
loader.load()
session.close()

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
from src.etl.transform import Transformer

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 80)
print("ALERT DETECTION BASELINE PERFORMANCE TEST (LOCAL)")
print("=" * 80)
print()

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Create transformer with session
    transform = Transformer(session)
    
    # Run alert detection (will print timing)
    transform.detect_alerts()
    
    print()
    print("Baseline measurement complete!")
    
finally:
    session.close()

print("=" * 80)

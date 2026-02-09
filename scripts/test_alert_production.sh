#!/bin/bash
# Test alert detection performance on production

echo "================================================================================  "
echo "ALERT DETECTION PERFORMANCE TEST (PRODUCTION)"
echo "================================================================================  "
echo ""

# Run Python script on production via Docker
docker exec -i alkana-backend python3 -c "
import time
from src.etl.transform import Transformer
from src.db.connection import SessionLocal

session = SessionLocal()
try:
    print('Running alert detection...')
    transform = Transformer(session)
    transform.detect_alerts()
    print('')
    print('Alert detection complete!')
finally:
    session.close()
"

echo ""
echo "================================================================================  "

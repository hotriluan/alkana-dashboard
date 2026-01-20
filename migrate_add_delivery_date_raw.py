#!/usr/bin/env python3
"""
Database Migration: Add delivery_date column to raw_zrsd004 table

Purpose: Complete OTIF implementation by adding planned delivery date to raw layer
Compliance: ClaudeKit Engineer Standards
Date: 2026-01-13
"""
import psycopg2
from src.config import DATABASE_URL

def run_migration():
    print("=" * 70)
    print("Database Migration: Add delivery_date column to raw_zrsd004")
    print("=" * 70)
    
    # Parse DATABASE_URL
    conn_params = {}
    url = DATABASE_URL.replace('postgresql://', '')
    user_pass, host_db = url.split('@')
    user, password = user_pass.split(':')
    host_port, database = host_db.split('/')
    host, port = host_port.split(':')
    
    conn_params = {
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'database': database
    }
    
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    try:
        # Check if column already exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'raw_zrsd004' 
            AND column_name = 'delivery_date'
        """)
        
        if cur.fetchone():
            print("ℹ Column delivery_date already exists in raw_zrsd004 - skipping")
        else:
            # Add column to raw_zrsd004
            cur.execute("""
                ALTER TABLE raw_zrsd004 
                ADD COLUMN delivery_date TIMESTAMP
            """)
            conn.commit()
            print("✓ Successfully added delivery_date column to raw_zrsd004")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        raise
    
    print("=" * 70)
    print("Migration completed!")

if __name__ == '__main__':
    run_migration()

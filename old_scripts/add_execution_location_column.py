import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('local.env')

def get_db_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(os.getenv('PG_DATABASE_URL'))

def add_execution_location_column():
    """Adds the execution_location column to the metadata.tool table."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            print("Checking for 'execution_location' column in 'metadata.tool' table...")
            # Check if the column already exists
            cur.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'metadata'
                  AND table_name = 'tool'
                  AND column_name = 'execution_location';
            """)
            exists = cur.fetchone()

            if exists:
                print("'execution_location' column already exists.")
            else:
                print("Column not found. Adding 'execution_location' column...")
                cur.execute("""
                    ALTER TABLE metadata.tool
                    ADD COLUMN "execution_location" TEXT;
                """)
                print("'execution_location' column added successfully.")
            
            conn.commit()
            
    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_execution_location_column() 
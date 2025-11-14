import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('local.env')

def get_db_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(os.getenv('PG_DATABASE_URL'))

def drop_execution_location_column():
    """Drops the execution_location column from the metadata.tool table if it exists."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            print("Checking for 'execution_location' column in 'metadata.tool' table...")
            # Check if the column exists
            cur.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'metadata'
                  AND table_name = 'tool'
                  AND column_name = 'execution_location';
            """)
            exists = cur.fetchone()

            if not exists:
                print("'execution_location' column does not exist. No action needed.")
            else:
                print("Column found. Dropping 'execution_location' column...")
                cur.execute("""
                    ALTER TABLE metadata.tool
                    DROP COLUMN "execution_location";
                """)
                print("'execution_location' column dropped successfully.")
            
            conn.commit()
            
    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    drop_execution_location_column() 
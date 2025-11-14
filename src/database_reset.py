"""
Database reset script for the cc Agents system.
Clears all data and reinitializes the database.
"""

import psycopg2
from dotenv import load_dotenv
from .config import get_db_connection

# Load environment variables
load_dotenv('local.env')

def reset_database():
    """Reset the database by clearing all data."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            print("🗑️  Clearing database...")
            
            # Clear all tables in reverse dependency order
            tables_to_clear = [
                "system_agent_workflow_edge",
                "system_agent_workflow_node",
                "system_agent_workflow",
                "system_agent_tool",
                "system_agent",
                "system_tool"
            ]
            
            for table in tables_to_clear:
                cur.execute(f"DELETE FROM {table};")
                print(f"  ✅ Cleared {table}")
            
            conn.commit()
            print("✅ Database reset completed successfully!")
            
    except Exception as e:
        print(f"❌ Error resetting database: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def main():
    """Main function."""
    print("🔄 Resetting cc Agents database...")
    print("⚠️  This will delete ALL data in the database!")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Database reset cancelled.")
        return
    
    try:
        reset_database()
        print("\n💡 Next steps:")
        print("  1. Run 'python -m src.cli sync-all' to sync all definitions to the database")
        print("  2. Or create new agents/workflows using the CLI")
    except Exception as e:
        print(f"❌ Failed to reset database: {str(e)}")

if __name__ == "__main__":
    main() 
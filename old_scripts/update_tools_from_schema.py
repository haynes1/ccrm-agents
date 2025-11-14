import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv('local.env')

def get_db_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(os.getenv('PG_DATABASE_URL'))

def update_tool_in_db(cur, tool_id, tool_schema):
    """Updates the jsonSchema for a specific tool in the database."""
    print(f"Updating tool {tool_id} in the database...")
    cur.execute(
        """
        UPDATE metadata.tool
        SET "jsonSchema" = %s, "updatedAt" = NOW()
        WHERE id = %s;
        """,
        (json.dumps(tool_schema), tool_id),
    )

def process_agent_schema(cur, agent_name):
    """Processes a single agent's jsonSchema.json file."""
    schema_path = os.path.join('agents', agent_name, 'jsonSchema.json')
    print(f"Processing schema: {schema_path}")

    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"  - Schema file not found. Skipping.")
        return 0
    except json.JSONDecodeError:
        print(f"  - Error decoding JSON from schema. Skipping.")
        return 0

    tools = schema.get('tools', [])
    if not tools:
        print(f"  - No tools found in schema. Skipping.")
        return 0

    update_count = 0
    for tool in tools:
        tool_id = tool.get('toolId')
        if not tool_id:
            print(f"  - Skipping a tool because it has no toolId.")
            continue
        
        # Here, we pass the entire tool object into the jsonSchema field
        update_tool_in_db(cur, tool_id, tool)
        update_count += 1
    
    return update_count

def main():
    """Main function to update all tools in the DB from local schemas."""
    total_updated = 0
    conn = None
    try:
        agent_dirs = [d for d in os.listdir('agents') if os.path.isdir(os.path.join('agents', d))]
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for agent_name in agent_dirs:
                total_updated += process_agent_schema(cur, agent_name)
            
            if total_updated > 0:
                print(f"Committing changes to the database...")
                conn.commit()
                print("Changes committed.")
            else:
                print("No tools were updated.")
        
        print(f"\nUpdate complete. Total tools updated: {total_updated}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if conn:
            conn.rollback()
            print("Transaction rolled back.")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 
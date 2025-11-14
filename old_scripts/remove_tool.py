#!/usr/bin/env python3

import os
import sys
import json
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv('local.env')

def get_db_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(os.getenv('PG_DATABASE_URL'))

def remove_tool_from_agent(agent_id, tool_id, delete_tool=False):
    """Remove a tool from an agent and optionally delete the tool."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First, get the agent name
            cur.execute("""
                SELECT name FROM metadata.agent WHERE id = %s
            """, (agent_id,))
            result = cur.fetchone()
            if not result:
                raise Exception(f"Agent with ID {agent_id} not found")
            agent_name = result['name']

            # Remove the agent-tool association
            cur.execute("""
                DELETE FROM metadata.agent_tool 
                WHERE "agentId" = %s AND "toolId" = %s
            """, (agent_id, tool_id))

            # If delete_tool is True, delete the tool
            if delete_tool:
                cur.execute("""
                    DELETE FROM metadata.tool 
                    WHERE id = %s
                """, (tool_id,))

            conn.commit()

            # Update the agent's jsonSchema.json
            schema_path = os.path.join('agents', agent_name, 'jsonSchema.json')
            
            # Read existing schema
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Remove the tool from the schema
            if 'tools' in schema:
                schema['tools'] = [tool for tool in schema['tools'] if tool.get('toolId') != tool_id]
            
            # Write updated schema
            with open(schema_path, 'w') as f:
                json.dump(schema, f, indent=2)

def main():
    """Main function to remove a tool from an agent."""
    try:
        # Get agent ID
        agent_id = input("Enter agent ID: ").strip()
        
        # Get tool ID
        tool_id = input("Enter tool ID: ").strip()
        
        # Ask if tool should be deleted
        delete_tool = input("Delete the tool? (y/N): ").strip().lower() == 'y'
        
        # Remove tool from agent
        remove_tool_from_agent(agent_id, tool_id, delete_tool)
        print(f"Successfully removed tool {tool_id} from agent {agent_id}")
        if delete_tool:
            print("Tool was also deleted from the database")
        
        # Run sync_from_db to ensure everything is in sync
        os.system(f"python src/sync_from_db.py {agent_id}")
        
    except Exception as e:
        print(f"Error removing tool: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
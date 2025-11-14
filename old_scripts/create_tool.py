import os
import json
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('local.env')

def get_db_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(os.getenv('PG_DATABASE_URL'))

def create_tool_in_db(agent_id):
    """Create a new tool in the database and return its ID."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Create new tool
            cur.execute("""
                INSERT INTO metadata.tool 
                (id, "toolName", "descriptionForLlm", "jsonSchema", "toolType", "isSystemTool")
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(uuid.uuid4()),
                f"tool_{uuid.uuid4().hex[:8]}",  # Generate a unique tool name
                "A tool for the agent to use",
                json.dumps({}),  # Empty JSON schema for now
                'custom',
                True
            ))
            tool_id = cur.fetchone()['id']
            
            # Create agent-tool relationship
            cur.execute("""
                INSERT INTO metadata.agent_tool 
                (id, "agentId", "toolId")
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                str(uuid.uuid4()),
                agent_id,
                tool_id
            ))
            
            conn.commit()
            return tool_id

def update_agent_schema(agent_id, tool_id):
    """Update the agent's jsonSchema.json to include the new tool."""
    # First, get the agent name from the database
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT name FROM metadata.agent WHERE id = %s
            """, (agent_id,))
            result = cur.fetchone()
            if not result:
                raise Exception(f"Agent with ID {agent_id} not found")
            agent_name = result['name']
    
    # Update the jsonSchema.json file
    schema_path = os.path.join('agents', agent_name, 'jsonSchema.json')
    
    # Read existing schema
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Initialize tools array if it doesn't exist
    if 'tools' not in schema:
        schema['tools'] = []
    
    # Add new tool
    schema['tools'].append({
        "toolId": tool_id
    })
    
    # Write updated schema
    with open(schema_path, 'w') as f:
        json.dump(schema, f, indent=2)

def main():
    """Main function to create a new tool."""
    if len(sys.argv) != 2:
        print("Usage: python create_tool.py <agent_id>")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    
    try:
        # Create tool in database
        tool_id = create_tool_in_db(agent_id)
        print(f"Created tool with ID: {tool_id}")
        
        # Update agent's jsonSchema.json
        update_agent_schema(agent_id, tool_id)
        print(f"Updated agent's jsonSchema.json with new tool")
        
    except Exception as e:
        print(f"Error creating tool: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
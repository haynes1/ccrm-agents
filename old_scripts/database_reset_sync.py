import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv('local.env')

def get_db_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(os.getenv('PG_DATABASE_URL'))

def read_agent_files(agent_name):
    """Read agent files from local directory."""
    agent_dir = os.path.join('agents', agent_name)
    
    # Read system prompt
    with open(os.path.join(agent_dir, 'systemPrompt.md'), 'r') as f:
        system_prompt = f.read().strip()
    
    # Read JSON schema
    with open(os.path.join(agent_dir, 'jsonSchema.json'), 'r') as f:
        schema = json.load(f)
    
    # Extract system message from schema if it exists
    system_message = next(
        (msg for msg in schema.get('messages', []) if msg.get('role') == 'system'),
        None
    )
    
    # Use system message content if available, otherwise use the markdown file
    system_prompt = system_message['content'] if system_message else system_prompt
    
    return {
        'name': agent_name,
        'systemPrompt': system_prompt,
        'schema': schema
    }

def create_agent_with_id(conn, agent_data):
    """Create an agent in the database using the ID from the schema."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get agent ID from schema
        agent_id = agent_data['schema'].get('agentId')
        if not agent_id:
            raise ValueError(f"No agentId found in schema for agent {agent_data['name']}")
        
        # Create agent with specified ID
        cur.execute("""
            INSERT INTO metadata.agent 
            (id, name, description, "systemPrompt", "llmModelId", "isDefault")
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            agent_id,
            agent_data['name'],
            agent_data['schema'].get('description', ''),
            agent_data['systemPrompt'],
            'gpt-4',  # Default model
            False
        ))
        
        # Get tools from schema
        schema_tools = agent_data['schema'].get('tools', [])
        
        # Create tools and their relationships
        for tool in schema_tools:
            tool_id = tool.get('toolId')
            if not tool_id:
                continue
            
            # Create tool
            cur.execute("""
                INSERT INTO metadata.tool 
                (id, "toolName", "descriptionForLlm", "jsonSchema", "toolType", "isSystemTool", "internalApiPath")
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                tool_id,
                tool['function']['name'],
                tool['function']['description'],
                json.dumps(tool['function'].get('parameters', {})),
                tool['type'],
                True,
                tool.get('internalApiPath')
            ))
            
            # Create agent-tool relationship
            cur.execute("""
                INSERT INTO metadata.agent_tool 
                (id, "agentId", "toolId")
                VALUES (uuid_generate_v4(), %s, %s)
                ON CONFLICT ("agentId", "toolId") DO NOTHING
            """, (agent_id, tool_id))
        
        return agent_id

def main():
    """Main function to sync all local agents to a fresh database."""
    try:
        # Get all agent directories
        agent_dirs = [d for d in os.listdir('agents') 
                     if os.path.isdir(os.path.join('agents', d))]
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                print("Clearing existing data...")
                cur.execute("DELETE FROM metadata.agent_tool;")
                cur.execute("DELETE FROM metadata.agent;")
                print("Data cleared.")
            
            for agent_name in agent_dirs:
                print(f"Syncing agent: {agent_name}")
                agent_data = read_agent_files(agent_name)
                agent_id = create_agent_with_id(conn, agent_data)
                print(f"Successfully synced agent: {agent_name} (ID: {agent_id})")
            
            conn.commit()
        
        print("All agents synced successfully!")
    except Exception as e:
        print(f"Error syncing agents: {str(e)}")
        raise

if __name__ == "__main__":
    main()
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

def sync_agent_from_db(agent):
    """Sync a single agent from database to local files."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get agent details
            cur.execute("""
                SELECT a.*, 
                       json_agg(
                           json_build_object(
                               'toolId', t.id,
                               'type', t."toolType",
                               'function', json_build_object(
                                   'name', t."toolName",
                                   'description', t."descriptionForLlm",
                                   'parameters', t."jsonSchema"
                               ),
                               'internalApiPath', t."internalApiPath"
                           )
                       ) as tools
                FROM metadata.agent a
                LEFT JOIN metadata.agent_tool at ON a.id = at."agentId"
                LEFT JOIN metadata.tool t ON t.id = at."toolId"
                WHERE a.name = %s
                GROUP BY a.id
            """, (agent,))
            
            result = cur.fetchone()
            if not result:
                print(f"Agent {agent} not found in database")
                return
            
            # Create agent directory if it doesn't exist
            agent_dir = os.path.join('agents', agent)
            os.makedirs(agent_dir, exist_ok=True)
            
            # Write system prompt
            with open(os.path.join(agent_dir, 'systemPrompt.md'), 'w') as f:
                f.write(result['systemPrompt'])
            
            # Prepare schema
            schema = {
                'agentId': result['id'],
                'description': result['description'] or '',
                'messages': [
                    {
                        'role': 'system',
                        'content': result['systemPrompt']
                    }
                ],
                'tools': [tool for tool in result['tools'] if tool['toolId'] is not None]
            }
            
            # Write JSON schema
            with open(os.path.join(agent_dir, 'jsonSchema.json'), 'w') as f:
                json.dump(schema, f, indent=2)

def main():
    """Main function to sync all agents from DB to local files."""
    try:
        # Get all agent directories
        agent_dirs = [d for d in os.listdir('agents') 
                     if os.path.isdir(os.path.join('agents', d))]
        
        for agent_name in agent_dirs:
            print(f"Syncing agent: {agent_name}")
            sync_agent_from_db(agent_name)
            print(f"Successfully synced agent: {agent_name}")
        
        print("All agents synced successfully!")
    except Exception as e:
        print(f"Error syncing agents: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
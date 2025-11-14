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

def create_agent_in_db(agent_name):
    """Create a new agent in the database and return its ID."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Create new agent
            cur.execute("""
                INSERT INTO metadata.agent 
                (id, name, description, "systemPrompt", "llmModelId", "isDefault")
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(uuid.uuid4()),
                agent_name,
                f"Agent {agent_name}",
                f"You are {agent_name}, a helpful AI assistant.",
                'gpt-4',  # Default model
                False
            ))
            agent_id = cur.fetchone()['id']
            conn.commit()
            return agent_id

def create_agent_directory(agent_name, agent_id):
    """Create agent directory and initial files."""
    # Create agent directory
    agent_dir = os.path.join('agents', agent_name)
    os.makedirs(agent_dir, exist_ok=True)
    
    # Create initial systemPrompt.md
    with open(os.path.join(agent_dir, 'systemPrompt.md'), 'w') as f:
        f.write(f"You are {agent_name}, a helpful AI assistant.")
    
    # Create initial jsonSchema.json
    schema = {
        "agentId": agent_id
    }
    
    with open(os.path.join(agent_dir, 'jsonSchema.json'), 'w') as f:
        json.dump(schema, f, indent=2)

def main():
    """Main function to create a new agent."""
    if len(sys.argv) != 2:
        print("Usage: python create_agent.py <agent_name>")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    
    try:
        # Create agent in database
        agent_id = create_agent_in_db(agent_name)
        print(f"Created agent '{agent_name}' in database with ID: {agent_id}")
        
        # Create agent directory and files
        create_agent_directory(agent_name, agent_id)
        print(f"Created agent directory and files at: agents/{agent_name}/")
        
        print("\nInitial files created:")
        print(f"- agents/{agent_name}/systemPrompt.md")
        print(f"- agents/{agent_name}/jsonSchema.json")
        
    except Exception as e:
        print(f"Error creating agent: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
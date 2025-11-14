import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import uuid

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

def upsert_agent(conn, agent_data):
    """Insert or update an agent and its tools in the database using the local JSON as the source of truth."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # --- Upsert Agent ---
        cur.execute("SELECT id FROM metadata.agent WHERE name = %s", (agent_data['name'],))
        result = cur.fetchone()
        agent_id = None
        if result:
            agent_id = result['id']
            # Update existing agent
            cur.execute("""
                UPDATE metadata.agent 
                SET "systemPrompt" = %s, description = %s, "updatedAt" = NOW()
                WHERE id = %s
            """, (agent_data['systemPrompt'], agent_data['schema'].get('description', ''), agent_id))
        else:
            # Insert new agent
            agent_id = agent_data['schema'].get('agentId', str(uuid.uuid4()))
            cur.execute("""
                INSERT INTO metadata.agent (id, name, description, "systemPrompt", "llmModelId", "isDefault")
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                agent_id, agent_data['name'], agent_data['schema'].get('description', ''),
                agent_data['systemPrompt'], 'gpt-4', False
            ))

        # --- Upsert Tools and Associations ---
        schema_tools = agent_data['schema'].get('tools', [])
        schema_tool_ids = set()

        if schema_tools:
            for tool_data in schema_tools:
                tool_function = tool_data.get('function', {})
                tool_name = tool_function.get('name')

                if not tool_name:
                    continue

                # The user's system expects the entire tool object to be stored in the jsonSchema column.
                json_schema_blob = tool_data

                # --- Tool Upsert Logic ---
                # The primary identifier for a tool is its ID. We check for existence based on the toolId from the JSON file.
                tool_id_str = tool_data.get('toolId')
                tool_id = uuid.UUID(tool_id_str) if tool_id_str else uuid.uuid4()

                cur.execute('SELECT id FROM metadata.tool WHERE id = %s', (str(tool_id),))
                result = cur.fetchone()

                if result:
                    # Tool exists, update it.
                    # Note: We ensure the toolName is also updated, in case it changed in the JSON.
                    cur.execute("""
                        UPDATE metadata.tool SET
                            "toolName" = %s, "descriptionForLlm" = %s, "jsonSchema" = %s,
                            "toolType" = %s, "internalApiPath" = %s, "isSystemTool" = %s,
                            "updatedAt" = NOW()
                        WHERE id = %s;
                    """, (
                        tool_name, tool_function.get('description'), json.dumps(json_schema_blob),
                        tool_data.get('type'), tool_data.get('internalApiPath'), True,
                        str(tool_id)
                    ))
                else:
                    # Tool does not exist, insert it.
                    cur.execute("""
                        INSERT INTO metadata.tool (id, "toolName", "descriptionForLlm", "jsonSchema", "toolType", "internalApiPath", "isSystemTool")
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (
                        str(tool_id), tool_name, tool_function.get('description'), json.dumps(json_schema_blob),
                        tool_data.get('type'), tool_data.get('internalApiPath'), True
                    ))

                schema_tool_ids.add(str(tool_id))

                # Create association if it doesn't exist
                cur.execute("""
                    INSERT INTO metadata.agent_tool (id, "agentId", "toolId")
                    SELECT %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM metadata.agent_tool WHERE "agentId" = %s AND "toolId" = %s
                    );
                """, (str(uuid.uuid4()), agent_id, str(tool_id), agent_id, str(tool_id)))
        
        # --- De-associate Old Tools ---
        cur.execute('SELECT "toolId" FROM metadata.agent_tool WHERE "agentId" = %s', (agent_id,))
        db_tool_ids = {str(row['toolId']) for row in cur.fetchall()}

        tools_to_remove = db_tool_ids - schema_tool_ids
        if tools_to_remove:
            # Note: Explicitly casting to uuid[] to avoid type errors with psycopg2
            cur.execute(
                'DELETE FROM metadata.agent_tool WHERE "agentId" = %s AND "toolId" = ANY(ARRAY[%s]::uuid[]);',
                (agent_id, [str(t) for t in tools_to_remove])
            )
            print(f"De-associated {len(tools_to_remove)} tools from agent {agent_data['name']}.")

        return agent_id

def main():
    """Main function to sync all local agents to DB."""
    try:
        # Get all agent directories
        agent_dirs = [d for d in os.listdir('agents') 
                     if os.path.isdir(os.path.join('agents', d))]
        
        with get_db_connection() as conn:
            for agent_name in agent_dirs:
                print(f"Syncing agent: {agent_name}")
                agent_data = read_agent_files(agent_name)
                agent_id = upsert_agent(conn, agent_data)
                print(f"Successfully synced agent: {agent_name} (ID: {agent_id})")
            
            conn.commit()
        
        print("All agents synced successfully!")
    except Exception as e:
        print(f"Error syncing agents: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
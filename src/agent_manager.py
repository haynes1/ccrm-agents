"""
Agent management functionality for the cc Agents system.
Handles creation, syncing, and management of agents with dual scope support.
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Tuple
from .config import get_db_connection, get_db_cursor, Scope, ResourceType, get_definitions_path, ensure_directory_exists
from .tool_manager import ToolManager

class AgentManager:
    """Manages agent operations including creation, syncing, and database operations."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        """Context manager entry."""
        self.conn = get_db_connection()
        self.cursor = get_db_cursor(self.conn)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def _get_table_name(self, scope: Scope) -> str:
        """Get the correct table name based on the scope."""
        if scope == Scope.SYSTEM:
            return "metadata.system_agent"
        elif scope == Scope.COMMON_BACKGROUND:
            return "metadata.common_background_agent"
        else:
            raise ValueError(f"Invalid scope: {scope}")
    
    def create_agent(self, name: str, scope: Scope, description: str = "", system_prompt: str = "") -> str:
        """Create a new agent in the database and local files."""
        agent_id = str(uuid.uuid4())
        table_name = self._get_table_name(scope)
        
        # Create agent in database
        self.cursor.execute(f"""
            INSERT INTO {table_name} 
            (id, name, description, "systemPrompt", "llmModelId", "isDefault")
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            agent_id,
            name,
            description,
            system_prompt or f"You are {name}, a helpful AI assistant.",
            'gpt-4',
            False
        ))
        
        # Create local directory and files
        self._create_agent_files(name, agent_id, scope, description, system_prompt)
        
        self.conn.commit()
        return agent_id
    
    def _create_agent_files(self, name: str, agent_id: str, scope: Scope, description: str, system_prompt: str):
        """Create the local files for an agent."""
        # Create directory
        agent_dir = os.path.join(get_definitions_path(scope, ResourceType.AGENT), name)
        ensure_directory_exists(agent_dir)
        
        # Create systemPrompt.md
        prompt_content = system_prompt or f"You are {name}, a helpful AI assistant."
        with open(os.path.join(agent_dir, 'systemPrompt.md'), 'w') as f:
            f.write(prompt_content)
        
        # Create jsonSchema.json
        schema = {
            "agentId": agent_id,
            "name": name,
            "description": description,
            "scope": scope.value,
            "tools": []
        }
        
        with open(os.path.join(agent_dir, 'jsonSchema.json'), 'w') as f:
            json.dump(schema, f, indent=2)
    
    def sync_agent_to_db(self, name: str, scope: Scope) -> str:
        """Sync a single agent from local files to database."""
        agent_dir = os.path.join(get_definitions_path(scope, ResourceType.AGENT), name)
        table_name = self._get_table_name(scope)
        
        if not os.path.exists(agent_dir):
            raise FileNotFoundError(f"Agent directory not found: {agent_dir}")
        
        # Read files
        with open(os.path.join(agent_dir, 'systemPrompt.md'), 'r') as f:
            system_prompt = f.read().strip()
        
        with open(os.path.join(agent_dir, 'jsonSchema.json'), 'r') as f:
            schema = json.load(f)
        
        agent_id = schema.get('agentId', str(uuid.uuid4()))
        
        # Upsert agent
        self.cursor.execute(f"""
            INSERT INTO {table_name} 
            (id, name, description, "systemPrompt", "llmModelId", "isDefault")
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                "systemPrompt" = EXCLUDED."systemPrompt",
                "updatedAt" = NOW()
        """, (
            agent_id,
            name,
            schema.get('description', ''),
            system_prompt,
            'gpt-4',
            False
        ))
        
        # Commit the agent creation/update before handling tools
        self.conn.commit()
        
        # Handle tools if present
        if 'tools' in schema:
            with ToolManager() as tm:
                sync_results = tm.sync_agent_tools(agent_id, schema['tools'], scope)
                print(f"Tool sync results: {sync_results}")
        
        return agent_id
    
    def sync_agent_from_db(self, name: str, scope: Scope) -> str:
        """Sync a single agent from database to local files."""
        table_name = self._get_table_name(scope)
        # Get agent from database
        self.cursor.execute(f"""
            SELECT * FROM {table_name} WHERE name = %s
        """, (name,))
        
        agent = self.cursor.fetchone()
        if not agent:
            raise ValueError(f"Agent {name} not found in database with scope {scope.value}")
        
        # Create local files
        self._create_agent_files(
            name, 
            agent['id'], 
            scope, 
            agent['description'] or '',
            agent['systemPrompt']
        )
        
        return agent['id']
    
    def list_agents(self, scope: Optional[Scope] = None) -> List[Dict]:
        """List all agents, optionally filtered by scope."""
        if scope:
            table_name = self._get_table_name(scope)
            query = f"SELECT *, '{scope.value}' as scope FROM {table_name} ORDER BY name"
            self.cursor.execute(query)
        else:
            system_table = self._get_table_name(Scope.SYSTEM)
            common_table = self._get_table_name(Scope.COMMON_BACKGROUND)
            query = f"""
                SELECT *, 'SYSTEM' as scope FROM {system_table}
                UNION ALL
                SELECT *, 'COMMON_BACKGROUND' as scope FROM {common_table}
                ORDER BY name
            """
            self.cursor.execute(query)
            
        return [dict(row) for row in self.cursor.fetchall()]
    
    def delete_agent(self, name: str, scope: Scope) -> bool:
        """Delete an agent from both database and local files."""
        table_name = self._get_table_name(scope)
        # Delete from database
        self.cursor.execute(f"""
            DELETE FROM {table_name} WHERE name = %s
        """, (name,))
        
        if self.cursor.rowcount == 0:
            return False
        
        # Delete local files
        agent_dir = os.path.join(get_definitions_path(scope, ResourceType.AGENT), name)
        if os.path.exists(agent_dir):
            import shutil
            shutil.rmtree(agent_dir)
        
        self.conn.commit()
        return True
    
    def sync_all_agents(self, scope: Optional[Scope] = None) -> Dict[str, List[str]]:
        """Sync all agents from local files to database."""
        results = {"success": [], "errors": []}
        
        # Get all scope directories to process
        scopes_to_process = [scope] if scope else [Scope.SYSTEM, Scope.COMMON_BACKGROUND]
        
        for current_scope in scopes_to_process:
            definitions_path = get_definitions_path(current_scope, ResourceType.AGENT)
            
            if not os.path.exists(definitions_path):
                continue
            
            for agent_name in os.listdir(definitions_path):
                agent_dir = os.path.join(definitions_path, agent_name)
                if os.path.isdir(agent_dir):
                    try:
                        agent_id = self.sync_agent_to_db(agent_name, current_scope)
                        results["success"].append(f"{current_scope.value}:{agent_name} (ID: {agent_id})")
                    except Exception as e:
                        results["errors"].append(f"{current_scope.value}:{agent_name} - {str(e)}")
        
        return results
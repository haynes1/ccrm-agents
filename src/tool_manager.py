"""
Tool management functionality for the 2n Agents system.
Handles tool creation, updates, associations, and cleanup with proper edge case handling.
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Set
from .config import get_db_connection, get_db_cursor, Scope, ResourceType, get_definitions_path, ensure_directory_exists

class ToolManager:
    """Manages tool operations including creation, updates, associations, and cleanup."""
    
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

    def _get_agent_tool_table_name(self, scope: Scope) -> str:
        """Get the correct agent-tool table name based on the scope."""
        if scope == Scope.SYSTEM:
            return "metadata.system_agent_tool"
        elif scope == Scope.COMMON_BACKGROUND:
            return "metadata.common_background_agent_tool"
        else:
            raise ValueError(f"Invalid scope: {scope}")

    def create_tool(self, tool_id: str, tool_name: str, description: str = "", 
                   tool_type: str = "custom", internal_api_path: str = None, 
                   json_schema: Dict = None) -> str:
        """Create a new tool in the database."""
        if not json_schema:
            json_schema = {}
        
        self.cursor.execute("""
            INSERT INTO metadata.system_tool
            (id, "toolName", "descriptionForLlm", "jsonSchema", "toolType", "internalApiPath", "isSystemTool")
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                "toolName" = EXCLUDED."toolName",
                "descriptionForLlm" = EXCLUDED."descriptionForLlm",
                "jsonSchema" = EXCLUDED."jsonSchema",
                "toolType" = EXCLUDED."toolType",
                "internalApiPath" = EXCLUDED."internalApiPath",
                "updatedAt" = NOW()
        """, (
            tool_id,
            tool_name,
            description,
            json.dumps(json_schema),
            tool_type,
            internal_api_path,
            True
        ))
        
        self.conn.commit()
        return tool_id
    
    def update_tool(self, tool_id: str, tool_name: str = None, description: str = None,
                   tool_type: str = None, internal_api_path: str = None, 
                   json_schema: Dict = None) -> bool:
        """Update an existing tool."""
        # Build dynamic update query
        updates = []
        params = []
        
        if tool_name is not None:
            updates.append('"toolName" = %s')
            params.append(tool_name)
        
        if description is not None:
            updates.append('"descriptionForLlm" = %s')
            params.append(description)
        
        if tool_type is not None:
            updates.append('"toolType" = %s')
            params.append(tool_type)
        
        if internal_api_path is not None:
            updates.append('"internalApiPath" = %s')
            params.append(internal_api_path)
        
        if json_schema is not None:
            updates.append('"jsonSchema" = %s')
            params.append(json.dumps(json_schema))
        
        if not updates:
            return False
        
        updates.append('"updatedAt" = NOW()')
        params.append(tool_id)
        
        query = f"""
            UPDATE metadata.system_tool
            SET {', '.join(updates)}
            WHERE id = %s
        """
        
        self.cursor.execute(query, params)
        self.conn.commit()
        
        return self.cursor.rowcount > 0
    
    def delete_tool(self, tool_id: str, force: bool = False) -> bool:
        """Delete a tool from the database."""
        # Check for associations in both scopes
        system_agent_tool_table = self._get_agent_tool_table_name(Scope.SYSTEM)
        common_agent_tool_table = self._get_agent_tool_table_name(Scope.COMMON_BACKGROUND)
        
        self.cursor.execute(f"""
            SELECT COUNT(*) as count FROM {system_agent_tool_table} WHERE "toolId" = %s
        """, (tool_id,))
        association_count = self.cursor.fetchone()['count']
        
        self.cursor.execute(f"""
            SELECT COUNT(*) as count FROM {common_agent_tool_table} WHERE "toolId" = %s
        """, (tool_id,))
        association_count += self.cursor.fetchone()['count']
        
        if association_count > 0 and not force:
            raise ValueError(f"Cannot delete tool {tool_id}: it is associated with {association_count} agents. Use --force to override.")
        
        # Remove all associations first
        self.cursor.execute(f'DELETE FROM {system_agent_tool_table} WHERE "toolId" = %s', (tool_id,))
        self.cursor.execute(f'DELETE FROM {common_agent_tool_table} WHERE "toolId" = %s', (tool_id,))
        
        # Delete the tool
        self.cursor.execute("DELETE FROM metadata.system_tool WHERE id = %s", (tool_id,))
        
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_tool(self, tool_id: str) -> Optional[Dict]:
        """Get a tool by ID."""
        self.cursor.execute("SELECT * FROM metadata.system_tool WHERE id = %s", (tool_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def list_tools(self) -> List[Dict]:
        """List all tools."""
        self.cursor.execute('SELECT * FROM metadata.system_tool ORDER BY "toolName"')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_agent_tools(self, agent_id: str, scope: Scope) -> List[Dict]:
        """Get all tools associated with an agent."""
        agent_tool_table = self._get_agent_tool_table_name(scope)
        self.cursor.execute(f"""
            SELECT t.* FROM metadata.system_tool t
            JOIN {agent_tool_table} at ON t.id = at."toolId"
            WHERE at."agentId" = %s
            ORDER BY t."toolName"
        """, (agent_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def associate_tool_with_agent(self, agent_id: str, tool_id: str, scope: Scope) -> bool:
        """Associate a tool with an agent."""
        agent_tool_table = self._get_agent_tool_table_name(scope)
        
        # Verify tool exists
        if not self.get_tool(tool_id):
            raise ValueError(f"Tool {tool_id} not found")
        
        # Create association
        self.cursor.execute(f"""
            INSERT INTO {agent_tool_table} (id, "agentId", "toolId")
            VALUES (%s, %s, %s)
            ON CONFLICT ("agentId", "toolId") DO NOTHING
        """, (str(uuid.uuid4()), agent_id, tool_id))
        
        self.conn.commit()
        return True
    
    def disassociate_tool_from_agent(self, agent_id: str, tool_id: str, scope: Scope) -> bool:
        """Remove a tool association from an agent."""
        agent_tool_table = self._get_agent_tool_table_name(scope)
        self.cursor.execute(f"""
            DELETE FROM {agent_tool_table} 
            WHERE "agentId" = %s AND "toolId" = %s
        """, (agent_id, tool_id))
        
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def sync_agent_tools(self, agent_id: str, tools: List[Dict], scope: Scope) -> Dict[str, int]:
        """Sync tool associations for an agent with proper cleanup."""
        agent_tool_table = self._get_agent_tool_table_name(scope)
        
        # Get current tool associations
        self.cursor.execute(f"""
            SELECT "toolId" FROM {agent_tool_table} WHERE "agentId" = %s
        """, (agent_id,))
        current_tool_ids = {str(row['toolId']) for row in self.cursor.fetchall()}
        
        # Process new tools
        new_tool_ids = set()
        created_count = 0
        updated_count = 0
        
        for tool_data in tools:
            tool_id = tool_data.get('toolId')
            if not tool_id:
                continue
            
            tool_function = tool_data.get('function', {})
            tool_name = tool_function.get('name', f"tool_{tool_id[:8]}")
            
            try:
                self.create_tool(
                    tool_id=tool_id,
                    tool_name=tool_name,
                    description=tool_function.get('description', ''),
                    tool_type=tool_data.get('type', 'custom'),
                    json_schema=tool_data
                )
                new_tool_ids.add(tool_id)
                
            except Exception as e:
                print(f"Warning: Failed to process tool {tool_id}: {str(e)}")
                continue
        
        # Remove old associations
        tools_to_remove = current_tool_ids - new_tool_ids
        removed_count = 0
        for tool_id in tools_to_remove:
            if self.disassociate_tool_from_agent(agent_id, tool_id, scope):
                removed_count += 1
        
        # Add new associations
        added_count = 0
        for tool_id in new_tool_ids:
            if tool_id not in current_tool_ids:
                if self.associate_tool_with_agent(agent_id, tool_id, scope):
                    added_count += 1
        
        return {
            "created": created_count,
            "updated": updated_count,
            "added": added_count,
            "removed": removed_count
        }

    def find_orphaned_tools(self) -> List[Dict]:
        """Find tools that are not associated with any agents across both scopes."""
        system_agent_tool_table = self._get_agent_tool_table_name(Scope.SYSTEM)
        common_agent_tool_table = self._get_agent_tool_table_name(Scope.COMMON_BACKGROUND)

        self.cursor.execute(f"""
            SELECT t.* FROM metadata.system_tool t
            LEFT JOIN {system_agent_tool_table} sat ON t.id = sat."toolId"
            LEFT JOIN {common_agent_tool_table} cat ON t.id = cat."toolId"
            WHERE sat."toolId" IS NULL AND cat."toolId" IS NULL
            ORDER BY t."toolName"
        """)
        
        return [dict(row) for row in self.cursor.fetchall()]

    def cleanup_orphaned_tools(self, force: bool = False) -> int:
        """Remove tools that are not associated with any agents."""
        orphaned_tools = self.find_orphaned_tools()
        
        if not orphaned_tools:
            return 0
        
        if not force:
            print(f"Found {len(orphaned_tools)} orphaned tools:")
            for tool in orphaned_tools:
                print(f"  - {tool['toolName']} (ID: {tool['id']})")
            print("Run with --force to delete them.")
            return 0
        
        deleted_count = 0
        for tool in orphaned_tools:
            if self.delete_tool(tool['id'], force=True):
                deleted_count += 1
        
        return deleted_count
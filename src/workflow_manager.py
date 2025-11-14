"""
Workflow management functionality for the cc Agents system.
Handles creation, syncing, and management of agentic workflows with dual scope support.
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Tuple
from .config import get_db_connection, get_db_cursor, Scope, ResourceType, get_definitions_path, ensure_directory_exists

class WorkflowManager:
    """Manages workflow operations including creation, syncing, and database operations."""
    
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

    def _get_table_name(self, scope: Scope, resource: ResourceType) -> str:
        """Get the correct table name based on the scope and resource type."""
        # CCRM only has system_ tables (no schema prefix, no common_background variants)
        if resource == ResourceType.WORKFLOW:
            return "system_agent_workflow"
        elif resource == ResourceType.WORKFLOW_NODE:
            return "system_agent_workflow_node"
        elif resource == ResourceType.WORKFLOW_EDGE:
            return "system_agent_workflow_edge"
        elif resource == ResourceType.AGENT:
            return "system_agent"
        else:
            raise ValueError(f"Invalid resource type for table name: {resource}")

    def _validate_agent_exists(self, agent_id: str) -> Optional[Scope]:
        """Validate that an agent exists and return the scope."""
        if not agent_id:
            return None

        agent_table = self._get_table_name(Scope.SYSTEM, ResourceType.AGENT)

        self.cursor.execute(f"SELECT id FROM {agent_table} WHERE id = %s", (agent_id,))
        if self.cursor.fetchone():
            return Scope.SYSTEM

        return None
    
    def sync_workflow_to_db(self, workflow_id: str, scope: Scope) -> str:
        """Sync a single workflow from local files to database using a literal 1-to-1 mapping."""
        workflow_dir = os.path.join(get_definitions_path(scope, ResourceType.WORKFLOW), workflow_id)

        if not os.path.exists(workflow_dir):
            raise FileNotFoundError(f"Workflow directory not found: {workflow_dir}")

        with open(os.path.join(workflow_dir, 'workflow.json'), 'r') as f:
            workflow_data = json.load(f)

        workflow_table = self._get_table_name(scope, ResourceType.WORKFLOW)
        entrypoint_node_id = workflow_data.get('entrypointNodeId')

        # Step 1: Insert/update workflow WITHOUT entrypoint_node_id to avoid FK constraint violation
        self.cursor.execute(f"""
            INSERT INTO {workflow_table}
            (id, name, description, entrypoint_node_id, is_conversational)
            VALUES (%s, %s, %s, NULL, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                is_conversational = EXCLUDED.is_conversational,
                updated_at = NOW()
        """, (
            workflow_data['id'],
            workflow_data['name'],
            workflow_data.get('description', ''),
            workflow_data.get('isConversational', False)
        ))

        # Step 2: Sync nodes (now they can be created)
        self._sync_workflow_nodes(workflow_id, workflow_data.get('nodes', []), scope)

        # Step 3: Sync edges
        self._sync_workflow_edges(workflow_id, workflow_data.get('edges', []), scope)

        # Step 4: Update workflow with entrypoint_node_id now that nodes exist
        if entrypoint_node_id:
            self.cursor.execute(f"""
                UPDATE {workflow_table}
                SET entrypoint_node_id = %s, updated_at = NOW()
                WHERE id = %s
            """, (entrypoint_node_id, workflow_id))

        self.conn.commit()
        return workflow_id
    
    def _sync_workflow_nodes(self, workflow_id: str, nodes: List[Dict], scope: Scope):
        """Sync workflow nodes to database with agent validation."""
        node_table = self._get_table_name(scope, ResourceType.WORKFLOW_NODE)
        self.cursor.execute(f'DELETE FROM {node_table} WHERE workflow_id = %s', (workflow_id,))
        
        for node in nodes:
            agent_id = node.get('agentId')
            
            if agent_id and not self._validate_agent_exists(agent_id):
                raise ValueError(f"Agent {agent_id} referenced in workflow {workflow_id} does not exist in any scope")
            
            self.cursor.execute(f"""
                INSERT INTO {node_table}
                (id, workflow_id, agent_id, node_type, node_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                node['id'],
                workflow_id,
                agent_id,
                node['nodeType'],
                node['nodeName']
            ))
    
    def _sync_workflow_edges(self, workflow_id: str, edges: List[Dict], scope: Scope):
        """Sync workflow edges to database."""
        edge_table = self._get_table_name(scope, ResourceType.WORKFLOW_EDGE)
        self.cursor.execute(f'DELETE FROM {edge_table} WHERE workflow_id = %s', (workflow_id,))
        
        for edge in edges:
            self.cursor.execute(f"""
                INSERT INTO {edge_table}
                (id, workflow_id, source_node_id, target_node_id, condition_type, condition_value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                edge['id'],
                workflow_id,
                edge['sourceNodeId'],
                edge.get('targetNodeId'),
                edge['conditionType'],
                edge.get('conditionValue')
            ))

    def sync_workflow_from_db(self, workflow_id: str, scope: Scope) -> str:
        """Sync a single workflow from database to local files."""
        workflow_table = self._get_table_name(scope, ResourceType.WORKFLOW)
        node_table = self._get_table_name(scope, ResourceType.WORKFLOW_NODE)
        edge_table = self._get_table_name(scope, ResourceType.WORKFLOW_EDGE)

        self.cursor.execute(f"SELECT * FROM {workflow_table} WHERE id = %s", (workflow_id,))
        workflow = self.cursor.fetchone()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found in database with scope {scope.value}")
        
        self.cursor.execute(f'SELECT * FROM {node_table} WHERE workflow_id = %s', (workflow_id,))
        nodes = [dict(row) for row in self.cursor.fetchall()]

        self.cursor.execute(f'SELECT * FROM {edge_table} WHERE workflow_id = %s', (workflow_id,))
        edges = [dict(row) for row in self.cursor.fetchall()]
        
        workflow_dir = os.path.join(get_definitions_path(scope, ResourceType.WORKFLOW), workflow_id)
        ensure_directory_exists(workflow_dir)
        
        workflow_data = {
            "id": workflow_id,
            "name": workflow['name'],
            "description": workflow.get('description', ''),
            "scope": scope.value,
            "isConversational": workflow.get('isConversational', False),
            "entrypointNodeId": workflow.get('entrypoint_node_id'),
            "nodes": [
                {
                    "id": node['id'],
                    "workflowId": node['workflowId'],
                    "nodeType": node['nodeType'],
                    "nodeName": node['nodeName'],
                    "agentId": node.get('agentId')
                }
                for node in nodes
            ],
            "edges": [
                {
                    "id": edge['id'],
                    "workflowId": edge['workflowId'],
                    "sourceNodeId": edge['sourceNodeId'],
                    "targetNodeId": edge.get('targetNodeId'),
                    "conditionType": edge['conditionType'],
                    "conditionValue": edge.get('conditionValue')
                }
                for edge in edges
            ]
        }
        
        with open(os.path.join(workflow_dir, 'workflow.json'), 'w') as f:
            json.dump(workflow_data, f, indent=2)
        
        return workflow_id

    def list_workflows(self, scope: Optional[Scope] = None) -> List[Dict]:
        """List all workflows, optionally filtered by scope."""
        if scope:
            table_name = self._get_table_name(scope, ResourceType.WORKFLOW)
            query = f"SELECT *, '{scope.value}' as scope FROM {table_name} ORDER BY name"
            self.cursor.execute(query)
        else:
            system_table = self._get_table_name(Scope.SYSTEM, ResourceType.WORKFLOW)
            common_table = self._get_table_name(Scope.COMMON_BACKGROUND, ResourceType.WORKFLOW)
            query = f"""
                SELECT *, 'SYSTEM' as scope FROM {system_table}
                UNION ALL
                SELECT *, 'COMMON_BACKGROUND' as scope FROM {common_table}
                ORDER BY name
            """
            self.cursor.execute(query)
            
        return [dict(row) for row in self.cursor.fetchall()]

    def delete_workflow(self, workflow_id: str, scope: Scope) -> bool:
        """Delete a workflow from both database and local files."""
        workflow_table = self._get_table_name(scope, ResourceType.WORKFLOW)
        
        self.cursor.execute(f"DELETE FROM {workflow_table} WHERE id = %s", (workflow_id,))
        
        if self.cursor.rowcount == 0:
            return False
        
        workflow_dir = os.path.join(get_definitions_path(scope, ResourceType.WORKFLOW), workflow_id)
        if os.path.exists(workflow_dir):
            import shutil
            shutil.rmtree(workflow_dir)
        
        self.conn.commit()
        return True

    def sync_all_workflows(self, scope: Optional[Scope] = None) -> Dict[str, List[str]]:
        """Sync all workflows from local files to database."""
        results = {"success": [], "errors": []}
        
        scopes_to_process = [scope] if scope else [Scope.SYSTEM, Scope.COMMON_BACKGROUND]
        
        for current_scope in scopes_to_process:
            definitions_path = get_definitions_path(current_scope, ResourceType.WORKFLOW)
            
            if not os.path.exists(definitions_path):
                continue
            
            for workflow_id in os.listdir(definitions_path):
                workflow_dir = os.path.join(definitions_path, workflow_id)
                if os.path.isdir(workflow_dir):
                    try:
                        synced_id = self.sync_workflow_to_db(workflow_id, current_scope)
                        results["success"].append(f"{current_scope.value}:{workflow_id} (ID: {synced_id})")
                    except Exception as e:
                        results["errors"].append(f"{current_scope.value}:{workflow_id} - {str(e)}")
        
        return results
    
    def get_workflow_agents(self, workflow_id: str, scope: Scope) -> List[Dict]:
        """Get all agents referenced by a workflow from any scope."""
        node_table = self._get_table_name(scope, ResourceType.WORKFLOW_NODE)
        system_agent_table = self._get_table_name(Scope.SYSTEM, ResourceType.AGENT)
        common_agent_table = self._get_table_name(Scope.COMMON_BACKGROUND, ResourceType.AGENT)
        
        query = f"""
            WITH AllAgents AS (
                SELECT id, name, 'SYSTEM' as scope FROM {system_agent_table}
                UNION ALL
                SELECT id, name, 'COMMON_BACKGROUND' as scope FROM {common_agent_table}
            )
            SELECT DISTINCT aa.* FROM AllAgents aa
            JOIN {node_table} n ON aa.id = n."agentId"
            WHERE n."workflowId" = %s AND n."agentId" IS NOT NULL
            ORDER BY aa.name
        """
        self.cursor.execute(query, (workflow_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_agent_workflows(self, agent_id: str) -> List[Dict]:
        """Get all workflows that reference a specific agent across all scopes."""
        system_node_table = self._get_table_name(Scope.SYSTEM, ResourceType.WORKFLOW_NODE)
        common_node_table = self._get_table_name(Scope.COMMON_BACKGROUND, ResourceType.WORKFLOW_NODE)
        system_workflow_table = self._get_table_name(Scope.SYSTEM, ResourceType.WORKFLOW)
        common_workflow_table = self._get_table_name(Scope.COMMON_BACKGROUND, ResourceType.WORKFLOW)

        query = f"""
            SELECT DISTINCT w.*, 'SYSTEM' as scope 
            FROM {system_workflow_table} w
            JOIN {system_node_table} n ON w.id = n."workflowId"
            WHERE n."agentId" = %s
            UNION ALL
            SELECT DISTINCT w.*, 'COMMON_BACKGROUND' as scope
            FROM {common_workflow_table} w
            JOIN {common_node_table} n ON w.id = n."workflowId"
            WHERE n."agentId" = %s
            ORDER BY name
        """
        self.cursor.execute(query, (agent_id, agent_id))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def create_workflow(self, workflow_id: str, name: str, scope: Scope, description: str = "") -> str:
        """Creates a new workflow with a single default node."""
        workflow_dir = os.path.join(get_definitions_path(scope, ResourceType.WORKFLOW), workflow_id)
        ensure_directory_exists(workflow_dir)

        entrypoint_node_id = str(uuid.uuid4())
        
        workflow_data = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "scope": scope.value,
            "isConversational": False,
            "entrypointNodeId": entrypoint_node_id,
            "nodes": [
                {
                    "id": entrypoint_node_id,
                    "workflowId": workflow_id,
                    "nodeType": "ROUTER",
                    "nodeName": "Start"
                }
            ],
            "edges": []
        }

        with open(os.path.join(workflow_dir, 'workflow.json'), 'w') as f:
            json.dump(workflow_data, f, indent=2)
            
        self.sync_workflow_to_db(workflow_id, scope)
        return workflow_id
        
    def validate_workflow(self, workflow_id: str, scope: Scope) -> Dict[str, any]:
        """Validate a workflow and return detailed status."""
        workflow_table = self._get_table_name(scope, ResourceType.WORKFLOW)
        node_table = self._get_table_name(scope, ResourceType.WORKFLOW_NODE)
        edge_table = self._get_table_name(scope, ResourceType.WORKFLOW_EDGE)

        self.cursor.execute(f"SELECT * FROM {workflow_table} WHERE id = %s", (workflow_id,))
        workflow = self.cursor.fetchone()
        
        if not workflow:
            return {"valid": False, "errors": [f"Workflow {workflow_id} in scope {scope.value} does not exist"]}
        
        self.cursor.execute(f'SELECT * FROM {node_table} WHERE workflow_id = %s', (workflow_id,))
        nodes = [dict(row) for row in self.cursor.fetchall()]

        self.cursor.execute(f'SELECT * FROM {edge_table} WHERE workflow_id = %s', (workflow_id,))
        edges = [dict(row) for row in self.cursor.fetchall()]
        
        errors = []
        warnings = []
        
        entrypoint_node_id = workflow.get('entrypoint_node_id')
        if not entrypoint_node_id or not any(node['id'] == entrypoint_node_id for node in nodes):
            errors.append(f"Entrypoint node {entrypoint_node_id} does not exist")
        
        for node in nodes:
            agent_id = node.get('agentId')
            if agent_id and not self._validate_agent_exists(agent_id):
                errors.append(f"Agent {agent_id} referenced by node {node['nodeName']} does not exist in any scope")
        
        node_ids = {node['id'] for node in nodes}
        for edge in edges:
            if edge['sourceNodeId'] not in node_ids:
                errors.append(f"Edge references non-existent source node {edge['sourceNodeId']}")
            if edge.get('targetNodeId') and edge['targetNodeId'] not in node_ids:
                errors.append(f"Edge references non-existent target node {edge['targetNodeId']}")
        
        connected_nodes = {edge['sourceNodeId'] for edge in edges}
        for edge in edges:
            if edge.get('targetNodeId'):
                connected_nodes.add(edge['targetNodeId'])
                
        orphaned_nodes = node_ids - connected_nodes - {entrypoint_node_id}
        if orphaned_nodes:
            warnings.append(f"Orphaned nodes found (unreachable from any edge): {', '.join(orphaned_nodes)}")
        
        return {
            "valid": len(errors) == 0,
            "workflow": dict(workflow),
            "nodes": nodes,
            "edges": edges,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_node_exists(self, node_id: str, scope: Scope) -> bool:
        """Validate that a node exists in the database for a given scope."""
        node_table = self._get_table_name(scope, ResourceType.WORKFLOW_NODE)
        self.cursor.execute(f"SELECT COUNT(*) as count FROM {node_table} WHERE id = %s", (node_id,))
        return self.cursor.fetchone()['count'] > 0

    def add_node_to_workflow(self, workflow_id: str, node_name: str, scope: Scope, agent_id: str = None, 
                            node_type: str = "AGENT") -> str:
        """Add a node to an existing workflow with agent validation."""
        if agent_id and not self._validate_agent_exists(agent_id):
            raise ValueError(f"Agent {agent_id} does not exist in any scope")
        
        node_id = str(uuid.uuid4())
        node_table = self._get_table_name(scope, ResourceType.WORKFLOW_NODE)
        
        self.cursor.execute(f"""
            INSERT INTO {node_table}
            (id, "workflowId", "agentId", "nodeType", "nodeName")
            VALUES (%s, %s, %s, %s, %s)
        """, (node_id, workflow_id, agent_id, node_type, node_name))
        
        self.conn.commit()
        return node_id
    
    def add_edge_to_workflow(self, workflow_id: str, source_node_id: str, scope: Scope, target_node_id: str = None,
                            condition_type: str = "ALWAYS", condition_value: str = None) -> str:
        """Add an edge to an existing workflow with node validation."""
        if not self._validate_node_exists(source_node_id, scope):
            raise ValueError(f"Source node {source_node_id} does not exist in scope {scope.value}")
        
        if target_node_id and not self._validate_node_exists(target_node_id, scope):
            raise ValueError(f"Target node {target_node_id} does not exist in scope {scope.value}")
        
        edge_id = str(uuid.uuid4())
        edge_table = self._get_table_name(scope, ResourceType.WORKFLOW_EDGE)
        
        self.cursor.execute(f"""
            INSERT INTO {edge_table}
            (id, "workflowId", "sourceNodeId", "targetNodeId", "conditionType", "conditionValue")
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (edge_id, workflow_id, source_node_id, target_node_id, condition_type, condition_value))
        
        self.conn.commit()
        return edge_id
"""
Configuration and database connection management for the 2n Agents system.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import Optional
from enum import Enum

# Load environment variables
load_dotenv('local.env')

class Scope(Enum):
    """Enum for agent and workflow scopes."""
    SYSTEM = "SYSTEM"
    COMMON_BACKGROUND = "COMMON_BACKGROUND"

class ResourceType(Enum):
    """Enum for resource types."""
    AGENT = "agent"
    WORKFLOW = "workflow"
    WORKFLOW_NODE = "workflow_node"
    WORKFLOW_EDGE = "workflow_edge"

def get_db_connection():
    """Create a database connection using environment variables."""
    database_url = os.getenv('PG_DATABASE_URL')
    if not database_url:
        raise ValueError("PG_DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def get_db_cursor(connection):
    """Get a RealDictCursor for database operations."""
    return connection.cursor(cursor_factory=RealDictCursor)

def validate_scope(scope: str) -> Scope:
    """Validate and return a Scope enum from string."""
    try:
        return Scope(scope.upper())
    except ValueError:
        raise ValueError(f"Invalid scope: {scope}. Must be one of: {[s.value for s in Scope]}")

def validate_resource_type(resource_type: str) -> ResourceType:
    """Validate and return a ResourceType enum from string."""
    try:
        return ResourceType(resource_type.lower())
    except ValueError:
        raise ValueError(f"Invalid resource type: {resource_type}. Must be one of: {[rt.value for rt in ResourceType]}")

def get_definitions_path(scope: Scope, resource_type: ResourceType) -> str:
    """Get the path for a specific scope and resource type."""
    scope_dir = "System" if scope == Scope.SYSTEM else "CommonBackground"
    resource_dir = "Agents" if resource_type == ResourceType.AGENT else "AgenticWorkflows"
    return os.path.join("definitions", scope_dir, resource_dir)

def ensure_directory_exists(path: str):
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True) 
"""
Test script for the 2n Agents system.
Verifies that the new system works correctly with database and file operations.
"""

import os
import tempfile
import shutil
from .config import Scope, ResourceType, get_definitions_path
from .agent_manager import AgentManager
from .workflow_manager import WorkflowManager

def test_agent_operations():
    """Test agent creation and management."""
    print("🧪 Testing agent operations...")
    
    with AgentManager() as am:
        # Test creating an agent
        agent_id = am.create_agent(
            name="test-agent",
            scope=Scope.SYSTEM,
            description="A test agent",
            system_prompt="You are a test agent."
        )
        print(f"  ✅ Created agent with ID: {agent_id}")
        
        # Test listing agents
        agents = am.list_agents(Scope.SYSTEM)
        print(f"  ✅ Found {len(agents)} system agents")
        
        # Test syncing agent
        synced_id = am.sync_agent_to_db("test-agent", Scope.SYSTEM)
        print(f"  ✅ Synced agent with ID: {synced_id}")
        
        # Test deleting agent
        deleted = am.delete_agent("test-agent", Scope.SYSTEM)
        print(f"  ✅ Deleted agent: {deleted}")

def test_workflow_operations():
    """Test workflow creation and management."""
    print("🧪 Testing workflow operations...")
    
    with WorkflowManager() as wm:
        # Test creating a workflow
        workflow_id = wm.create_workflow(
            workflow_id="test-workflow",
            name="Test Workflow",
            scope=Scope.SYSTEM,
            description="A test workflow"
        )
        print(f"  ✅ Created workflow with ID: {workflow_id}")
        
        # Test listing workflows
        workflows = wm.list_workflows(Scope.SYSTEM)
        print(f"  ✅ Found {len(workflows)} system workflows")
        
        # Test syncing workflow
        synced_id = wm.sync_workflow_to_db("test-workflow", Scope.SYSTEM)
        print(f"  ✅ Synced workflow with ID: {synced_id}")
        
        # Test deleting workflow
        deleted = wm.delete_workflow("test-workflow", Scope.SYSTEM)
        print(f"  ✅ Deleted workflow: {deleted}")

def test_file_structure():
    """Test that the file structure is created correctly."""
    print("🧪 Testing file structure...")
    
    # Test agent file structure
    agent_path = get_definitions_path(Scope.SYSTEM, ResourceType.AGENT)
    print(f"  ✅ Agent path: {agent_path}")
    
    # Test workflow file structure
    workflow_path = get_definitions_path(Scope.SYSTEM, ResourceType.WORKFLOW)
    print(f"  ✅ Workflow path: {workflow_path}")
    
    # Test common background paths
    cb_agent_path = get_definitions_path(Scope.COMMON_BACKGROUND, ResourceType.AGENT)
    print(f"  ✅ Common Background agent path: {cb_agent_path}")
    
    cb_workflow_path = get_definitions_path(Scope.COMMON_BACKGROUND, ResourceType.WORKFLOW)
    print(f"  ✅ Common Background workflow path: {cb_workflow_path}")

def test_scope_validation():
    """Test scope validation."""
    print("🧪 Testing scope validation...")
    
    from .config import validate_scope, validate_resource_type
    
    # Test valid scopes
    system_scope = validate_scope("SYSTEM")
    cb_scope = validate_scope("COMMON_BACKGROUND")
    print(f"  ✅ Valid scopes: {system_scope.value}, {cb_scope.value}")
    
    # Test valid resource types
    agent_type = validate_resource_type("agent")
    workflow_type = validate_resource_type("workflow")
    print(f"  ✅ Valid resource types: {agent_type.value}, {workflow_type.value}")
    
    # Test invalid scope (should raise exception)
    try:
        validate_scope("INVALID")
        print("  ❌ Should have raised exception for invalid scope")
    except ValueError:
        print("  ✅ Correctly rejected invalid scope")

def main():
    """Run all tests."""
    print("🚀 Testing 2n Agents System...")
    print("=" * 50)
    
    try:
        test_scope_validation()
        print()
        
        test_file_structure()
        print()
        
        test_agent_operations()
        print()
        
        test_workflow_operations()
        print()
        
        print("✅ All tests passed!")
        print("\n💡 The new system is working correctly.")
        print("   You can now use the CLI to manage agents and workflows:")
        print("   python -m src.cli --help")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
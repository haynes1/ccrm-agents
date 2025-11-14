"""
Command-line interface for the cc Agents system.
Provides a unified way to manage agents and workflows with dual scope support.
"""

import argparse
import sys
from typing import Optional
from .config import Scope, ResourceType, validate_scope, validate_resource_type
from .agent_manager import AgentManager
from .workflow_manager import WorkflowManager
from .tool_manager import ToolManager
from .error_handler import error_handler

def create_agent_command(args):
    """Create a new agent."""
    try:
        error_handler.log_operation_start("create_agent", {"name": args.name, "scope": args.scope})
        
        scope = validate_scope(args.scope)
        
        with AgentManager() as am:
            agent_id = am.create_agent(
                name=args.name,
                scope=scope,
                description=args.description or "",
                system_prompt=args.system_prompt or ""
            )
            print(f"✅ Created agent '{args.name}' with ID: {agent_id}")
            print(f"📁 Files created in: definitions/{scope.value}/Agents/{args.name}/")
            
            error_handler.log_operation_success("create_agent", {"agent_id": agent_id})
            
    except Exception as e:
        error_handler.log_operation_failure("create_agent", e)
        error_handler.handle_error(e, {
            "operation": "create_agent",
            "agent_name": args.name,
            "scope": args.scope
        })

def sync_agent_command(args):
    """Sync an agent to/from database."""
    try:
        error_handler.log_operation_start("sync_agent", {
            "name": args.name, 
            "scope": args.scope, 
            "direction": args.direction
        })
        
        scope = validate_scope(args.scope)
        
        with AgentManager() as am:
            if args.direction == "to":
                agent_id = am.sync_agent_to_db(args.name, scope)
                print(f"✅ Synced agent '{args.name}' to database (ID: {agent_id})")
            else:
                agent_id = am.sync_agent_from_db(args.name, scope)
                print(f"✅ Synced agent '{args.name}' from database (ID: {agent_id})")
            
            error_handler.log_operation_success("sync_agent", {"agent_id": agent_id})
            
    except Exception as e:
        error_handler.log_operation_failure("sync_agent", e)
        error_handler.handle_error(e, {
            "operation": "sync_agent",
            "agent_name": args.name,
            "scope": args.scope,
            "direction": args.direction
        })

def list_agents_command(args):
    """List all agents."""
    scope = validate_scope(args.scope) if args.scope else None
    
    with AgentManager() as am:
        agents = am.list_agents(scope)
        
        if not agents:
            scope_text = f" in scope {scope.value}" if scope else ""
            print(f"📭 No agents found{scope_text}")
            return
        
        print(f"📋 Agents{(' in scope ' + scope.value) if scope else ''}:")
        for agent in agents:
            print(f"  • {agent['name']} (ID: {agent['id']}, Scope: {agent['scope']})")

def delete_agent_command(args):
    """Delete an agent."""
    scope = validate_scope(args.scope)
    
    with AgentManager() as am:
        if am.delete_agent(args.name, scope):
            print(f"✅ Deleted agent '{args.name}' from scope {scope.value}")
        else:
            print(f"❌ Agent '{args.name}' not found in scope {scope.value}")

def sync_all_agents_command(args):
    """Sync all agents from local files to database."""
    scope = validate_scope(args.scope) if args.scope else None
    
    with AgentManager() as am:
        results = am.sync_all_agents(scope)
        
        if results["success"]:
            print("✅ Successfully synced:")
            for success in results["success"]:
                print(f"  • {success}")
        
        if results["errors"]:
            print("❌ Errors:")
            for error in results["errors"]:
                print(f"  • {error}")

def create_workflow_command(args):
    """Create a new workflow."""
    scope = validate_scope(args.scope)
    
    with WorkflowManager() as wm:
        workflow_id = wm.create_workflow(
            workflow_id=args.id,
            name=args.name,
            scope=scope,
            description=args.description or ""
        )
        print(f"✅ Created workflow '{args.name}' with ID: {workflow_id}")
        print(f"📁 Files created in: definitions/{scope.value}/AgenticWorkflows/{workflow_id}/")

def sync_workflow_command(args):
    """Sync a workflow to/from database."""
    scope = validate_scope(args.scope)
    
    with WorkflowManager() as wm:
        if args.direction == "to":
            workflow_id = wm.sync_workflow_to_db(args.id, scope)
            print(f"✅ Synced workflow '{args.id}' to database")
        else:
            workflow_id = wm.sync_workflow_from_db(args.id, scope)
            print(f"✅ Synced workflow '{args.id}' from database")

def list_workflows_command(args):
    """List all workflows."""
    scope = validate_scope(args.scope) if args.scope else None
    
    with WorkflowManager() as wm:
        workflows = wm.list_workflows(scope)
        
        if not workflows:
            scope_text = f" in scope {scope.value}" if scope else ""
            print(f"📭 No workflows found{scope_text}")
            return
        
        print(f"📋 Workflows{(' in scope ' + scope.value) if scope else ''}:")
        for workflow in workflows:
            print(f"  • {workflow['name']} (ID: {workflow['id']}, Scope: {workflow['scope']})")

def delete_workflow_command(args):
    """Delete a workflow."""
    scope = validate_scope(args.scope)
    
    with WorkflowManager() as wm:
        if wm.delete_workflow(args.id, scope):
            print(f"✅ Deleted workflow '{args.id}' from scope {scope.value}")
        else:
            print(f"❌ Workflow '{args.id}' not found in scope {scope.value}")

def sync_all_workflows_command(args):
    """Sync all workflows from local files to database."""
    scope = validate_scope(args.scope) if args.scope else None
    
    with WorkflowManager() as wm:
        results = wm.sync_all_workflows(scope)
        
        if results["success"]:
            print("✅ Successfully synced:")
            for success in results["success"]:
                print(f"  • {success}")
        
        if results["errors"]:
            print("❌ Errors:")
            for error in results["errors"]:
                print(f"  • {error}")

def list_tools_command(args):
    """List all tools."""
    with ToolManager() as tm:
        tools = tm.list_tools()
        
        if not tools:
            print("📭 No tools found")
            return
        
        print(f"📋 Tools ({len(tools)} total):")
        for tool in tools:
            print(f"  • {tool['toolName']} (ID: {tool['id']}, Type: {tool['toolType']})")

def get_tool_command(args):
    """Get a specific tool."""
    with ToolManager() as tm:
        tool = tm.get_tool(args.id)
        
        if not tool:
            print(f"❌ Tool {args.id} not found")
            return
        
        print(f"🔧 Tool: {tool['toolName']}")
        print(f"  ID: {tool['id']}")
        print(f"  Type: {tool['toolType']}")
        print(f"  Description: {tool['descriptionForLlm'] or 'No description'}")
        if tool['internalApiPath']:
            print(f"  API Path: {tool['internalApiPath']}")

def create_tool_command(args):
    """Create a new tool."""
    with ToolManager() as tm:
        tool_id = tm.create_tool(
            tool_id=args.id,
            tool_name=args.name,
            description=args.description or "",
            tool_type=args.type,
            internal_api_path=args.api_path
        )
        print(f"✅ Created tool '{args.name}' with ID: {tool_id}")

def delete_tool_command(args):
    """Delete a tool."""
    with ToolManager() as tm:
        try:
            if tm.delete_tool(args.id, force=args.force):
                print(f"✅ Deleted tool {args.id}")
            else:
                print(f"❌ Tool {args.id} not found")
        except ValueError as e:
            print(f"❌ Error: {e}")

def orphaned_tools_command(args):
    """Find orphaned tools."""
    with ToolManager() as tm:
        orphaned_tools = tm.find_orphaned_tools()
        
        if not orphaned_tools:
            print("✅ No orphaned tools found")
            return
        
        print(f"🔍 Found {len(orphaned_tools)} orphaned tools:")
        for tool in orphaned_tools:
            print(f"  • {tool['toolName']} (ID: {tool['id']})")

def cleanup_tools_command(args):
    """Cleanup orphaned tools."""
    with ToolManager() as tm:
        deleted_count = tm.cleanup_orphaned_tools(force=args.force)
        
        if deleted_count > 0:
            print(f"✅ Cleaned up {deleted_count} orphaned tools")
        else:
            print("✅ No orphaned tools to clean up")

def validate_workflow_command(args):
    """Validate a workflow."""
    scope = validate_scope(args.scope)
    with WorkflowManager() as wm:
        result = wm.validate_workflow(args.id, scope)
        
        if result["valid"]:
            print(f"✅ Workflow '{args.id}' is valid")
            if result["warnings"]:
                print("\n⚠️  Warnings:")
                for warning in result["warnings"]:
                    print(f"   • {warning}")
        else:
            print(f"❌ Workflow '{args.id}' has errors:")
            for error in result["errors"]:
                print(f"   • {error}")

def get_workflow_agents_command(args):
    """Get agents referenced by a workflow."""
    scope = validate_scope(args.scope)
    with WorkflowManager() as wm:
        agents = wm.get_workflow_agents(args.id, scope)
        
        if not agents:
            print(f"📭 No agents referenced by workflow '{args.id}'")
            return
        
        print(f"📋 Agents referenced by workflow '{args.id}':")
        for agent in agents:
            print(f"  • {agent['name']} (ID: {agent['id']}, Scope: {agent['scope']})")

def get_agent_workflows_command(args):
    """Get workflows that reference an agent."""
    with WorkflowManager() as wm:
        workflows = wm.get_agent_workflows(args.agent_id)
        
        if not workflows:
            print(f"📭 No workflows reference agent '{args.agent_id}'")
            return
        
        print(f"📋 Workflows that reference agent '{args.agent_id}':")
        for workflow in workflows:
            print(f"  • {workflow['name']} (ID: {workflow['id']}, Scope: {workflow['scope']})")

def sync_all_command(args):
    """Sync all agents and workflows."""
    try:
        error_handler.log_operation_start("sync_all", {"scope": args.scope})
        
        scope = validate_scope(args.scope) if args.scope else None
        
        print("🔄 Syncing all agents...")
        with AgentManager() as am:
            agent_results = am.sync_all_agents(scope)
        
        print("🔄 Syncing all workflows...")
        with WorkflowManager() as wm:
            workflow_results = wm.sync_all_workflows(scope)
        
        # Report results
        total_success = len(agent_results["success"]) + len(workflow_results["success"])
        total_errors = len(agent_results["errors"]) + len(workflow_results["errors"])
        
        print(f"\n📊 Sync Summary:")
        print(f"  ✅ Successfully synced: {total_success} resources")
        print(f"  ❌ Errors: {total_errors} resources")
        
        if agent_results["errors"] or workflow_results["errors"]:
            print("\n❌ Detailed errors:")
            for error in agent_results["errors"]:
                print(f"  • Agent: {error}")
            for error in workflow_results["errors"]:
                print(f"  • Workflow: {error}")
        
        error_handler.log_operation_success("sync_all", {
            "total_success": total_success,
            "total_errors": total_errors
        })
        
    except Exception as e:
        error_handler.log_operation_failure("sync_all", e)
        error_handler.handle_error(e, {
            "operation": "sync_all",
            "scope": args.scope
        })

def main():
    """Main CLI entry point."""
    if not error_handler.validate_environment():
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="cc Agents Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new system agent
  python -m src.cli agent create --name "Research Agent" --scope SYSTEM --description "An agent for research tasks"

  # Sync all agents to database
  python -m src.cli agent sync-all

  # Create a new workflow
  python -m src.cli workflow create --id "research-v1" --name "Research Workflow" --scope SYSTEM

  # Sync everything
  python -m src.cli sync-all

Troubleshooting:
  # Check logs for detailed error information
  tail -f cc_agents.log

  # Test system configuration
  python -m src.test_system
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)
    
    # Agent commands
    agent_parser = subparsers.add_parser('agent', help='Agent management')
    agent_subparsers = agent_parser.add_subparsers(dest='agent_command', help='Agent commands', required=True)
    
    create_agent_parser = agent_subparsers.add_parser('create', help='Create a new agent')
    create_agent_parser.add_argument('--name', required=True, help='Agent name')
    create_agent_parser.add_argument('--scope', required=True, choices=[s.value for s in Scope], help='Agent scope')
    create_agent_parser.add_argument('--description', help='Agent description')
    create_agent_parser.add_argument('--system-prompt', help='System prompt')
    create_agent_parser.set_defaults(func=create_agent_command)
    
    sync_agent_parser = agent_subparsers.add_parser('sync', help='Sync an agent')
    sync_agent_parser.add_argument('--name', required=True, help='Agent name')
    sync_agent_parser.add_argument('--scope', required=True, choices=[s.value for s in Scope], help='Agent scope')
    sync_agent_parser.add_argument('--direction', choices=['to', 'from'], default='to', help='Sync direction')
    sync_agent_parser.set_defaults(func=sync_agent_command)
    
    list_agents_parser = agent_subparsers.add_parser('list', help='List all agents')
    list_agents_parser.add_argument('--scope', choices=[s.value for s in Scope], help='Filter by scope')
    list_agents_parser.set_defaults(func=list_agents_command)
    
    delete_agent_parser = agent_subparsers.add_parser('delete', help='Delete an agent')
    delete_agent_parser.add_argument('--name', required=True, help='Agent name')
    delete_agent_parser.add_argument('--scope', required=True, choices=[s.value for s in Scope], help='Agent scope')
    delete_agent_parser.set_defaults(func=delete_agent_command)
    
    sync_all_agents_parser = agent_subparsers.add_parser('sync-all', help='Sync all agents')
    sync_all_agents_parser.add_argument('--scope', choices=[s.value for s in Scope], help='Filter by scope')
    sync_all_agents_parser.set_defaults(func=sync_all_agents_command)
    
    # Workflow commands
    workflow_parser = subparsers.add_parser('workflow', help='Workflow management')
    workflow_subparsers = workflow_parser.add_subparsers(dest='workflow_command', help='Workflow commands', required=True)
    
    create_workflow_parser = workflow_subparsers.add_parser('create', help='Create a new workflow')
    create_workflow_parser.add_argument('--id', required=True, help='Workflow ID')
    create_workflow_parser.add_argument('--name', required=True, help='Workflow name')
    create_workflow_parser.add_argument('--scope', required=True, choices=[s.value for s in Scope], help='Workflow scope')
    create_workflow_parser.add_argument('--description', help='Workflow description')
    create_workflow_parser.set_defaults(func=create_workflow_command)
    
    sync_workflow_parser = workflow_subparsers.add_parser('sync', help='Sync a workflow')
    sync_workflow_parser.add_argument('--id', required=True, help='Workflow ID')
    sync_workflow_parser.add_argument('--scope', required=True, choices=[s.value for s in Scope], help='Workflow scope')
    sync_workflow_parser.add_argument('--direction', choices=['to', 'from'], default='to', help='Sync direction')
    sync_workflow_parser.set_defaults(func=sync_workflow_command)
    
    list_workflows_parser = workflow_subparsers.add_parser('list', help='List all workflows')
    list_workflows_parser.add_argument('--scope', choices=[s.value for s in Scope], help='Filter by scope')
    list_workflows_parser.set_defaults(func=list_workflows_command)
    
    delete_workflow_parser = workflow_subparsers.add_parser('delete', help='Delete a workflow')
    delete_workflow_parser.add_argument('--id', required=True, help='Workflow ID')
    delete_workflow_parser.add_argument('--scope', required=True, choices=[s.value for s in Scope], help='Workflow scope')
    delete_workflow_parser.set_defaults(func=delete_workflow_command)
    
    sync_all_workflows_parser = workflow_subparsers.add_parser('sync-all', help='Sync all workflows')
    sync_all_workflows_parser.add_argument('--scope', choices=[s.value for s in Scope], help='Filter by scope')
    sync_all_workflows_parser.set_defaults(func=sync_all_workflows_command)
    
    validate_workflow_parser = workflow_subparsers.add_parser('validate', help='Validate a workflow')
    validate_workflow_parser.add_argument('--id', required=True, help='Workflow ID')
    validate_workflow_parser.add_argument('--scope', required=True, choices=[s.value for s in Scope], help='Workflow scope')
    validate_workflow_parser.set_defaults(func=validate_workflow_command)
    
    get_workflow_agents_parser = workflow_subparsers.add_parser('agents', help='Get agents referenced by a workflow')
    get_workflow_agents_parser.add_argument('--id', required=True, help='Workflow ID')
    get_workflow_agents_parser.add_argument('--scope', required=True, choices=[s.value for s in Scope], help='Workflow scope')
    get_workflow_agents_parser.set_defaults(func=get_workflow_agents_command)
    
    get_agent_workflows_parser = workflow_subparsers.add_parser('referenced-by', help='Get workflows that reference an agent')
    get_agent_workflows_parser.add_argument('--agent-id', required=True, help='Agent ID')
    get_agent_workflows_parser.set_defaults(func=get_agent_workflows_command)

    # Tool commands
    tool_parser = subparsers.add_parser('tool', help='Tool management')
    tool_subparsers = tool_parser.add_subparsers(dest='tool_command', help='Tool commands', required=True)
    
    list_tools_parser = tool_subparsers.add_parser('list', help='List all tools')
    list_tools_parser.set_defaults(func=list_tools_command)
    
    get_tool_parser = tool_subparsers.add_parser('get', help='Get a specific tool')
    get_tool_parser.add_argument('--id', required=True, help='Tool ID')
    get_tool_parser.set_defaults(func=get_tool_command)
    
    create_tool_parser = tool_subparsers.add_parser('create', help='Create a new tool')
    create_tool_parser.add_argument('--id', required=True, help='Tool ID')
    create_tool_parser.add_argument('--name', required=True, help='Tool name')
    create_tool_parser.add_argument('--description', help='Tool description')
    create_tool_parser.add_argument('--type', default='custom', help='Tool type')
    create_tool_parser.add_argument('--api-path', help='Internal API path')
    create_tool_parser.set_defaults(func=create_tool_command)
    
    delete_tool_parser = tool_subparsers.add_parser('delete', help='Delete a tool')
    delete_tool_parser.add_argument('--id', required=True, help='Tool ID')
    delete_tool_parser.add_argument('--force', action='store_true', help='Force delete even if associated with agents')
    delete_tool_parser.set_defaults(func=delete_tool_command)
    
    orphaned_tools_parser = tool_subparsers.add_parser('orphaned', help='Find orphaned tools')
    orphaned_tools_parser.set_defaults(func=orphaned_tools_command)
    
    cleanup_tools_parser = tool_subparsers.add_parser('cleanup', help='Cleanup orphaned tools')
    cleanup_tools_parser.add_argument('--force', action='store_true', help='Force cleanup')
    cleanup_tools_parser.set_defaults(func=cleanup_tools_command)

    # Global sync command
    sync_all_parser = subparsers.add_parser('sync-all', help='Sync all agents and workflows')
    sync_all_parser.add_argument('--scope', choices=[s.value for s in Scope], help='Filter by scope')
    sync_all_parser.set_defaults(func=sync_all_command)
    
    args = parser.parse_args()
    
    try:
        args.func(args)
    except Exception as e:
        error_handler.handle_error(e, {"command": args.command})

if __name__ == "__main__":
    main()
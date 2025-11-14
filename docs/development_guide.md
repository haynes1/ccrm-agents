# Development Guide

Welcome to the 2n-agents repository! This guide will help you understand how to work with agents and agentic workflows in this system.

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Core Concepts](#core-concepts)
3. [Directory Structure](#directory-structure)
4. [Quick Start](#quick-start)
5. [Creating Agents](#creating-agents)
6. [Creating Workflows](#creating-workflows)
7. [Scripts Reference](#scripts-reference)
8. [Database Schema](#database-schema)

## Repository Overview

This repository is designed to manage and control AI agents and agentic workflows. It provides a structured way to define, version, and deploy both system-level and common background agents and workflows.

### Key Features

- **Dual Scope Support**: Define agents and workflows for both system-wide use and common background contexts
- **Version Control**: Track changes to agent definitions and workflow configurations
- **Database Integration**: Sync definitions to a database for runtime execution
- **Scriptable Operations**: Python scripts for common development tasks

## Version Control Strategy

This system is designed with **the repository as the source of truth** for version control, while the database serves as runtime storage. This approach enables proper collaboration and version control for agent definitions.

### Repository as Source of Truth

- **Git History**: All agent and workflow definitions are tracked in git with complete history
- **Collaboration**: Multiple engineers can work on definitions and merge changes through pull requests
- **Code Review**: Changes can be reviewed before being deployed
- **Rollbacks**: Easy to revert changes using git commands
- **Branching**: Work on features in separate branches before merging

### Database as Runtime Storage

- **Execution**: Database stores the runtime definitions for the application
- **Performance**: Fast lookups for the running system
- **Consistency**: Ensures the running system matches the repository

### Bidirectional Sync Support

The system supports syncing in both directions:

#### Repository → Database (Primary Workflow)
```bash
# Sync all definitions from repository to database
python -m src.cli sync-all

# Sync specific agent from repository to database
python -m src.cli agent sync --name "Agent Name" --scope SYSTEM --direction to
```

#### Database → Repository (Recovery/Import)
```bash
# Pull agent from database to repository (useful for recovery)
python -m src.cli agent sync --name "Agent Name" --scope SYSTEM --direction from

# Pull workflow from database to repository (useful for recovery)
python -m src.cli workflow sync --id "workflow-id" --scope SYSTEM --direction from
```

### Recommended Team Workflow

#### Development Process
```bash
# 1. Create feature branch
git checkout -b feature/new-agent

# 2. Create/modify agents/workflows
python -m src.cli agent create --name "New Agent" --scope SYSTEM
# Edit the files in definitions/

# 3. Test locally
python -m src.cli sync-all
# Test the agent/workflow

# 4. Commit and push
git add definitions/
git commit -m "Add new agent for research tasks"
git push origin feature/new-agent

# 5. Create pull request for review
```

#### Production Deployment
```bash
# 1. Merge approved changes
git checkout main
git pull origin main

# 2. Deploy to database
python -m src.cli sync-all

# 3. Verify deployment
python -m src.cli agent list
python -m src.cli workflow list
```

#### Recovery Scenarios
```bash
# If database has changes not in repository (emergency fixes, etc.)
python -m src.cli agent sync --name "Agent Name" --scope SYSTEM --direction from
# Review the changes, then commit
git add definitions/System/Agents/Agent-Name/
git commit -m "Recover agent changes from database"
```

## Core Concepts

### Agents
An **Agent** is a specific AI persona with:
- A defined system prompt that establishes its behavior and capabilities
- A set of available tools it can use
- A scope (SYSTEM or COMMON_BACKGROUND)

### Agentic Workflows
An **Agentic Workflow** is a state machine that:
- Defines how multiple agents work together
- Specifies the flow of control between agents
- Handles routing logic and decision points
- Can include tool execution nodes

### Scopes
- **System**: Agents and workflows available globally across the entire system
- **Common Background**: Agents and workflows specific to common background contexts

## Directory Structure

```
2n-agents/
├── definitions/           # Source of truth for agents and workflows
│   ├── System/           # System-scoped definitions
│   │   ├── Agents/       # System agents
│   │   └── AgenticWorkflows/  # System workflows
│   └── CommonBackground/ # Common background definitions
│       ├── Agents/       # Common background agents
│       └── AgenticWorkflows/  # Common background workflows
├── src/                  # Python scripts for database operations
├── docs/                 # Documentation
│   ├── development_guide.md
│   └── agentic_workflow_system.md
├── schema.ts             # TypeScript schema definitions
└── README.md            # Project overview
```

## Quick Start

### Prerequisites
1. Python 3.8+ installed
2. Database access configured (see `local.env` for configuration)
3. Required Python packages installed (`pip install -r requirements.txt`)

### First Steps
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 2n-agents
   ```

2. **Set up your environment**
   ```bash
   pip install -r requirements.txt
   cp local.env.example local.env  # if available
   # Edit local.env with your database credentials
   ```

3. **Explore existing definitions**
   ```bash
   ls definitions/System/Agents/
   ls definitions/CommonBackground/Agents/
   ```

4. **Understand the dependency order**
   - **Agents must be created before workflows**
   - **Workflows reference agents by ID**
   - **Always validate workflows after creation**

## Creating Agents

**⚠️ IMPORTANT: Agent Creation Must Precede Workflow Creation**

Before creating any workflows, you **must** first create and define all agents that the workflow will reference. The system validates that all referenced agents exist before allowing workflow creation.

### Development Workflow Order
1. **Create Agents First** - Define all agents that your workflow will use
2. **Sync Agents to Database** - Ensure agents are available in the database
3. **Create Workflow** - Define workflow that references the existing agents
4. **Validate Workflow** - Use validation to ensure all references are correct

### Step 1: Create Agent Directory
Create a new directory under the appropriate scope:

```bash
# For a system agent
mkdir -p definitions/System/Agents/my-new-agent

# For a common background agent
mkdir -p definitions/CommonBackground/Agents/my-new-agent
```

### Step 2: Define Agent Files
Each agent needs two files:

**`systemPrompt.md`** - The agent's system prompt:
```markdown
# My New Agent

You are an expert at [specific task]. Your role is to [describe behavior].

## Instructions
- [List specific instructions]
- [Define expected outputs]
- [Specify any constraints]

## Tools Available
- [List available tools if any]
```

**`jsonSchema.json`** - Agent metadata and configuration:
```json
{
  "name": "My New Agent",
  "description": "A brief description of what this agent does",
  "scope": "SYSTEM",
  "tools": ["tool1", "tool2"],
  "version": "1.0.0"
}
```

### Step 3: Sync to Database
```bash
python src/sync_to_db.py --agent my-new-agent --scope SYSTEM
```

## Creating Workflows

**⚠️ PREREQUISITE: All Referenced Agents Must Exist**

Before creating a workflow, ensure that all agents referenced in the workflow nodes have been created and synced to the database. The system will validate agent existence and fail if any referenced agents are missing.

### Prerequisites Checklist
- [ ] All agents referenced in workflow nodes have been created
- [ ] All agents have been synced to the database
- [ ] Agent IDs in workflow match the actual agent IDs in the database

### Step-by-Step Guide

1.  **Create a Directory**: Add a new directory for your workflow under `definitions/<Scope>/AgenticWorkflows/<YourWorkflowName>/`.
2.  **Define `workflow.json`**: Inside this new directory, create a `workflow.json` file. This file must contain a literal, 1-to-1 representation of the database records you intend to create.

    *   **You are responsible for all UUIDs.** You must generate new, valid UUIDs for the main workflow `id`, for every `id` in the `nodes` array, and for every `id` in the `edges` array.
    *   The `agentId`, `sourceNodeId`, and `targetNodeId` fields must also contain the correct, real UUIDs to link the workflow together. You can use an online UUID generator or a command-line tool like `uuidgen`.
3.  **Sync to Database**: Once your `workflow.json` is complete and contains only real UUIDs, sync it to the database:

    ```bash
    python3 src/cli.py workflow sync --scope <YourScope> --id <YourWorkflowName>
    ```
4.  **Validate**: After syncing, you can validate the workflow to ensure all references are correct and there are no orphaned nodes:
    ```bash
    python3 src/cli.py workflow validate --id <YourWorkflowName>
    ```

#### Important Considerations

*   **Repository is the Source of Truth**: Always remember that the final, committed `workflow.json` in the repository is the definitive source of truth. The database is merely a runtime mirror.
*   **Agent Creation Must Precede Workflow Creation**: Before creating any workflows, you **must** first create and define all agents that the workflow will reference. The system validates that all referenced agents exist before allowing workflow creation.

### Common Validation Errors
- **Agent Not Found**: `Agent agent-uuid referenced by node first_agent does not exist`
  - **Solution**: Create the missing agent first, then retry workflow creation
- **Invalid Node Reference**: `Source node node-1 in workflow my-new-workflow does not exist`
  - **Solution**: Check that all node IDs in edges match actual node IDs

### Troubleshooting Workflow Creation

**Problem**: Workflow validation fails with "Agent does not exist" errors

**Root Cause**: This happens when you try to create a workflow before creating the agents it references.

**Solution Steps**:
1. **Identify Missing Agents**: Check the validation error to see which agents are missing
2. **Create Missing Agents**: Follow the agent creation process for each missing agent
3. **Sync Agents to Database**: Ensure all agents are synced to the database
4. **Verify Agent IDs**: Make sure the agent IDs in your workflow match the actual agent IDs
5. **Retry Workflow Creation**: Validate and sync the workflow again

**Example**:
```bash
# Error: Agent a1b2c3d4-0001-4000-8000-000000000001 does not exist

# Step 1: Create the missing agent
python -m src.cli agent create --name "Research Agent" --scope SYSTEM

# Step 2: Verify the agent exists
python -m src.cli agent list

# Step 3: Update workflow with correct agent ID
# Edit workflow.json to use the correct agent ID

# Step 4: Retry workflow creation
python -m src.cli workflow validate --id "my-workflow"
python -m src.cli workflow sync --id "my-workflow" --scope SYSTEM
```

## Scripts Reference

### Unified CLI Interface

The new system provides a unified command-line interface for all operations:

**Main CLI** - Access all functionality through a single interface
```bash
# Show help
python -m src.cli --help

# Create a new system agent
python -m src.cli agent create --name "Research Agent" --scope SYSTEM --description "An agent for research tasks"

# Sync all agents to database
python -m src.cli agent sync-all

# Create a new workflow
python -m src.cli workflow create --id "research-v1" --name "Research Workflow" --scope SYSTEM

# Sync everything
python -m src.cli sync-all
```

### Agent Management

**Create Agent** - Create a new agent with dual scope support
```bash
python -m src.cli agent create --name "Agent Name" --scope SYSTEM --description "Description" --system-prompt "System prompt"
```

**Sync Agent** - Sync individual agents to/from database
```bash
# Sync to database (Repository → Database - Normal workflow)
python -m src.cli agent sync --name "Agent Name" --scope SYSTEM --direction to

# Sync from database (Database → Repository - Recovery workflow)
python -m src.cli agent sync --name "Agent Name" --scope SYSTEM --direction from
```

**List Agents** - List all agents with optional scope filtering
```bash
# List all agents
python -m src.cli agent list

# List only system agents
python -m src.cli agent list --scope SYSTEM
```

**Delete Agent** - Delete an agent from both database and local files
```bash
python -m src.cli agent delete --name "Agent Name" --scope SYSTEM
```

**Sync All Agents** - Sync all agents from local files to database
```bash
# Sync all agents
python -m src.cli agent sync-all

# Sync only system agents
python -m src.cli agent sync-all --scope SYSTEM
```

### Workflow Management

**Create Workflow** - Create a new workflow with dual scope support
```bash
python -m src.cli workflow create --id "workflow-id" --name "Workflow Name" --scope SYSTEM --description "Description"
```

**Sync Workflow** - Sync individual workflows to/from database
```bash
# Sync to database (Repository → Database - Normal workflow)
python -m src.cli workflow sync --id "workflow-id" --scope SYSTEM --direction to

# Sync from database (Database → Repository - Recovery workflow)
python -m src.cli workflow sync --id "workflow-id" --scope SYSTEM --direction from
```

**List Workflows** - List all workflows with optional scope filtering
```bash
# List all workflows
python -m src.cli workflow list

# List only system workflows
python -m src.cli workflow list --scope SYSTEM
```

**Delete Workflow** - Delete a workflow from both database and local files
```bash
python -m src.cli workflow delete --id "workflow-id" --scope SYSTEM
```

**Validate Workflow** - Validate a workflow and check for issues
```bash
python -m src.cli workflow validate --id "workflow-id"
```

**Get Workflow Agents** - List all agents referenced by a workflow
```bash
python -m src.cli workflow agents --id "workflow-id"
```

**Get Agent Workflows** - List all workflows that reference an agent
```bash
python -m src.cli workflow referenced-by --agent-id "agent-id"
```

**Sync All Workflows** - Sync all workflows from local files to database
```bash
# Sync all workflows
python -m src.cli workflow sync-all

# Sync only system workflows
python -m src.cli workflow sync-all --scope SYSTEM
```

### Tool Management

**List Tools** - List all tools in the system
```bash
python -m src.cli tool list
```

**Get Tool** - Get details of a specific tool
```bash
python -m src.cli tool get --id "tool-id"
```

**Create Tool** - Create a new tool
```bash
python -m src.cli tool create --id "tool-id" --name "Tool Name" --description "Tool description" --type "custom"
```

**Delete Tool** - Delete a tool (with safety checks)
```bash
# Safe delete (fails if tool is associated with agents)
python -m src.cli tool delete --id "tool-id"

# Force delete (removes associations and deletes tool)
python -m src.cli tool delete --id "tool-id" --force
```

**Find Orphaned Tools** - Find tools not associated with any agents
```bash
python -m src.cli tool orphaned
```

**Cleanup Orphaned Tools** - Remove tools not associated with any agents
```bash
# Preview orphaned tools
python -m src.cli tool cleanup

# Actually delete orphaned tools
python -m src.cli tool cleanup --force
```

### Global Operations

**Sync Everything** - Sync all agents and workflows at once
```bash
# Sync everything
python -m src.cli sync-all

# Sync only system resources
python -m src.cli sync-all --scope SYSTEM
```

### Database Management

**`database_reset.py`** - Reset database and clear all data
```bash
python -m src.database_reset
```

### Legacy Scripts

The old scripts are preserved in the `old_scripts/` directory for reference:
- `old_scripts/sync_to_db.py` - Old sync script (single scope only)
- `old_scripts/create_agent.py` - Old agent creation script
- `old_scripts/database_reset_sync.py` - Old database reset script
- And others...

## Database Schema

For detailed information about the database schema and how agents and workflows are stored, see [agentic_workflow_system.md](./agentic_workflow_system.md).

### Key Tables

- **`agents`**: Stores agent definitions with system prompts
- **`agent_workflows`**: Stores workflow blueprints
- **`agent_workflow_nodes`**: Defines nodes within workflows
- **`agent_workflow_edges`**: Defines connections between nodes

## Edge Case Handling

The system includes comprehensive edge case handling for both agent-tool and agent-workflow relationships:

### Tool Association Safety
- **Validation**: Tools and agents are validated before creating associations
- **Conflict Prevention**: Duplicate associations are prevented with `ON CONFLICT DO NOTHING`
- **Cascade Protection**: Tools with active associations cannot be deleted without `--force`

### Tool Lifecycle Management
- **Automatic Creation**: Tools are automatically created when referenced in agent schemas
- **Automatic Updates**: Tool definitions are updated when agent schemas change
- **Association Cleanup**: When tools are removed from agents, associations are properly cleaned up
- **Orphaned Tool Detection**: Tools not associated with any agents can be identified and cleaned up

### Agent-Workflow Separation
- **Independent Lifecycles**: Agents and workflows have completely independent lifecycles
- **Reference Validation**: Workflows validate that referenced agents exist before creating nodes
- **No Cascade Deletion**: Deleting a workflow does NOT delete any agents it references
- **Agent Independence**: Agents can exist without being referenced by any workflows
- **Workflow Validation**: Comprehensive validation ensures workflow integrity

### Database Consistency
- **Transaction Safety**: All operations use database transactions for consistency
- **Rollback Support**: Failed operations are properly rolled back
- **Constraint Enforcement**: Database constraints prevent invalid relationships

## Best Practices

### Agent Development
1. **Clear Prompts**: Write system prompts that are specific and actionable
2. **Version Control**: Use semantic versioning for agent updates
3. **Testing**: Test agents in isolation before adding to workflows
4. **Documentation**: Document agent capabilities and limitations

### Workflow Development
1. **Start Simple**: Begin with single-agent workflows
2. **Test Incrementally**: Add complexity gradually
3. **Clear Routing**: Ensure edge conditions are well-defined
4. **Error Handling**: Consider failure scenarios in your workflow design

### Repository Management
1. **Scope Appropriately**: Use SYSTEM scope for global agents, COMMON_BACKGROUND for specific contexts
2. **Consistent Naming**: Use descriptive, consistent names for agents and workflows
3. **Regular Syncs**: Keep database in sync with repository changes
4. **Backup**: Regularly backup your definitions directory

## Error Handling and Logging

The system provides comprehensive error handling and logging to help you understand and resolve issues quickly.

### Log Files

All operations are logged to `2n_agents.log` in the project root:

```bash
# View recent logs
tail -f 2n_agents.log

# Search for errors
grep ERROR 2n_agents.log

# Search for specific operations
grep "create_agent" 2n_agents.log
```

### Error Types and Solutions

The system classifies errors into different types and provides specific troubleshooting tips:

#### Database Connection Errors
```bash
❌ Database connection failed: connection to server at "localhost" failed

💡 Troubleshooting:
   • Check that PostgreSQL is running: `brew services list | grep postgresql`
   • Verify your database connection in `local.env`
   • Test connection: `psql $PG_DATABASE_URL`
   • Check network connectivity to database host
```

#### Validation Errors
```bash
❌ Validation error: Invalid scope: INVALID. Must be one of: ['SYSTEM', 'COMMON_BACKGROUND']

💡 Troubleshooting:
   • Run `python -m src.cli --help` to see valid options
   • Check that all required parameters are provided
   • Verify scope values: SYSTEM or COMMON_BACKGROUND
   • Ensure agent/workflow names are valid
```

#### File Not Found Errors
```bash
❌ File not found: Agent directory not found: definitions/System/Agents/my-agent

💡 Troubleshooting:
   • Run `python -m src.cli agent list` to see available agents
   • Run `python -m src.cli workflow list` to see available workflows
   • Check that files exist in `definitions/` directory
   • Verify file permissions: `ls -la definitions/`
```

#### Configuration Errors
```bash
❌ Configuration error: PG_DATABASE_URL environment variable not set

💡 Troubleshooting:
   • Check that `local.env` exists and is properly configured
   • Verify all required environment variables are set
   • Run `python -m src.test_system` to test configuration
   • Check that all required Python packages are installed
```

### Environment Validation

The CLI automatically validates your environment before running commands:

```bash
# Missing local.env
❌ Configuration file 'local.env' not found
💡 Please create local.env with your database configuration

# Missing environment variables
❌ Missing required environment variables: PG_DATABASE_URL
💡 Please set these variables in your local.env file
```

### Debugging Tips

1. **Check Logs**: Always check `2n_agents.log` for detailed error information
2. **Test Configuration**: Run `python -m src.test_system` to verify your setup
3. **Verbose Output**: Some commands provide detailed output about what they're doing
4. **Step by Step**: Try operations with smaller scope first (e.g., single agent vs. all agents)

### Common Issues

**Agent not found in database**
- Check that the agent was synced: `python -m src.cli agent sync --name agent-name --scope SYSTEM`
- Verify the agent directory structure is correct
- Check logs for detailed error information

**Workflow execution fails**
- Check that all referenced agents exist in the database
- Verify edge conditions are properly defined
- Ensure entrypoint node is correctly set

**Sync errors**
- Check database connectivity in `local.env`
- Verify Python dependencies are installed
- Check file permissions on definitions directory
- Review logs for specific error details

### Getting Help

1. **Check Logs**: `tail -f 2n_agents.log` for detailed error information
2. **Test System**: `python -m src.test_system` to verify configuration
3. **Review Documentation**: Check [agentic_workflow_system.md](./agentic_workflow_system.md) for technical details
4. **Review Examples**: Look at existing agent and workflow definitions for patterns

## Next Steps

1. **Explore Existing Definitions**: Look at the agents and workflows in `definitions/` to understand patterns
2. **Create Your First Agent**: Follow the agent creation steps above
3. **Build a Simple Workflow**: Start with a single-agent workflow
4. **Contribute**: Add new agents and workflows to expand the system's capabilities

For more detailed technical information, see [agentic_workflow_system.md](./agentic_workflow_system.md). 
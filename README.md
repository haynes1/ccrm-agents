# 2n Agents

A comprehensive system for managing and deploying AI agents and agentic workflows with configurable tools and capabilities.

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 2n-agents
   ```

2. **Set up your environment**
   ```bash
   pip install -r requirements.txt
   # Configure your database connection in local.env
   ```

3. **Explore the system**
   ```bash
   # See what agents are available
   ls definitions/System/Agents/
   ls definitions/CommonBackground/Agents/
   
   # See what workflows are defined
   ls definitions/System/AgenticWorkflows/
   ```

4. **Read the documentation**
   - 📖 [Development Guide](docs/development_guide.md) - Complete guide for working with agents and workflows
   - 🔧 [Technical Reference](docs/agentic_workflow_system.md) - Database schema and system architecture

## 🎯 What This System Does

This repository provides a structured way to:

- **Define AI Agents**: Create reusable AI personas with specific system prompts and tool sets
- **Build Agentic Workflows**: Orchestrate multiple agents into complex, state-driven processes
- **Manage Dual Scopes**: Support both system-wide agents and common background contexts
- **Version Control Everything**: Track changes to agent definitions and workflow configurations with git
- **Sync with Runtime**: Deploy definitions to a database for execution

## 🔄 Version Control Strategy

**Repository as Source of Truth**: This system treats the repository as the source of truth for version control, while the database serves as runtime storage. This enables:

- **Git History**: Complete version control for all agent/workflow changes
- **Team Collaboration**: Multiple engineers can work on definitions through pull requests
- **Code Review**: Changes can be reviewed before deployment
- **Rollbacks**: Easy to revert changes using git
- **Bidirectional Sync**: Sync from repo to database (normal) or database to repo (recovery)

## 🏗️ Core Concepts

### Agents
An **Agent** is a specific AI persona with:
- A defined system prompt that establishes its behavior
- A set of available tools it can use
- A scope (SYSTEM or COMMON_BACKGROUND)

### Agentic Workflows
An **Agentic Workflow** is a state machine that:
- Defines how multiple agents work together
- Specifies the flow of control between agents
- Handles routing logic and decision points

### Scopes
- **System**: Agents and workflows available globally across the entire system
- **Common Background**: Agents and workflows specific to common background contexts

## 📁 Repository Structure

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
└── README.md            # This file
```

## 🛠️ Key Scripts

### Unified CLI Interface
- **`python -m src.cli`** - Main command-line interface for all operations
- **`python -m src.database_reset`** - Reset database and clear all data

### Agent Management
- **`python -m src.cli agent create`** - Create new agents with dual scope support
- **`python -m src.cli agent sync-all`** - Sync all agents to database
- **`python -m src.cli agent list`** - List all agents with scope filtering

### Workflow Management
- **`python -m src.cli workflow create`** - Create new workflows with dual scope support
- **`python -m src.cli workflow sync-all`** - Sync all workflows to database
- **`python -m src.cli workflow list`** - List all workflows with scope filtering

### Global Operations
- **`python -m src.cli sync-all`** - Sync all agents and workflows at once

For detailed usage instructions, see the [Scripts Reference](docs/development_guide.md#scripts-reference).

## 🚀 Getting Started

### For New Developers

1. **Read the [Development Guide](docs/development_guide.md)** - Complete walkthrough of how to work with this system
2. **Explore existing definitions** - Look at the agents and workflows in `definitions/` to understand patterns
3. **Create your first agent** - Follow the step-by-step guide in the development documentation
1.  **Build a simple workflow** by creating a `workflow.json` and manually providing all necessary UUIDs.

**⚠️ Important**: Always create agents before workflows. Workflows reference agents and will fail validation if referenced agents don't exist.

### For Experienced Developers

1. **Review the [Technical Reference](docs/agentic_workflow_system.md)** - Database schema and system architecture
2. **Check the scripts** - See `src/` for available automation tools
3. **Examine the schema** - Look at `schema.ts` for TypeScript definitions

## 🔧 Development

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Required Python packages (see `requirements.txt`)

### Environment Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure database connection in `local.env`
3. Run database setup: `python src/database_reset_sync.py`

### Common Tasks

**Create a new agent:**
```bash
python -m src.cli agent create --name "My Agent" --scope SYSTEM --description "A helpful agent"
```

**Sync all definitions to database:**
```bash
python -m src.cli sync-all
```

**List all system agents:**
```bash
python -m src.cli agent list --scope SYSTEM
```

**Create a new workflow:**
```bash
python -m src.cli workflow create --id "my-workflow" --name "My Workflow" --scope SYSTEM
```

**Reset database:**
```bash
python -m src.database_reset
```

## 📚 Documentation

- **[Development Guide](docs/development_guide.md)** - Complete guide for working with agents and workflows
- **[Technical Reference](docs/agentic_workflow_system.md)** - Database schema, system architecture, and technical details
- **Scripts** - See `src/` directory for all available automation tools

## 🤝 Contributing

1. **Follow the patterns** - Look at existing agents and workflows for examples
2. **Use appropriate scopes** - SYSTEM for global agents, COMMON_BACKGROUND for specific contexts
3. **Test your changes** - Sync to database and verify functionality
4. **Document updates** - Update relevant documentation when adding new features

## 📄 License

[Your License Here]
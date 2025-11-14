# Agentic Workflow System: A Technical Guide

This document provides a comprehensive technical overview of the Agentic Workflow System. It is intended for developers who need to define, create, and manage agents and the workflows that orchestrate them.

## 1. Core Concepts

The system is built on three fundamental concepts:

-   **`Agent`**: The core, reusable building block. An Agent is a specific AI persona with a defined system prompt and a set of available tools. It's the "who" that performs a task.

-   **`AgentWorkflow`**: The blueprint for an agentic process. A Workflow is a state machine graph that defines which agents are involved, how they are connected, and how control flows between them. It's the "how" a task is accomplished.

-   **`AgentWorkflowRun`**: A log of a single execution of an `AgentWorkflow`. It captures the inputs, outputs, status, and metadata of a specific run. It's the record of "what happened."

## 2. Database Schema

To define these concepts, the system uses a set of interconnected database tables. Your population scripts will need to insert data into these tables to create new agents and workflows.

---

### **Table: `agents`**
This table stores the definition for every individual agent.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` (PK) | A unique identifier for the agent. |
| `name` | `varchar` | A human-readable name (e.g., "Research Specialist"). |
| `system_prompt`| `text` | The full system prompt that defines the agent's persona and instructions. |
| `scope` | `enum` | The agent's scope: `SYSTEM` (globally available) or `WORKSPACE` (specific to a workspace). |

*Note: Tool associations for agents are managed in a separate linking table, e.g., `agent_tools`.*

---

### **Table: `agent_workflows`**
This table defines the high-level properties of a workflow blueprint, including its entrypoint.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `varchar` (PK) | A unique, human-readable ID for the workflow (e.g., `'chat-supervisor-v1'`). |
| `name` | `varchar` | A user-friendly name (e.g., "Real-time Supervisor/Worker Chat"). |
| `description` | `text` | Explains what this workflow does. |
| `entrypoint_node_id` | `uuid` (FK) | **Crucial:** Points to the single node in `agent_workflow_nodes` that starts every run. |

---

### **Table: `agent_workflow_nodes`**
This table defines every node (or "stop") within a workflow graph. It's a join table that links agents to workflows.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` (PK) | A unique ID for this specific node instance. |
| `workflow_id` | `varchar` (FK) | Links to `agent_workflows`. |
| `agent_id` | `uuid` (FK, nullable) | Links to the `agents` table. This is null if the node is not an agent (e.g., a tool executor). |
| `node_type` | `enum` | The type of the node: `AGENT` or `TOOL_EXECUTOR`. |
| `node_name` | `varchar` | A unique name for the node within the graph (e.g., `'supervisor'`, `'content_writer'`). |

---

### **Table: `agent_workflow_edges`**
This table defines the connections (or "arrows") between nodes, including the routing logic.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` (PK) | A unique ID for the edge. |
| `workflow_id` | `varchar` (FK) | Links to `agent_workflows`. |
| `source_node_id` | `uuid` (FK) | The `agent_workflow_nodes.id` where the edge originates. |
| `target_node_id` | `uuid` (FK, nullable) | The `agent_workflow_nodes.id` where the edge terminates. Can be null for an edge to `END`. |
| `condition_type` | `enum` | **The core of the routing logic.** See values below. |
| `condition_value`| `varchar` (nullable) | The value to check for conditional routing. |

**`condition_type` Enum Values:**
-   `ALWAYS`: A direct, unconditional link from source to target.
-   `CONDITIONAL`: A routed link. The meaning of `condition_value` depends on the `node_type` of the edge's source node:
    -   If the source is an `AGENT` node, the `condition_value` is matched against the `next` value set in the graph's state (e.g., the worker name chosen by a supervisor).
    -   If the source is a `TOOL_EXECUTOR` node, the `condition_value` is matched against the `name` of the tool that was just executed.
-   `ON_COMPLETE`: A special edge that connects a node to the graph's `END` state. `target_node_id` will be null.

## 3. JSON Examples for Population Scripts

Use these JSON structures as a guide for your data. Your Python script should generate and insert data that conforms to these examples.

---

### **Example 1: A Simple, Single-Agent Workflow**
Let's define a workflow called `'summarizer-v1'` that uses a single agent to summarize text.

**1. `agents` data:**
```json
[
  {
    "id": "a1b2c3d4-0001-4000-8000-000000000001",
    "name": "Text Summarizer",
    "system_prompt": "You are an expert at summarizing text. You will be given a piece of content and you must return a concise, accurate summary.",
    "scope": "SYSTEM"
  }
]
```

**2. `agent_workflows` data:**
```json
[
  {
    "id": "summarizer-v1",
    "name": "Simple Text Summarizer",
    "description": "A single-agent workflow that takes text and returns a summary.",
    "entrypoint_node_id": "n1b2c3d4-0001-4000-8000-000000000001"
  }
]
```

**3. `agent_workflow_nodes` data:**
```json
[
  {
    "id": "n1b2c3d4-0001-4000-8000-000000000001",
    "workflow_id": "summarizer-v1",
    "agent_id": "a1b2c3d4-0001-4000-8000-000000000001",
    "node_type": "AGENT",
    "node_name": "summarizer"
  }
]
```

**4. `agent_workflow_edges` data:**
*(This simple workflow has no complex edges. The `AgentGraphFactoryService` will implicitly wire the single node to `END`.)*

---

### **Example 2: The Complex Chat Supervisor/Worker Workflow**
This defines the `'chat-supervisor-v1'` workflow.

**1. `agents` data:** (Assume agents for `supervisor`, `researcher`, and `writer` are already defined)
```json
[
  { "id": "agent-uuid-supervisor", "name": "Supervisor", ... },
  { "id": "agent-uuid-researcher", "name": "Researcher", ... },
  { "id": "agent-uuid-writer", "name": "Writer", ... }
]
```

**2. `agent_workflows` data:**
```json
[
  {
    "id": "chat-supervisor-v1",
    "name": "Real-time Supervisor/Worker Chat",
    "description": "A multi-agent workflow for handling real-time chat with dynamic routing.",
    "entrypoint_node_id": "node-uuid-supervisor"
  }
]
```

**3. `agent_workflow_nodes` data:**
```json
[
  {
    "id": "node-uuid-supervisor",
    "workflow_id": "chat-supervisor-v1",
    "agent_id": "agent-uuid-supervisor",
    "node_type": "AGENT",
    "node_name": "supervisor"
  },
  {
    "id": "node-uuid-researcher",
    "workflow_id": "chat-supervisor-v1",
    "agent_id": "agent-uuid-researcher",
    "node_type": "AGENT",
    "node_name": "researcher"
  },
  {
    "id": "node-uuid-writer",
    "workflow_id": "chat-supervisor-v1",
    "agent_id": "agent-uuid-writer",
    "node_type": "AGENT",
    "node_name": "writer"
  },
  {
    "id": "node-uuid-tools",
    "workflow_id": "chat-supervisor-v1",
    "agent_id": null,
    "node_type": "TOOL_EXECUTOR",
    "node_name": "tool_executor"
  }
]
```

**4. `agent_workflow_edges` data:**
```json
[
  // 1. Conditional routing from the supervisor to workers or the tool executor
  {
    "id": "edge-uuid-1",
    "workflow_id": "chat-supervisor-v1",
    "source_node_id": "node-uuid-supervisor",
    "target_node_id": "node-uuid-researcher",
    "condition_type": "CONDITIONAL",
    "condition_value": "researcher"
  },
  {
    "id": "edge-uuid-2",
    "workflow_id": "chat-supervisor-v1",
    "source_node_id": "node-uuid-supervisor",
    "target_node_id": "node-uuid-writer",
    "condition_type": "CONDITIONAL",
    "condition_value": "writer"
  },
  {
    "id": "edge-uuid-3",
    "workflow_id": "chat-supervisor-v1",
    "source_node_id": "node-uuid-supervisor",
    "target_node_id": "node-uuid-tools",
    "condition_type": "CONDITIONAL",
    "condition_value": "tool_executor"
  },
  // 2. After workers run, they ALWAYS return control to the supervisor
  {
    "id": "edge-uuid-4",
    "workflow_id": "chat-supervisor-v1",
    "source_node_id": "node-uuid-researcher",
    "target_node_id": "node-uuid-supervisor",
    "condition_type": "ALWAYS"
  },
  {
    "id": "edge-uuid-5",
    "workflow_id": "chat-supervisor-v1",
    "source_node_id": "node-uuid-writer",
    "target_node_id": "node-uuid-supervisor",
    "condition_type": "ALWAYS"
  },
  // 3. After the tool executor runs, routing can be conditional on the tool name
  {
    "id": "edge-uuid-6",
    "workflow_id": "chat-supervisor-v1",
    "source_node_id": "node-uuid-tools",
    "target_node_id": "node-uuid-researcher", // Route to the researcher to interpret the results
    "condition_type": "CONDITIONAL",
    "condition_value": "external_research" // This is the name of the tool
  },
  // 4. A fallback edge for the tool executor to return control to the supervisor for any other tool
  {
    "id": "edge-uuid-7",
    "workflow_id": "chat-supervisor-v1",
    "source_node_id": "node-uuid-tools",
    "target_node_id": "node-uuid-supervisor",
    "condition_type": "ALWAYS"
  }
]
```

## 4. How to Define a New Workflow
Follow these steps to create a new workflow:

1.  **Define Agents:** Ensure all required agents exist in the `agents` table.
2.  **Create Workflow Record:** Add a new row to `agent_workflows`.
3.  **Define Nodes:** For each agent in the workflow, add a row to `agent_workflow_nodes`, linking it to your new workflow ID. Remember to add a `TOOL_EXECUTOR` node if any agent uses server-side tools.
4.  **Define Edges:** Add rows to `agent_workflow_edges` to define the flow of control between the nodes. **Crucially, if an agent's node is expected to use tools, you must add a conditional edge from that agent's node to the `TOOL_EXECUTOR` node.**
5.  **Set Entrypoint:** Set the `entrypoint_node_id` in your `agent_workflows` record to the ID of the starting node from `agent_workflow_nodes`.

The `AgentGraphFactoryService` in the backend is designed to read this data and dynamically construct the corresponding `LangGraph` application, which is then executed by the `AgentGraphRunnerService`. This data-driven approach ensures that new and complex agentic processes can be defined and deployed without any changes to the core application code. 
# Agentic Workflow Architecture

This document outlines the architecture for defining, creating, and running agentic workflows within the system. It is the result of an analysis of the previous hardcoded agent graph system and a design process aimed at creating a more flexible, robust, and future-proof model.

## 1. The Workflow Definition JSON

The core of the system is a declarative JSON structure used to define an agentic workflow. This JSON serves as a universal format that can be used by any program to create, update, or delete workflows in the database.

The structure is a literal 1-to-1 mapping of the database entities. It assumes that entities like Agents (and their UUIDs) are known before the workflow is defined. The service that consumes this JSON can then perform a direct "upsert" or "delete-and-recreate" operation based on the provided UUIDs.

### Example: `2nChat` Workflow

This example is a complete and literal definition of the original hardcoded chat workflow.

```json
{
  "id": "2nChat",
  "name": "2nChat",
  "description": "The original agentic chat workflow with a supervisor/router and multiple workers.",
  "isConversational": true,
  "entrypointNodeId": "node-uuid-1", 
  "nodes": [
    {
      "id": "node-uuid-1",
      "workflowId": "2nChat",
      "nodeType": "AGENT",
      "nodeName": "Router",
      "agentId": "agent-uuid-router"
    },
    {
      "id": "node-uuid-2",
      "workflowId": "2nChat",
      "nodeType": "AGENT",
      "nodeName": "RC2",
      "agentId": "agent-uuid-rc2"
    },
    {
      "id": "node-uuid-3",
      "workflowId": "2nChat",
      "nodeType": "AGENT",
      "nodeName": "DM2",
      "agentId": "agent-uuid-dm2"
    },
    {
      "id": "node-uuid-4",
      "workflowId": "2nChat",
      "nodeType": "AGENT",
      "nodeName": "2N",
      "agentId": "agent-uuid-2n"
    },
    {
      "id": "node-uuid-5",
      "workflowId": "2nChat",
      "nodeType": "TOOL_EXECUTOR",
      "nodeName": "tool_executor",
      "agentId": null
    }
  ],
  "edges": [
    { "id": "edge-uuid-1", "workflowId": "2nChat", "sourceNodeId": "node-uuid-1", "targetNodeId": "node-uuid-2", "conditionType": "CONDITIONAL", "conditionValue": "RC2" },
    { "id": "edge-uuid-2", "workflowId": "2nChat", "sourceNodeId": "node-uuid-1", "targetNodeId": "node-uuid-3", "conditionType": "CONDITIONAL", "conditionValue": "DM2" },
    { "id": "edge-uuid-3", "workflowId": "2nChat", "sourceNodeId": "node-uuid-1", "targetNodeId": "node-uuid-4", "conditionType": "CONDITIONAL", "conditionValue": "2N" },
    { "id": "edge-uuid-4", "workflowId": "2nChat", "sourceNodeId": "node-uuid-1", "targetNodeId": "node-uuid-5", "conditionType": "CONDITIONAL", "conditionValue": "tool_executor" },
    { "id": "edge-uuid-5", "workflowId": "2nChat", "sourceNodeId": "node-uuid-1", "targetNodeId": null, "conditionType": "CONDITIONAL", "conditionValue": "END" },
    
    { "id": "edge-uuid-6", "workflowId": "2nChat", "sourceNodeId": "node-uuid-2", "targetNodeId": "node-uuid-1", "conditionType": "CONDITIONAL", "conditionValue": "Router" },
    { "id": "edge-uuid-7", "workflowId": "2nChat", "sourceNodeId": "node-uuid-2", "targetNodeId": "node-uuid-5", "conditionType": "CONDITIONAL", "conditionValue": "tool_executor" },
    { "id": "edge-uuid-8", "workflowId": "2nChat", "sourceNodeId": "node-uuid-2", "targetNodeId": null, "conditionType": "CONDITIONAL", "conditionValue": "END" },
    
    { "id": "edge-uuid-9", "workflowId": "2nChat", "sourceNodeId": "node-uuid-3", "targetNodeId": "node-uuid-1", "conditionType": "CONDITIONAL", "conditionValue": "Router" },
    { "id": "edge-uuid-10", "workflowId": "2nChat", "sourceNodeId": "node-uuid-3", "targetNodeId": "node-uuid-5", "conditionType": "CONDITIONAL", "conditionValue": "tool_executor" },
    { "id": "edge-uuid-11", "workflowId": "2nChat", "sourceNodeId": "node-uuid-3", "targetNodeId": null, "conditionType": "CONDITIONAL", "conditionValue": "END" },

    { "id": "edge-uuid-12", "workflowId": "2nChat", "sourceNodeId": "node-uuid-4", "targetNodeId": "node-uuid-1", "conditionType": "CONDITIONAL", "conditionValue": "Router" },
    { "id": "edge-uuid-13", "workflowId": "2nChat", "sourceNodeId": "node-uuid-4", "targetNodeId": "node-uuid-5", "conditionType": "CONDITIONAL", "conditionValue": "tool_executor" },
    { "id": "edge-uuid-14", "workflowId": "2nChat", "sourceNodeId": "node-uuid-4", "targetNodeId": null, "conditionType": "CONDITIONAL", "conditionValue": "END" },

    { "id": "edge-uuid-15", "workflowId": "2nChat", "sourceNodeId": "node-uuid-1", "targetNodeId": "node-uuid-6", "conditionType": "CONDITIONAL", "conditionValue": "externalSearchCaller" },

    { "id": "edge-uuid-16", "workflowId": "2nChat", "sourceNodeId": "node-uuid-6", "targetNodeId": "node-uuid-5", "conditionType": "CONDITIONAL", "conditionValue": "tool_executor" },

    { "id": "edge-uuid-17", "workflowId": "2nChat", "sourceNodeId": "node-uuid-5", "targetNodeId": "node-uuid-6", "conditionType": "CONDITIONAL", "conditionValue": "external_research" },
    
    { "id": "edge-uuid-18", "workflowId": "2nChat", "sourceNodeId": "node-uuid-5", "targetNodeId": "node-uuid-1", "conditionType": "ALWAYS", "conditionValue": null }
  ]
}
```

### Key Principles of the JSON Structure
- **Literal Mapping**: All fields in the JSON objects for the workflow, nodes, and edges correspond directly to the column names in their respective database tables.
- **Developer-Managed UUIDs**: The definition assumes that the UUIDs for agents, and even for the workflow nodes and edges themselves, are generated by the developer beforehand. This allows for a deterministic definition and makes the repository the source of truth.
- **`conditionValue` Convention**: For an edge with `conditionType: 'CONDITIONAL'`, the `conditionValue` is a string that the system checks to determine the route. The meaning of this value depends on the `nodeType` of the edge's source node:
    - If the source node is an `AGENT`, the `conditionValue` is matched against the `state.next` property, which typically corresponds to the `nodeName` of the target node. This allows an agent to decide which agent to route to next.
    - If the source node is a `TOOL_EXECUTOR`, the `conditionValue` is matched against the `name` of the tool that was just executed (e.g., `"external_research"`). This allows for specific routing based on which tool was used.

## 2. Core Architectural Principles

### 2.1. Flexible Routing via Declarative Edges

The system has moved away from a hardcoded "supervisor/worker" model with a specialized `route` tool. Instead, it uses a flexible graph structure defined by nodes and edges.

- **How it Works:** The `AgentGraphFactoryService` reads the `nodes` and `edges` from the database. It uses `langgraph`'s native `addConditionalEdges` functionality to construct the graph. Routing is determined by a shared `state.next` property, which any agent node can set in its output.
- **Benefit:** This allows for any type of graph structure (linear pipelines, trees, complex multi-agent meshes), not just the old star-shaped supervisor model. This makes the system truly future-proof.

### 2.2. Graph Termination: `END` Edges and the `isConversational` Flag

A robust workflow needs a reliable way to stop. This is achieved through a two-part mechanism that combines a low-level engine instruction with a high-level agent policy.

- **The `END` Edge (The "Off Switch"):** An edge with a `conditionValue` of `"END"` and a `targetNodeId` of `null` is the fundamental `langgraph` instruction to terminate the workflow. When an agent sets `state.next = 'END'`, the graph execution will halt.

- **The `isConversational` Flag (The Policy):** This flag enables the *interface* that allows an agent to use the "off switch" reliably. When a workflow is marked as `isConversational: true`, the `AgentGraphFactoryService` injects a special `end` tool and a corresponding system prompt instruction into every agent in that workflow. This gives the agent a structured function to call when it determines the conversation is over, which our code then uses to set `state.next = 'END'`.

These two parts work together: the flag provides the agent with the "how-to" knowledge, and the `END` edge provides the underlying "ability" to terminate the graph.

### 2.4. The `tool_executor` Node

For any workflow that involves agents using server-side tools, the graph must contain a special node of type `TOOL_EXECUTOR`. This node must be explicitly defined in the workflow's `nodes` array.

- **Purpose:** This node is the generic engine that `langgraph` uses to run any server-side tool an agent requests. When an agent decides to use a tool, the graph must have an edge that routes it to this node.

- **Explicit Definition:** The `tool_executor` node and all edges leading to and from it **must be explicitly defined** in the JSON. The system will **not** create these automatically. This ensures the JSON remains a complete and unambiguous representation of the graph's entire topology.

- **Routing After Tool Execution:** After the `tool_executor` finishes, the system uses a three-tiered logic to determine the next node:
    1.  **Per-Tool Conditional Edge:** The system first looks for a `CONDITIONAL` edge whose `sourceNodeId` is the `tool_executor` and whose `conditionValue` exactly matches the `name` of the tool that was just executed (e.g., `"external_research"`). This allows for powerful, specialized flows where the output of a specific tool is always sent to a specific interpreter agent.
    2.  **Explicit Fallback Edge:** If no matching per-tool edge is found, the system looks for a single `ALWAYS` edge originating from the `tool_executor`. This serves as a predictable, catch-all route for any tool that doesn't have a specific conditional path defined. A common pattern is to have this edge route back to the main supervisor/router agent.
    3.  **Hardcoded Default (Return to Caller):** If neither a specific conditional nor a general always edge is defined, the system invokes a hardcoded default behavior as a final safety net: it routes control directly back to the agent node that originally called the tool. This enables a simple "call-and-return" pattern without requiring any edge definitions from the `tool_executor`.

### 2.5. System Prompts as the "Brains"

While the JSON defines the *structure* (the roads), the agents' **system prompts** provide the *intelligence* to navigate that structure (the driving directions).

The system prompts are responsible for:
- **Guiding Routing:** Instructing an agent on how to choose the next agent (e.g., "If the user asks about X, set the `next` state to 'AgentX'").
- **Defining Tool Usage:** Detailing when and how to use its available tools.
- **Preventing Cycles:** Providing behavioral rules to avoid oscillations (e.g., "Do not delegate the same task to the same agent twice without new information.").

## 3. Programmatic Fallbacks (Defense-in-Depth)

Relying on non-deterministic LLMs and prompts alone is insufficient to guarantee stability. The system must include deterministic guardrails. These are implemented at runtime by the services that execute the graphs.

1.  **Step Limit (Circuit Breaker):** This is the most critical fallback. The graph execution is automatically interrupted if it exceeds a predefined number of steps (e.g., 15). This is implemented using the `interruptAfter` configuration in `langgraph`'s `compile()` method. This provides a hard guarantee against infinite loops.

2.  **Timeout:** To prevent a single node or LLM call from hanging indefinitely, the entire graph invocation is wrapped in a timeout (e.g., 90 seconds). This is implemented in the calling service (like `AgentChatService`) using `Promise.race`.

3.  **Human in the Loop:** As a final fallback, the system can be designed to route to a `human_handoff` node if it detects a cycle or times out, allowing for manual intervention.

By combining a flexible, declarative workflow definition with these robust architectural patterns and fallbacks, the system is designed to be powerful, modular, and stable.

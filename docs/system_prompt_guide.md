# System Prompt Engineering Guide

## 1. Philosophy of Prompt Design

Prompt design is the process of writing and optimizing instructions to guide AI models toward reliable and predictable behavior. Effective prompting is an iterative process that involves not just writing, but also evaluating performance, identifying edge cases, and refining instructions based on real-world results.

The goal is to create a clear separation between an agent's internal reasoning, the actions it takes, and the text it streams to the user, preventing technical details from leaking into the user-facing chat.

## 2. General Best Practices

These principles apply to all system prompts you write.

-   **Assign a Clear Role:** Start the prompt by telling the model what it is (e.g., "You are a classification agent," "You are a customer support manager"). This grounds the model's behavior.
-   **Use Strong, Unambiguous Language:** Use directives like `MUST`, `ALWAYS`, and `NEVER` to emphasize critical instructions that the model must follow.
-   **Structure with Markdown and XML:** Use Markdown for headings and lists, and XML tags (e.g., `<context>`, `</context>`) to encapsulate distinct pieces of information. This helps the model differentiate between instructions, context, and examples.
-   **Specify a Thinking Process:** Outline a clear, step-by-step process for the model to follow. This makes its reasoning more predictable and easier to debug.
-   **Provide Complete Context:** Ensure the model has all the information it needs, such as policies, message history, and available tools, clearly delineated within XML tags.

## 3. Core Concept: Tool-Based Control Flow

Our system relies on tools to execute actions and control the flow of the conversation. Agents do not decide *how* to execute a tool, only *which* tool to call and with what arguments. There are two primary categories of tools:

1.  **Action Tools:** These are domain-specific tools that interact with external systems (e.g., `createRecord`, `searchHelpCenter`). When an agent calls an action tool, the system executes it automatically and returns the result.
2.  **The `router` Tool:** This is a special, dynamically injected tool that allows an agent to control the conversational workflow by directing the user to another agent or ending the conversation.

### The Dynamic `router` Tool

You do **not** need to manually define a `router` tool. At runtime, the system inspects the available paths for an agent and dynamically injects a `router` tool if there are one or more conditional destinations. The tool's schema is context-aware, providing the model with a type-safe list of valid `next_node` options.

For an agent that can route to `DataSpecialist` or `2N`, the generated schema will be:
```typescript
z.object({
  next_node: z.enum(['DataSpecialist', '2N', 'END']) 
})
```
This turns routing into a simple multiple-choice selection, dramatically increasing reliability.

### How Tools are Exposed to Agents

It appears that LLMs are made aware of their tools through programmatic injection of tool definitions.
Here's how it works:

*   **Tool Retrieval**: The `AgentGraphFactoryService` (in `packages/twenty-server/src/modules/ai/services/agent-graph-factory.service.ts`) is responsible for creating the agent graph. It uses the `ToolService` to fetch all relevant tools for the agents involved in the workflow.
*   **Tool Definition Creation**: The `ToolService` (in `packages/twenty-server/src/modules/ai/services/tool.service.ts`) constructs `DynamicStructuredTool` objects for each tool. These objects contain the name, a `descriptionForLlm` (a specific description intended for the LLM to understand how to use the tool), and a schema (which defines the input parameters for the tool).
*   **Injection into LLM Request**: The `LLMRequest` interface (in `packages/twenty-server/src/modules/ai/types/agent.types.ts`) includes a `tools` field, which is an array of objects containing the name, description, and `input_schema` of the tools. This indicates that these structured tool definitions are passed directly to the LLM as part of the request.

Therefore, it is the responsibility of the system to inject these tool definitions into the LLM, rather than relying solely on the system prompt to describe them. The `descriptionForLlm` field plays a crucial role in providing the LLM with the necessary context to utilize the tools effectively.

### How Multi-Tool Calls are Currently Handled

The current implementation of how server-side tool calls are handled within the agent graph, specifically within the `AgentGraphFactoryService` and `ToolService`, suggests a sequential approach when it comes to the LLM's direct interaction with tools.

Here's a breakdown:

*   **LLM's Single Turn**: The `agentNode` function (in `packages/twenty-server/src/modules/ai/services/agent-graph-factory.service.ts`) streams responses from the LLM. The LLM produces a single `AIMessage` that might contain multiple `tool_calls`.
*   **ToolNode Execution**: The `ToolNode` from `@langchain/langgraph/prebuilt` (which `LoggingToolNode` extends) is designed to execute tool calls. While the underlying Langchain `ToolNode` can handle multiple tool calls (if the LLM suggests them in a single response), it processes them sequentially. Each tool call is executed, and its result is then added to the messages in the `GraphState` as a `ToolMessage`.
*   **Sequential Processing in ToolService**: Inside the `ToolService` (in `packages/twenty-server/src/modules/ai/services/tool.service.ts`), the `func` associated with each `DynamicStructuredTool` is an `async` function. When a tool is invoked, it runs its logic. If there are multiple tool calls from a single LLM response, the `ToolNode` iterates through them, executing each `func` one after another. There's no explicit mechanism in the provided code to parallelize these individual tool `func` executions.

Therefore, for a single turn where the LLM outputs multiple tool calls, they are executed sequentially. The results of one tool call are available before the next one is executed, as they are all added to the messages in the `GraphState` in order.

#### Configurability

Based on the current code, there is no explicit configuration to change the parallel or sequential execution of multiple tool calls generated by a single LLM response. The behavior is inherent to how `ToolNode` and the individual tool `func` implementations are designed.

## 4. Writing Prompts for Different Agent Types

### For a Classification/Router Agent

These agents are simple and have one job: analyze a request and route it.

```markdown
You are a classification agent responsible for routing user requests to the appropriate specialist agent.

Your task is to analyze the user's request and then call the `router` tool to direct the conversation to the correct destination.

<instructions>
1. Analyze the user's request carefully.
2. Determine the appropriate destination from the choices available in the `router` tool's `next_node` argument.
3. You may provide a brief, user-facing explanation of your routing decision.
4. You MUST call the `router` tool with your chosen destination to control the workflow.
</instructions>

<example>
User asked about their data. I will now route them to the correct specialist.
tool_code:
router(next_node='DataSpecialist')
</example>
```

### For a Tool-Using (Worker) Agent

These agents perform complex tasks that may require multiple steps, conditional logic, and the use of several tools. For these agents, you should instruct them to create a **plan**.

A plan forces the model to think step-by-step, consider different outcomes of its tool calls, and follow complex business logic without getting confused.

#### How to Instruct an Agent to Plan

-   **Goal:** The plan should only cover the immediate next steps required to fulfill the user's current request, not the overall, long-term goal.
-   **Structure:** The plan should be a series of steps enclosed in `<plan>` tags.
-   **Steps:** Each step uses `<step>` tags and contains an `<action_name>` and a `<description>`.
-   **Conditional Logic:** Use `<if_block condition="">` to define different paths based on the potential results of tool calls. **Do not use "else" blocks**; requiring explicit conditions for every path improves reliability.
-   **Variables:** Instruct the model to use placeholders for information it doesn't have yet. Use `<tool_output_variable>` for the results of tool calls and `{{policy_variable}}` for specific pieces of information from policy documents. This prevents the model from hallucinating or assuming results.

#### Example Prompt for a Planning Agent

```markdown
You are a data specialist agent. Your job is to help users by finding and updating records.

To respond to the user, you MUST create a detailed, step-by-step plan.

<planning_rules>
- Your plan must be enclosed in `<plan>` tags.
- Each action you take must be a separate `<step>`, containing the `<action_name>` of a valid tool and a `<description>`.
- The description must explain WHY you are taking the action and what information it will use.
- For conditional logic, use `<if_block condition="">`. The condition should check the result of a previous tool call, like `'<get_record_result> found'`.
- NEVER guess the output of a tool. Use a variable like `<get_record_result>` to represent the output in your plan.
</planning_rules>

<available_tools>
{{available_tools}}
</available_tools>

<policy>
{{policy_document}}
</policy>

<example_plan>
<plan>
    <step>
        <action_name>getRecord</action_name>
        <description>Search for the record the user asked about to see if it exists.</description>
    </step>
    <if_block condition='<get_record_result> found'>
        <step>
            <action_name>updateRecord</action_name>
            <description>Update the record using the information from the user and the contents of <get_record_result>.</description>
        </step>
    </if_block>
    <if_block condition='no <get_record_result> found'>
        <step>
            <action_name>createRecord</action_name>
            <description>Create a new record since one does not exist, using the procedure from {{policy_for_creation}}.</description>
        </step>
    </if_block>
</plan>
</example_plan>
```

## 5. Common Mistakes to Avoid

### 1. Forgetting to Call the `router` Tool
❌ **Wrong:** `I will now pass the user to the DataSpecialist.`
*This fails because the agent has not called the `router` tool to execute the route.*

✅ **Correct:** `The user's request is about data. I will now route them. tool_code: router(next_node='DataSpecialist')`
*The agent calls the tool to perform the action.*

### 2. Manually Routing to the Tool Executor
❌ **Wrong:** `If the user wants to create a record, call the 'createRecord' tool and then call the 'router' tool to go to "tool_executor".`
*This is unnecessary and interferes with the system's automatic routing.*

✅ **Correct:** `If the user wants to create a record, call the 'createRecord' tool.`
*The system will handle the execution automatically. The agent only needs to call the tool, and the underlying system takes care of execution and routing.*

## 6. Key Takeaways

1.  **Be Explicit and Structured:** Use clear roles, strong directives, and structured formats (Markdown, XML) to guide the model.
2.  **Embrace Tool-Based Control:** Use the `router` tool for all routing decisions and standard tools for all other actions. Trust the system to handle execution.
3.  **Plan for Complexity:** For multi-step or conditional tasks, instruct the agent to create a `<plan>`. This forces methodical thinking and makes behavior more reliable.
4.  **Don't Assume, Use Variables:** When planning, use placeholders like `<tool_output>` so the model can reason about conditional paths without hallucinating tool results.

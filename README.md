Simple MCP Server + LLM Agent

A small learning project that demonstrates how to build an MCP (Model Context Protocol) server from scratch using Python, connect to it with an MCP client, and let an LLM discover and call MCP tools.

The project uses:

Python 3.10+

uv for Python project/dependency management

MCP Python SDK 2.x

OpenRouter for the LLM

OpenAI Python SDK as an OpenRouter-compatible API client

STDIO transport between the MCP client and server

Architecture

User
  |
  v
LLM (OpenRouter)
  |
  | decides which MCP tool to call
  v
MCP Client
  |
  | STDIO / JSON-RPC
  v
MCP Server
  |
  | executes tool
  v
Tool Result
  |
  v
LLM
  |
  v
Final Answer

The important idea is that the LLM does not directly access the application's Python data. It receives MCP tool definitions, decides which tool to use, and the MCP client executes the selected tool on the server.

Project Structure

test_mcp/
├── server.py
├── client.py
├── llm_test.py
├── pyproject.toml
├── uv.lock
└── README.md

server.py

Contains the MCP server and exposes tools such as:

add

subtract

multiply

get_customer

get_customer_balance

find_customer

It also demonstrates MCP resources and prompts.

client.py

Connects to the MCP server over STDIO, discovers its tools, converts MCP tool definitions into an LLM-compatible format, sends them to the LLM, executes requested MCP tools, and feeds tool results back to the LLM.

llm_test.py

A small standalone test to verify that the OpenRouter API connection works before integrating the LLM with MCP.

Prerequisites

Install:

Python 3.10 or newer

uv

An OpenRouter API key

Check Python:

python3 --version

Check uv:

uv --version

Setup

Clone or create the project and enter the directory:

cd ~/test_mcp

If dependencies are not already installed:

uv sync

The project should contain the MCP SDK and OpenAI Python SDK.

If needed, they can be added with:

uv add "mcp[cli]"
uv add openai

Configure OpenRouter

Set your API key as an environment variable.

macOS/Linux:

export OPENROUTER_API_KEY="your-api-key"

Verify it exists:

echo $OPENROUTER_API_KEY

Do not commit the API key to Git.

For a persistent shell configuration, you can add the export to your shell profile, but be careful not to expose the key in source code or public repositories.

Run the MCP Server

The server can be started directly:

uv run server.py

The server uses STDIO, so it will normally appear to wait silently for requests. That is expected.

The server also contains:

if __name__ == "__main__":
    mcp.run()

which starts the MCP server using the default STDIO transport.

Inspect the MCP Server

The MCP CLI/Inspector can be used to inspect the server:

uv run mcp dev server.py

The Inspector allows you to see:

Available tools

Tool descriptions

Input schemas

Resources

Prompts

Tool execution results

This is useful for debugging the MCP server before involving an LLM.

Test the LLM Separately

Before connecting the LLM to MCP, test OpenRouter:

uv run python llm_test.py

The test sends a simple question to OpenRouter and prints the model response.

The project currently uses an OpenRouter free model. Free model availability and limits can change over time.

Run the MCP + LLM Client

Run:

uv run python client.py

The client performs the following steps.

1. Connect to the MCP server

server = StdioServerParameters(
    command="uv",
    args=["run", "server.py"],
)

The MCP client starts the server as a subprocess.

2. Discover tools

mcp_result = await client.list_tools()

The client asks the MCP server which tools it provides.

3. Convert MCP tools for the LLM

MCP tool definitions are converted into the OpenAI-compatible function/tool format:

{
    "type": "function",
    "function": {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.input_schema,
    },
}

This gives the LLM enough information to decide which tool it should use.

4. Send the user question and tools to the LLM

The client sends:

User question
+
Available MCP tools

For example:

What is John's balance?

5. LLM requests a tool

The LLM may decide:

find_customer(name="John")

The client parses the requested tool and arguments.

6. MCP client executes the tool

The client calls:

await client.call_tool(
    tool_name,
    arguments,
)

The MCP server executes the corresponding Python function.

For example:

find_customer("John")

returns:

{
  "id": 1,
  "name": "John",
  "balance": 5000,
  "status": "active"
}

7. Tool result is sent back to the LLM

The MCP result is added to the conversation as a tool message:

messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": result_text,
})

The LLM now knows what the tool returned.

8. Agent loop

The client repeats the LLM/tool process:

LLM
 |
 | tool call?
 +---- No ----> Final answer
 |
 Yes
 |
 v
MCP tool
 |
 v
Tool result
 |
 v
LLM again

The loop ends when the LLM returns a normal response without requesting another tool.

Example

Input:

What is John's balance?

Possible flow:

LLM requested tool:
Tool: find_customer
Arguments: {'name': 'John'}

MCP result:
{
  "id": 1,
  "name": "John",
  "balance": 5000,
  "status": "active"
}

Final LLM response:
John's balance is 5000.

MCP Concepts Demonstrated

Tools

Tools are executable functions exposed by the MCP server.

Example:

@mcp.tool()
def get_customer_balance(customer_id: int) -> int:
    ...

The LLM can decide when to call them.

Resources

Resources represent data that can be exposed through MCP resource URIs.

Example:

customer://1

Resources are conceptually different from tools: a tool represents an action/function, while a resource represents information/data.

Prompts

Prompts are reusable prompt templates exposed by the MCP server.

Example:

@mcp.prompt()
def analyze_customer(customer_id: int) -> str:
    ...

MCP Client

The client connects to the MCP server and provides operations such as:

await client.list_tools()

and:

await client.call_tool(...)

STDIO Transport

In this project, the client launches the MCP server locally and communicates with it over standard input/output.

client.py
    |
    | stdin/stdout
    |
server.py

This is convenient for local development and learning.

Why the LLM Does Not Know the Python Dictionary

The server contains customer data:

customers = {
    1: {"name": "John", "balance": 5000, "status": "active"},
    ...
}

The LLM does not directly see this Python variable.

Instead, it sees tool definitions such as:

find_customer(name)
get_customer_balance(customer_id)

The LLM asks the MCP client to execute a tool, and the tool result is returned to the LLM.

This separation is an important part of the architecture.

Learning Progression

This project was built incrementally:

Learn basic Python/MCP concepts

Create a basic MCP server

Add simple tools

Add customer-related tools

Add MCP resources

Add MCP prompts

Inspect the server using MCP Inspector

Build an MCP client

Connect the client to an LLM

Convert MCP tools into LLM-compatible tool definitions

Let the LLM choose a tool

Execute the tool through MCP

Send the tool result back to the LLM

Implement the basic agent/tool-calling loop

Important Mental Model

Keep these four components separate:

MCP Server
    |
    | provides capabilities
    v
MCP Tools
    |
    | are executed by
    v
MCP Client
    |
    | orchestrated by decisions from
    v
LLM

More precisely:

LLM
  = decides what to do

MCP Client
  = connects to the MCP server and invokes tools

MCP Server
  = exposes tools/resources/prompts

Tool
  = performs the actual operation

The LLM provides the intelligence for deciding which capability to use, while MCP provides a standardized way to expose and invoke those capabilities.

Next Steps

Potential extensions to this project:

Add a proper maximum tool-call limit

Handle MCP tool errors

Validate LLM-generated tool arguments

Support multiple tool calls

Use structured MCP tool outputs

Separate the agent loop into reusable functions/classes

Add real backend/API calls instead of in-memory customer data

Explore MCP resources more deeply

Explore MCP prompts

Run the MCP server over Streamable HTTP instead of STDIO

Add authentication and authorization

Connect the MCP server to a real application

Build a small chat interface on top of the agent

Security Notes

This project is intentionally simple and is for learning.

For production:

Never hardcode API keys

Validate LLM-generated tool arguments

Restrict which tools the model can invoke

Validate authorization before executing sensitive operations

Handle tool failures and timeouts

Add logging/observability

Add limits to the number of tool calls

Avoid exposing sensitive data unnecessarily

Treat LLM-generated tool arguments as untrusted input

License

This project is intended as a learning/demo project.
import asyncio
import json
import os

from mcp import Client, StdioServerParameters
from openai import OpenAI

server = StdioServerParameters(
    command="uv",
    args=[
        "run",
        "server.py",
    ],
)


llm = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


def convert_mcp_tools_to_llm_tools(mcp_tools):
    """Convert MCP tool definitions into OpenAI-compatible tool definitions."""

    tools = []

    for tool in mcp_tools:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
        )

    return tools


async def main():

    # --------------------------------------------------
    # 1. Connect to MCP server
    # --------------------------------------------------

    async with Client(server) as client:

        print("Connected to MCP server")

        # --------------------------------------------------
        # 2. Discover MCP tools
        # --------------------------------------------------

        mcp_result = await client.list_tools()

        print("\nMCP tools:")

        for tool in mcp_result.tools:
            print(f"- {tool.name}")

        # --------------------------------------------------
        # 3. Convert MCP tools to LLM tool definitions
        # --------------------------------------------------

        llm_tools = convert_mcp_tools_to_llm_tools(mcp_result.tools)

        print("\nTools sent to LLM:")

        print(json.dumps(llm_tools, indent=2))

        # --------------------------------------------------
        # 4. User question
        # --------------------------------------------------

        user_message = "What is John's balance?"

        print(f"\nUser: {user_message}")

        # --------------------------------------------------
        # 5. Start conversation
        # --------------------------------------------------

        messages = [{"role": "user", "content": user_message}]

        # --------------------------------------------------
        # 6. LLM <-> MCP agent loop
        # --------------------------------------------------

        while True:

            response = llm.chat.completions.create(
                model="liquid/lfm-2.5-2.6b:free",
                messages=messages,
                tools=llm_tools,
            )

            assistant_message = response.choices[0].message

            # Add LLM response to conversation
            messages.append(assistant_message)

            # --------------------------------------------------
            # If LLM has no tool calls, we have the final answer
            # --------------------------------------------------

            if not assistant_message.tool_calls:

                print("\nFinal LLM response:")
                print(assistant_message.content)

                break

            # --------------------------------------------------
            # LLM requested one or more tools
            # --------------------------------------------------

            for tool_call in assistant_message.tool_calls:

                tool_name = tool_call.function.name

                arguments = json.loads(tool_call.function.arguments)

                print("\nLLM requested tool:")
                print("Tool:", tool_name)
                print("Arguments:", arguments)

                # --------------------------------------------------
                # Execute MCP tool
                # --------------------------------------------------

                tool_result = await client.call_tool(
                    tool_name,
                    arguments,
                )

                result_text = tool_result.content[0].text

                print("\nMCP result:")
                print(result_text)

                # --------------------------------------------------
                # Give MCP result back to LLM
                # --------------------------------------------------

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text,
                    }
                )


if __name__ == "__main__":
    asyncio.run(main())

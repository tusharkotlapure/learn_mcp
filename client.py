import asyncio
import json
import os

from mcp import Client, StdioServerParameters
from openai import OpenAI

MAX_ITERATIONS = 5

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


def convert_mcp_resources_to_llm_tool(mcp_resources):
    """Expose MCP resources to the LLM as a resource-reading function."""

    resource_descriptions = []

    for resource in mcp_resources:
        resource_descriptions.append(
            {
                "uri": str(resource.uri),
                "name": resource.name,
                "description": resource.description,
            }
        )

    return {
        "type": "function",
        "function": {
            "name": "read_mcp_resource",
            "description": (
                "Read an MCP resource. Use this when the user asks "
                "about information that may be contained in one of the "
                "available resources."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": (
                            "The URI of the resource to read. "
                            f"Available resources: {json.dumps(resource_descriptions)}"
                        ),
                    }
                },
                "required": ["uri"],
            },
        },
    }


def convert_mcp_prompts_to_llm_tool(mcp_prompts):
    """Expose MCP prompts to the LLM as a prompt-selection function."""

    prompt_descriptions = []

    for prompt in mcp_prompts:
        prompt_descriptions.append(
            {
                "name": prompt.name,
                "description": prompt.description,
            }
        )

    return {
        "type": "function",
        "function": {
            "name": "get_mcp_prompt",
            "description": (
                "Get a reusable MCP prompt. "
                "Use this when the user asks for an analysis or task "
                "that matches one of the available prompts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Name of the MCP prompt to use. "
                            f"Available prompts: "
                            f"{json.dumps(prompt_descriptions)}"
                        ),
                    },
                    "arguments": {
                        "type": "object",
                        "description": ("Arguments required by the selected prompt."),
                    },
                },
                "required": ["name", "arguments"],
            },
        },
    }


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
        # Discover MCP resources
        # --------------------------------------------------

        resource_result = await client.list_resources()

        print("\nMCP resources:")

        for resource in resource_result.resources:
            print(f"- {resource.uri}")

        llm_resources = convert_mcp_resources_to_llm_tool(resource_result.resources)

        print("\nResources sent to LLM:")
        print(json.dumps(llm_resources, indent=2))

        llm_tools.append(llm_resources)

        # --------------------------------------------------
        # Discover MCP prompts
        # --------------------------------------------------

        prompt_result = await client.list_prompts()

        print("\nMCP prompts:")

        for prompt in prompt_result.prompts:
            print(f"- {prompt.name}")

        llm_prompts = convert_mcp_prompts_to_llm_tool(prompt_result.prompts)

        print("\nPrompts sent to LLM:")
        print(json.dumps(llm_prompts, indent=2))

        llm_tools.append(llm_prompts)

        # --------------------------------------------------
        # 4. User question
        # --------------------------------------------------

        user_message = "I want analysis of train no: 12116 get info from this document https://wr.indianrailways.gov.in/ticker/1443706517885TT.pdf"

        print(f"\nUser: {user_message}")

        # --------------------------------------------------
        # 5. Start conversation
        # --------------------------------------------------

        messages = [{"role": "user", "content": user_message}]

        # --------------------------------------------------
        # 6. LLM <-> MCP agent loop
        # --------------------------------------------------

        for iteration_count in range(MAX_ITERATIONS):
            print(f"\nIteration {iteration_count + 1}/{MAX_ITERATIONS}")

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

                return  # Exit the main function if final response is reached

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

                if tool_name == "read_mcp_resource":

                    uri = arguments["uri"]

                    print("\nLLM requested resource:")
                    print("URI:", uri)

                    resource_result = await client.read_resource(uri)

                    result_text = resource_result.contents[0].text

                elif tool_name == "get_mcp_prompt":
                    prompt_name = arguments["name"]
                    prompt_arguments = arguments["arguments"]

                    print("\nLLM requested prompt:")
                    print("Name:", prompt_name)
                    print("Arguments:", prompt_arguments)

                    prompt_result = await client.get_prompt(
                        prompt_name,
                        arguments=prompt_arguments,
                    )

                    result_text = "\n".join(
                        message.content.text
                        for message in prompt_result.messages
                        if hasattr(message.content, "text")
                    )
                else:

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

    print("\nMaximum agent iterations reached.")


if __name__ == "__main__":
    asyncio.run(main())

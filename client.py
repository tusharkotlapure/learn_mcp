import asyncio
import os
import json

from mcp import Client, StdioServerParameters
from openai import OpenAI

from mcp_adapter import (
    convert_mcp_tools_to_llm_tools,
    convert_mcp_resources_to_llm_tool,
    convert_mcp_prompts_to_llm_tool,
)
from agent import MCPAgent

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


async def main():

    async with Client(server) as client:

        print("Connected to MCP server")

        # Discover capabilities
        mcp_tools = await client.list_tools()
        mcp_resources = await client.list_resources()
        mcp_prompts = await client.list_prompts()

        # Convert MCP → LLM
        llm_tools = convert_mcp_tools_to_llm_tools(mcp_tools.tools)

        llm_tools.append(convert_mcp_resources_to_llm_tool(mcp_resources.resources))

        llm_tools.append(convert_mcp_prompts_to_llm_tool(mcp_prompts.prompts))

        # User question
        user_message = """
            Read this PDF:
            https://www.w3.org/Press/99Folio.pdf

            Answer these questions strictly from the document:
            1. What is the document about?
            2. What are the main sections?
            3. Give me one specific fact mentioned in the document.
            """

        # Create agent
        agent = MCPAgent(
            llm=llm,
            client=client,
            llm_tools=llm_tools,
        )

        # Run agent
        final_response = await agent.run(user_message)

        print("\nFinal LLM response:")
        print(final_response)


if __name__ == "__main__":
    asyncio.run(main())

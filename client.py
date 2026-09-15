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
        user_message = (
            "I want analysis of train no: 12116 "
            "from this document "
            "https://wr.indianrailways.gov.in/"
            "ticker/1443706517885TT.pdf"
        )

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

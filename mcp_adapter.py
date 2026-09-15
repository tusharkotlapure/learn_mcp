import json

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

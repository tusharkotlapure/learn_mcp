import json

from constants import MAX_ITERATIONS


class MCPAgent:

    def __init__(
        self,
        llm,
        client,
        llm_tools,
    ):
        self.llm = llm
        self.client = client
        self.llm_tools = llm_tools

    async def run(self, user_message):

        messages = [
            {
                "role": "user",
                "content": user_message,
            }
        ]

        for iteration in range(MAX_ITERATIONS):

            print(
                f"\nIteration {iteration + 1}/{MAX_ITERATIONS}"
            )

            response = self.llm.chat.completions.create(
                model="liquid/lfm-2.5-2.6b:free",
                messages=messages,
                tools=self.llm_tools,
            )

            assistant_message = response.choices[0].message

            print("\nAssistant message:")
            print(assistant_message)

            messages.append(assistant_message)

            # No tool call = final answer
            if not assistant_message.tool_calls:

                print("\nFinal answer:")
                print(assistant_message.content)

                return assistant_message.content

            # Execute requested tools/resources/prompts
            for tool_call in assistant_message.tool_calls:

                await self.execute_tool_call(
                    tool_call,
                    messages,
                )

        return "Maximum agent iterations reached."

    async def execute_tool_call(
        self,
        tool_call,
        messages,
    ):

        tool_name = tool_call.function.name

        arguments = json.loads(
            tool_call.function.arguments
        )

        print("\nLLM requested:")
        print("Name:", tool_name)
        print("Arguments:", arguments)

        # -----------------------------------------
        # Resource
        # -----------------------------------------

        if tool_name == "read_mcp_resource":

            uri = arguments["uri"]

            print("\nReading MCP resource:")
            print(uri)

            result = await self.client.read_resource(uri)

            result_text = result.contents[0].text

        # -----------------------------------------
        # Prompt
        # -----------------------------------------

        elif tool_name == "get_mcp_prompt":

            prompt_name = arguments["name"]

            prompt_arguments = arguments.get(
                "arguments",
                {},
            )

            print("\nCalling MCP prompt:")
            print(prompt_name)

            result = await self.client.get_prompt(
                prompt_name,
                arguments=prompt_arguments,
            )

            result_text = "\n".join(
                message.content.text
                for message in result.messages
                if hasattr(message.content, "text")
            )

        # -----------------------------------------
        # Normal MCP tool
        # -----------------------------------------

        else:

            result = await self.client.call_tool(
                tool_name,
                arguments,
            )

            result_text = result.content[0].text

        print("\nMCP result:")
        print(result_text)

        # -----------------------------------------
        # Send result back to LLM
        # -----------------------------------------

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_text,
            }
        )
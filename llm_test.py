import os

from openai import OpenAI


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {
            "role": "user",
            "content": "Explain what an MCP server is in one sentence.",
        }
    ],
)

print("Model used:", response.model)
print("Response:", response.choices[0].message.content)
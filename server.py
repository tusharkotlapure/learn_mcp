from mcp.server.mcpserver import MCPServer
from httpx import AsyncClient
import io
import os
from pypdf import PdfReader
from docx import Document

mcp = MCPServer("Demo Server")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract one number from another."""
    return a - b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """multiply two numbers together."""
    return a * b


customers = {
    1: {
        "name": "John",
        "balance": 5000,
        "status": "active",
    },
    2: {
        "name": "Alice",
        "balance": 10000,
        "status": "active",
    },
    3: {
        "name": "Bob",
        "balance": 0,
        "status": "inactive",
    },
}


@mcp.tool()
def get_customer(customer_id: int) -> dict:
    """Get customer details using the customer ID."""

    customer = customers.get(customer_id)

    if customer is None:
        return {"error": "Customer not found"}

    return {
        "id": customer_id,
        **customer,
    }


@mcp.tool()
def get_customer_balance(customer_id: int) -> int:
    """Get the current balance of a customer."""

    customer = customers.get(customer_id)

    if customer is None:
        return 0

    return customer["balance"]


@mcp.tool()
def find_customer(name: str) -> dict:
    """Find a customer using their name."""

    for customer_id, customer in customers.items():
        if customer["name"].lower() == name.lower():
            return {
                "id": customer_id,
                **customer,
            }

    return {"error": "Customer not found"}


@mcp.resource("customer://{customer_id}")
def customer_resource(customer_id: int) -> str:
    """Customer information."""

    customer = customers.get(customer_id)

    if customer is None:
        return "Customer not found"

    return str(
        {
            "id": customer_id,
            **customer,
        }
    )

@mcp.resource("documents://python-notes")
async def python_notes() -> str:
    """Python programming notes."""

    path = "/Users/t.kotlapure/Downloads/PYTHON PROGRAMMING NOTES.pdf"

    return extract_text_from_file(path)

@mcp.resource("documents://ai-ml-notes")
async def ai_ml_notes() -> str:
    """AI and ML digital notes."""

    path = "https://mrcet.com/downloads/digital_notes/ECE/III%20Year/AI%20&%20ML%20DIGITAL%20NOTES.pdf"

    return extract_text_from_file(path)

@mcp.prompt()
def analyze_customer(customer_id: int) -> str:
    """Analyze a customer's account."""

    return f"""
Analyze customer {customer_id}.

Please provide:
1. Customer status
2. Current balance
3. Any potential concerns
4. A short recommendation
"""


@mcp.tool()
async def get_github_repository(
    owner: str,
    repo: str,
) -> dict:
    """Get information about a GitHub repository."""

    url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    async with AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
        )

    if response.status_code == 404:
        return {
            "error": "Repository not found",
            "owner": owner,
            "repo": repo,
        }

    if response.status_code != 200:
        return {
            "error": "GitHub API request failed",
            "status_code": response.status_code,
            "message": response.text,
        }

    data = response.json()

    return {
        "name": data["name"],
        "full_name": data["full_name"],
        "description": data["description"],
        "private": data["private"],
        "default_branch": data["default_branch"],
        "language": data["language"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "url": data["html_url"],
    }


@mcp.tool()
async def get_latest_commits(
    owner: str,
    repo: str,
) -> dict:
    """Get the latest commits of a GitHub repository."""

    url = f"https://api.github.com/repos/{owner}/{repo}/commits"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    async with AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
        )

    if response.status_code == 404:
        return {
            "error": "Repository not found",
            "owner": owner,
            "repo": repo,
        }

    if response.status_code != 200:
        return {
            "error": "GitHub API request failed",
            "status_code": response.status_code,
            "message": response.text,
        }

    data = response.json()

    return {
        "latest_commits": [
            {
                "sha": commit["sha"],
                "author": commit["commit"]["author"]["name"],
                "message": commit["commit"]["message"],
                "url": commit["html_url"],
            }
            for commit in data[:5]
        ]
    }


def extract_text_from_file(path: str) -> str:

    extension = os.path.splitext(path)[1].lower()

    if extension == ".pdf":

        reader = PdfReader(path)

        pages = []

        for page in reader.pages:
            pages.append(page.extract_text() or "")

        return "\n".join(pages)

    if extension in [".txt", ".md"]:

        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    if extension == ".docx":

        document = Document(path)

        paragraphs = [paragraph.text for paragraph in document.paragraphs]

        return "\n".join(paragraphs)

    raise ValueError(f"Unsupported document type: {extension}")


async def download_document(url: str) -> bytes:

    async with AsyncClient(follow_redirects=True) as client:

        response = await client.get(url)

        response.raise_for_status()

        return response.content


@mcp.tool()
async def read_document(
    source: str,
    # question: str,
) -> str:
    """
    Read a document from a local file path or URL.

    Supports PDF, TXT, Markdown and DOCX documents.
    Returns the document content so the LLM can answer
    the user's question.
    """

    is_url = source.startswith(("http://", "https://"))

    if is_url:

        document_bytes = await download_document(source)

        extension = os.path.splitext(source.split("?")[0])[1].lower()

        if extension == ".pdf":

            reader = PdfReader(io.BytesIO(document_bytes))

            pages = []

            for page in reader.pages:
                pages.append(page.extract_text() or "")

            text = "\n".join(pages)

        elif extension in [".txt", ".md"]:

            text = document_bytes.decode("utf-8")

        else:

            return f"Unsupported URL document type: {extension}"

    else:

        text = extract_text_from_file(source)

    return text


if __name__ == "__main__":
    mcp.run()

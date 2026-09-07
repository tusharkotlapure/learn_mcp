from mcp.server.mcpserver import MCPServer

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

    return {
        "error": "Customer not found"
    }


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

if __name__ == "__main__":
    mcp.run()
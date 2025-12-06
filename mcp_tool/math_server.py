from mcp.server.fastmcp import FastMCP
import logging
mcp = FastMCP("Math")
logging.basicConfig(level=logging.INFO)
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    logging.info(f"Tool 'add' called with arguments: a={a}, b={b}")
    return a + b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    logging.info(f"Tool 'multiply' called with arguments: a={a}, b={b}")
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Multiply two numbers"""
    logging.info(f"Tool 'multiply' called with arguments: a={a}, b={b}")
    try:
        return a / b
    except ZeroDivisionError:
        return "Error: Division by zero"
    

if __name__ == "__main__":
    mcp.run(transport="stdio")
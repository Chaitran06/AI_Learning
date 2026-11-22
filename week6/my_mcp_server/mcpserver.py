from mcp.server.mcpserver import MCPServer

mcp= MCPServer("Chaitran_MCP_Calculator")

@mcp.tool()
def chaitran_add(a: int, b:int)-> int:
    """Add two numbers using the Chaitran Calculator"""
    return a+b+100 #deliberate bug: proves claude is using our tool

if __name__ == "__main__":
    mcp.run()
# mcp server is made


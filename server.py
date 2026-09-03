from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
# FastMCP makes it incredibly easy to define tools by just wrapping Python functions.
mcp = FastMCP("AskMe")

# We can store some basic in-memory state for now until we discuss the database
# This is just a placeholder for our actual data store.
KNOWLEDGE_BASE = {}

@mcp.tool()
def ingest_data(content: str, source: str) -> str:
    """
    Ingest data into the AskMe knowledge base.
    
    Args:
        content: The text content to ingest.
        source: The source of the content (e.g., URL, filename, or topic name).
    """
    # TODO: Implement actual data ingestion logic (e.g., chunking, embeddings, vector DB)
    KNOWLEDGE_BASE[source] = content
    return f"Successfully ingested {len(content)} characters of data from '{source}'."

@mcp.tool()
def ask_question(query: str) -> str:
    """
    Ask a question to the AskMe knowledge base.
    
    Args:
        query: The user's question.
    """
    # TODO: Implement actual retrieval and LLM generation (RAG) logic
    if not KNOWLEDGE_BASE:
        return "The knowledge base is currently empty. Please use ingest_data first."
    
    # Placeholder response that just dumps what we know
    sources = list(KNOWLEDGE_BASE.keys())
    return f"This is a placeholder answer for the query: '{query}'.\nWe currently have data from: {sources}.\n\n(Real retrieval and synthesis will be implemented soon!)"

if __name__ == "__main__":
    # Run the server using stdio transport (perfect for local CLI usage)
    # When deployed to a central server, this can be switched to run via SSE.
    mcp.run()

class BaseTool:
    name: str = "BaseTool"
    description: str = "Base interface for all MCP tools"

    def execute(self, input_data: dict) -> dict:
        raise NotImplementedError("Subclasses must implement execute method.")

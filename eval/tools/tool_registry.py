"""
Tool Registry — Decorator-Based Tool Registration

All agent tools (pdf_knowledge, web_search, image_search, visit, zoom,
code_interpreter) are registered via the @register_tool decorator and
discovered at runtime through this registry.

Tools follow a uniform BaseTool interface (see tools/base.py) exposing:
  - name: str — unique tool identifier
  - description: str — LLM-facing description injected into the system prompt
  - schema: dict — OpenAI function-calling JSON Schema
  - execute(params) -> str — synchronous tool execution

NOTE: Partial release showing the registry pattern. Full tool implementations
available upon paper acceptance.
"""

TOOL_REGISTRY = {}


def register_tool(name=None):
    """
    Decorator that registers a tool class in the global registry.

    Usage:
        @register_tool("pdf_knowledge")
        class PDFKnowledgeTool(BaseTool):
            ...
    """
    def decorator(cls):
        tool_name = name or cls.name
        if tool_name in TOOL_REGISTRY:
            print(f"Warning: Tool '{tool_name}' already registered, overwriting.")
        TOOL_REGISTRY[tool_name] = cls
        cls.name = tool_name
        return cls
    return decorator


def get_tool(name):
    """Retrieve a tool class by name. Raises ValueError if not found."""
    if name not in TOOL_REGISTRY:
        available = list(TOOL_REGISTRY.keys())
        raise ValueError(
            f"Tool '{name}' not found. Available: {', '.join(available)}"
        )
    return TOOL_REGISTRY[name]


def list_tools():
    """Return a list of all registered tool names."""
    return list(TOOL_REGISTRY.keys())

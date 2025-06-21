from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ToolResult:
    """Result from executing a tool."""
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ResourceResult:
    """Result from reading a resource."""
    content: str
    mime_type: str = "text/plain"
    metadata: Optional[Dict[str, Any]] = None

class BaseTool(ABC):
    """Base class for MCP tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for tool inputs."""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

class BaseResource(ABC):
    """Base class for MCP resources."""
    
    @property
    @abstractmethod
    def uri(self) -> str:
        """Resource URI."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Resource name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Resource description."""
        pass
    
    @abstractmethod
    async def read(self) -> ResourceResult:
        """Read the resource content."""
        pass

class BasePrompt(ABC):
    """Base class for MCP prompts."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Prompt name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Prompt description."""
        pass
    
    @property
    @abstractmethod
    def arguments(self) -> List[Dict[str, Any]]:
        """Prompt arguments schema."""
        pass
    
    @abstractmethod
    async def generate(self, arguments: Dict[str, Any]) -> str:
        """Generate prompt content with given arguments."""
        pass 
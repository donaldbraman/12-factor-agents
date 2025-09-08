"""
Tool definitions for 12-factor agents.
Factor 4: Tools are structured outputs.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from datetime import datetime
import json


class ToolCall(BaseModel):
    """
    Factor 1: Natural language to tool calls.
    Structured representation of a tool invocation.
    """
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }


class ToolResponse(BaseModel):
    """
    Factor 4: Tools are structured outputs.
    Standardized response from all tools.
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        if self.success:
            return f"Success: {json.dumps(self.data, indent=2) if self.data else 'No data'}"
        else:
            return f"Error: {self.error}"


class Tool(ABC):
    """
    Base class for all agent tools.
    Ensures structured input/output.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.call_count = 0
        self.last_call: Optional[datetime] = None
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResponse:
        """Execute tool with parameters and return structured response"""
        pass
    
    def __call__(self, **kwargs) -> ToolResponse:
        """Make tool callable with tracking"""
        self.call_count += 1
        self.last_call = datetime.now()
        
        try:
            # Validate parameters
            validated_params = self.validate_parameters(**kwargs)
            
            # Execute tool
            result = self.execute(**validated_params)
            
            # Add metadata
            result.metadata.update({
                "tool_name": self.name,
                "call_count": self.call_count,
                "execution_time": (datetime.now() - self.last_call).total_seconds()
            })
            
            return result
            
        except Exception as e:
            return ToolResponse(
                success=False,
                error=str(e),
                metadata={
                    "tool_name": self.name,
                    "call_count": self.call_count
                }
            )
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Override to add parameter validation"""
        return kwargs
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema for LLM understanding"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters_schema()
        }
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        pass


class FileTool(Tool):
    """Example tool implementation for file operations"""
    
    def __init__(self):
        super().__init__(
            name="file_tool",
            description="Read, write, and manipulate files"
        )
    
    def execute(self, operation: str, path: str, content: Optional[str] = None) -> ToolResponse:
        """Execute file operation"""
        from pathlib import Path
        
        file_path = Path(path)
        
        try:
            if operation == "read":
                if not file_path.exists():
                    return ToolResponse(
                        success=False,
                        error=f"File not found: {path}"
                    )
                
                content = file_path.read_text()
                return ToolResponse(
                    success=True,
                    data={
                        "path": str(file_path),
                        "content": content,
                        "size": len(content)
                    }
                )
                
            elif operation == "write":
                if content is None:
                    return ToolResponse(
                        success=False,
                        error="Content required for write operation"
                    )
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                
                return ToolResponse(
                    success=True,
                    data={
                        "path": str(file_path),
                        "bytes_written": len(content)
                    }
                )
                
            elif operation == "exists":
                return ToolResponse(
                    success=True,
                    data={
                        "path": str(file_path),
                        "exists": file_path.exists()
                    }
                )
                
            else:
                return ToolResponse(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                error=str(e)
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "exists"],
                    "description": "File operation to perform"
                },
                "path": {
                    "type": "string",
                    "description": "File path"
                },
                "content": {
                    "type": "string",
                    "description": "Content for write operation"
                }
            },
            "required": ["operation", "path"]
        }


class HumanInteractionTool(Tool):
    """
    Factor 7: Contact humans with tool calls.
    Tool for structured human interaction.
    """
    
    def __init__(self):
        super().__init__(
            name="human_interaction",
            description="Request human input or approval"
        )
    
    def execute(self, interaction_type: str, message: str, context: Optional[Dict] = None) -> ToolResponse:
        """Request human interaction"""
        from pathlib import Path
        import json
        import time
        
        request_id = f"human_request_{int(time.time())}"
        request_file = Path(f"/tmp/{request_id}.json")
        response_file = Path(f"/tmp/{request_id}_response.json")
        
        # Write request for human
        request = {
            "id": request_id,
            "type": interaction_type,
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "response_file": str(response_file)
        }
        
        request_file.write_text(json.dumps(request, indent=2))
        
        # Wait for response (with timeout)
        timeout = 300  # 5 minutes
        start = time.time()
        
        while time.time() - start < timeout:
            if response_file.exists():
                response_data = json.loads(response_file.read_text())
                
                # Clean up files
                request_file.unlink()
                response_file.unlink()
                
                return ToolResponse(
                    success=True,
                    data=response_data
                )
            
            time.sleep(1)
        
        # Timeout
        return ToolResponse(
            success=False,
            error=f"Human response timeout after {timeout} seconds"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "interaction_type": {
                    "type": "string",
                    "enum": ["approval", "input", "clarification"],
                    "description": "Type of human interaction"
                },
                "message": {
                    "type": "string",
                    "description": "Message to human"
                },
                "context": {
                    "type": "object",
                    "description": "Additional context"
                }
            },
            "required": ["interaction_type", "message"]
        }
import json
import os
import platform
from typing import Dict, Any
from ..common.base import BaseResource, ResourceResult

# Optional import for psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SystemInfoResource(BaseResource):
    """Resource that provides system information."""
    
    @property
    def uri(self) -> str:
        return "system://info"
    
    @property
    def name(self) -> str:
        return "system_info"
    
    @property
    def description(self) -> str:
        return "System information and statistics"
    
    async def read(self) -> ResourceResult:
        try:
            # Get system information
            system_info = {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor()
                },
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation(),
                    "compiler": platform.python_compiler()
                }
            }
            
            # Add psutil-based info if available
            if PSUTIL_AVAILABLE:
                system_info.update({
                    "memory": {
                        "total": psutil.virtual_memory().total,
                        "available": psutil.virtual_memory().available,
                        "percent": psutil.virtual_memory().percent
                    },
                    "disk": {
                        "total": psutil.disk_usage('/').total,
                        "free": psutil.disk_usage('/').free,
                        "percent": psutil.disk_usage('/').percent
                    },
                    "cpu": {
                        "count": psutil.cpu_count(),
                        "percent": psutil.cpu_percent(interval=1)
                    }
                })
            else:
                system_info["note"] = "psutil not available - limited system info"
            
            return ResourceResult(json.dumps(system_info, indent=2), "application/json")
        except Exception as e:
            return ResourceResult(f"Error reading system info: {str(e)}", "text/plain")

class FileResource(BaseResource):
    """Resource that reads file content."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    @property
    def uri(self) -> str:
        return f"file://{self.file_path}"
    
    @property
    def name(self) -> str:
        return os.path.basename(self.file_path)
    
    @property
    def description(self) -> str:
        return f"File content: {self.file_path}"
    
    async def read(self) -> ResourceResult:
        try:
            if not os.path.exists(self.file_path):
                return ResourceResult(f"File not found: {self.file_path}", "text/plain")
            
            with open(self.file_path, 'r') as f:
                content = f.read()
            
            return ResourceResult(content, "text/plain")
        except Exception as e:
            return ResourceResult(f"Error reading file: {str(e)}", "text/plain") 
import yaml
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Configuration for a single MCP server."""
    name: str
    description: str
    enabled: bool = True
    transport: str = "http"  # "http" or "stdio"
    
    # HTTP transport fields
    url: Optional[str] = None
    
    # STDIO transport fields  
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    working_dir: Optional[str] = None

class ConfigManager:
    """Manages MCP server configurations."""
    
    def __init__(self, config_path: str = "config/mcp_servers.yml"):
        self.config_path = config_path
        self.servers: Dict[str, ServerConfig] = {}
        self.load_config()
    
    def load_config(self):
        """Load server configurations from YAML file."""
        if not os.path.exists(self.config_path):
            print(f"Config file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            servers_data = config_data.get('servers', {})
            for server_id, server_data in servers_data.items():
                if server_data.get('enabled', True):
                    transport = server_data.get('transport', 'http')
                    
                    self.servers[server_id] = ServerConfig(
                        name=server_data['name'],
                        description=server_data.get('description', ''),
                        enabled=server_data.get('enabled', True),
                        transport=transport,
                        # HTTP fields
                        url=server_data.get('url'),
                        # STDIO fields
                        command=server_data.get('command'),
                        args=server_data.get('args'),
                        env=server_data.get('env'),
                        working_dir=server_data.get('working_dir')
                    )
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get a specific server configuration."""
        return self.servers.get(server_id)
    
    def get_server_config(self, server_id: str) -> Optional[ServerConfig]:
        """Alias for get_server for consistency."""
        return self.get_server(server_id)
    
    def list_servers(self) -> List[tuple]:
        """List all enabled servers with their IDs."""
        return [(server_id, config) for server_id, config in self.servers.items()]
    
    def get_server_url(self, server_id: str) -> Optional[str]:
        """Get the URL for a specific server."""
        server = self.get_server(server_id)
        return server.url if server else None 
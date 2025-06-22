import yaml
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Configuration for a single MCP server."""
    name: str
    url: str
    description: str
    enabled: bool = True

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
                    self.servers[server_id] = ServerConfig(
                        name=server_data['name'],
                        url=server_data['url'],
                        description=server_data.get('description', ''),
                        enabled=server_data.get('enabled', True)
                    )
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get a specific server configuration."""
        return self.servers.get(server_id)
    
    def list_servers(self) -> List[tuple]:
        """List all enabled servers with their IDs."""
        return [(server_id, config) for server_id, config in self.servers.items()]
    
    def get_server_url(self, server_id: str) -> Optional[str]:
        """Get the URL for a specific server."""
        server = self.get_server(server_id)
        return server.url if server else None 
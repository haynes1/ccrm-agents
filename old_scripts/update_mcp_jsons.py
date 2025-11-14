import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MCPGenerator:
    def __init__(self):
        # Database connection
        self.db_url = (
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
            f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Base paths
        self.agents_path = Path("agents")
        
    def get_agent_data_from_db(self, agent_id: str) -> Dict:
        """Fetch agent data from the database."""
        with self.Session() as session:
            # Get agent profile
            agent_query = text("""
                SELECT * FROM agents 
                WHERE agent_id = :agent_id
            """)
            agent_result = session.execute(agent_query, {"agent_id": agent_id}).fetchone()
            
            if not agent_result:
                raise ValueError(f"Agent {agent_id} not found in database")
            
            # Get agent's tools
            tools_query = text("""
                SELECT t.* 
                FROM tools t
                JOIN agent_tools at ON t.tool_id = at.tool_id
                WHERE at.agent_id = :agent_id
            """)
            tools_result = session.execute(tools_query, {"agent_id": agent_id}).fetchall()
            
            # Get tool configurations if any
            tool_configs_query = text("""
                SELECT * FROM user_custom_tool_configurations
                WHERE agent_id = :agent_id
            """)
            tool_configs = session.execute(tool_configs_query, {"agent_id": agent_id}).fetchall()
            
            return {
                "agent": dict(agent_result),
                "tools": [dict(tool) for tool in tools_result],
                "tool_configs": [dict(config) for config in tool_configs]
            }
    
    def read_system_prompt(self, agent_path: Path) -> str:
        """Read the system prompt from the agent's directory."""
        prompt_path = agent_path / "prompts" / "system_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"System prompt not found at {prompt_path}")
        
        with open(prompt_path, "r") as f:
            return f.read()
    
    def generate_mcp_json(self, agent_id: str) -> Dict:
        """Generate MCP JSON for an agent by combining local files and database data."""
        agent_path = self.agents_path / agent_id
        if not agent_path.exists():
            raise FileNotFoundError(f"Agent directory not found: {agent_path}")
        
        # Get data from database
        db_data = self.get_agent_data_from_db(agent_id)
        
        # Read system prompt
        system_prompt = self.read_system_prompt(agent_path)
        
        # Combine tool configurations with tool definitions
        tools = []
        for tool in db_data["tools"]:
            tool_config = next(
                (config for config in db_data["tool_configs"] 
                 if config["tool_id"] == tool["tool_id"]),
                None
            )
            
            if tool_config:
                # Merge tool configuration with tool definition
                tool_data = {**tool, **tool_config}
            else:
                tool_data = tool
            
            tools.append(tool_data)
        
        # Generate MCP JSON
        mcp_json = {
            "agent_id": agent_id,
            "name": db_data["agent"]["name"],
            "description": db_data["agent"]["description"],
            "system_prompt": system_prompt,
            "llm_model": db_data["agent"]["llm_model_id"],
            "tools": tools
        }
        
        # Save MCP JSON
        mcp_path = agent_path / "configs" / "mcp.json"
        with open(mcp_path, "w") as f:
            json.dump(mcp_json, f, indent=2)
        
        return mcp_json
    
    def update_all_agents(self):
        """Update MCP JSONs for all agents in the agents directory."""
        for agent_dir in self.agents_path.iterdir():
            if agent_dir.is_dir():
                try:
                    print(f"Updating MCP JSON for agent: {agent_dir.name}")
                    self.generate_mcp_json(agent_dir.name)
                    print(f"Successfully updated {agent_dir.name}")
                except Exception as e:
                    print(f"Error updating {agent_dir.name}: {str(e)}")

def main():
    generator = MCPGenerator()
    generator.update_all_agents()

if __name__ == "__main__":
    main() 
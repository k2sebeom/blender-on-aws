from pathlib import Path
from typing import Dict
import streamlit as st

class WorkspaceService:
    """Service class to handle workspace-related operations."""
    
    def __init__(self, config: Dict):
        """
        Initialize workspace service with configuration.
        
        Args:
            config (Dict): Application configuration dictionary
        """
        self.config = config
        self.workspace_root = Path(config['workspace']['root'])
    
    def initialize_workspace(self) -> bool:
        """
        Initialize workspace directory structure.
        Creates the workspace root directory and required subdirectories.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Create workspace root if it doesn't exist
            self.workspace_root.mkdir(parents=True, exist_ok=True)

            return True    
        except Exception as e:
            st.error(f"Error initializing workspace: {e}")
            return False
    
    def get_workspace_path(self) -> Path:
        """
        Get the workspace root path.
        
        Returns:
            Path: Workspace root path
        """
        return self.workspace_root

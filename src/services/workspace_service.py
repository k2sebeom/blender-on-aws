from pathlib import Path
from typing import Dict
from datetime import datetime
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
    
    def create_job_directory(self, job_name: str) -> Path:
        """
        Create a directory for the job under workspace root.
        
        Args:
            job_name (str): Name of the job
            
        Returns:
            Path: Path to the created job directory
        """
        job_dir = self.workspace_root / job_name
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir
    
    def create_run_directory(self, job_dir: Path) -> Path:
        """
        Create a run directory under the job directory with human readable timestamp.
        
        Args:
            job_dir (Path): Path to the job directory
            
        Returns:
            Path: Path to the created run directory
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = job_dir / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create src directory under run directory
        src_dir = run_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        return run_dir
    
    def store_uploaded_file(self, file_data: bytes, filename: str, run_dir: Path) -> Path:
        """
        Store an uploaded file in the src directory under the run directory.
        
        Args:
            file_data (bytes): Content of the uploaded file
            filename (str): Name of the file
            run_dir (Path): Path to the run directory
            
        Returns:
            Path: Path where the file was stored
        """
        file_path = run_dir / "src" / filename
        file_path.write_bytes(file_data)
        return file_path

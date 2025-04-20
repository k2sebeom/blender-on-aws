from pathlib import Path
from typing import Dict
from datetime import datetime
import streamlit as st
import shutil
import json
from typing import List, Tuple
from src.models.db import Job


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
        self.items_per_page = 10  # Default pagination size
    
    def initialize_workspace(self) -> bool:
        """
        Initialize workspace directory structure.
        Creates the workspace root directory and required subdirectories.
        Copies scripts folder to workspace root.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Create workspace root if it doesn't exist
            self.workspace_root.mkdir(parents=True, exist_ok=True)
            
            # Copy scripts folder to workspace root
            scripts_dir = Path('scripts')
            workspace_scripts_dir = self.workspace_root / 'scripts'
            if scripts_dir.exists() and not workspace_scripts_dir.exists():
                shutil.copytree(scripts_dir, workspace_scripts_dir)

            return True    
        except Exception as e:
            st.error(f"Error initializing workspace: {e}")
            return False
        
    def parse_job_directory(self, job: Job) -> Path:
        return self.workspace_root / 'jobs' / f'{job.name}-{job.id}'
    
    def create_job_directory(self, job: Job, file_data: bytes, filename: str) -> Path:
        """
        Create a directory for the job under workspace root.
        
        Args:
            job (Job): Created job instance
            file_data (bytes): Blender file content
            filename (str): Name of the source file
            
        Returns:
            Path: Path to the created job directory
        """
        job_dir = self.parse_job_directory(job)
        job_dir.mkdir(parents=True, exist_ok=True)

        src_dir = job_dir / 'src'
        src_dir.mkdir()
        file_path = src_dir / filename
        file_path.write_bytes(file_data)

        return job_dir

    def get_output_files(self, job: Job) -> List[Tuple[Path, Path]]:
        job_dir = self.parse_job_directory(job)
        render_dir = job_dir / 'render'
        static_dir = job_dir / 'static'

        render_files = list(render_dir.glob('*')) if render_dir.exists() else []

        # Get both compressed and original files
        render_pairs = []
        if render_dir.exists() and static_dir.exists():
            for render_file in render_files:
                static_files = static_dir.glob(f"{render_file.stem}.*")
                if static_files:
                    render_pairs.append((render_file, next(static_files)))

        return render_pairs

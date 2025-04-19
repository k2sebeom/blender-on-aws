from pathlib import Path
from typing import Dict, List
from datetime import datetime
import streamlit as st
import subprocess
import glob
import shutil

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
        Copies scripts folder to workspace root.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Create workspace root if it doesn't exist
            self.workspace_root.mkdir(parents=True, exist_ok=True)
            
            # Copy scripts folder to workspace root
            scripts_dir = Path('scripts')
            if scripts_dir.exists():
                workspace_scripts_dir = self.workspace_root / 'scripts'
                if workspace_scripts_dir.exists():
                    shutil.rmtree(workspace_scripts_dir)
                shutil.copytree(scripts_dir, workspace_scripts_dir)

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
    
    def render_blend_file(self, blend_file: Path, run_dir: Path, frame_range: str) -> List[Path]:
        """
        Create render directory and execute blender render command.
        
        Args:
            blend_file (Path): Path to the .blend file
            run_dir (Path): Path to the run directory
            frame_range (str): Frame range to render
            
        Returns:
            List[Path]: List of paths to rendered PNG files
        """
        # Create render directory
        render_dir = run_dir / "render"
        render_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare render output path template
        output_template = str(render_dir / "######")
        
        # Construct and execute blender command
        cmd = [
            "blender",
            "-b",  # background mode
            "-y",  # yes to all
            str(blend_file),
            "--scene", "Scene",
            "--render-output", output_template,
            "--render-format", "PNG",
            "--render-frame", frame_range
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Get list of rendered PNG files
            rendered_files = sorted(Path(render_dir).glob("*.png"))
            
            if not rendered_files:
                raise Exception("No rendered files found")
                
            return rendered_files
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Blender render failed: {e.stderr}")
        except Exception as e:
            raise Exception(f"Error during rendering: {str(e)}")

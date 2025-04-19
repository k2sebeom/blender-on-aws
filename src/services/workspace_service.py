from pathlib import Path
from typing import Dict
from datetime import datetime
import streamlit as st
import shutil
from typing import List, Tuple

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
        job_dir = self.workspace_root / 'jobs' / job_name
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

    def get_paginated_jobs(self, page: int = 1) -> Tuple[List[Dict], int]:
        """
        Get a paginated list of jobs with their details.
        
        Args:
            page (int): Page number (1-based)
            
        Returns:
            Tuple[List[Dict], int]: (List of job details, total number of pages)
        """
        jobs_dir = self.workspace_root / 'jobs'
        if not jobs_dir.exists():
            return [], 0

        all_jobs = []
        for job in jobs_dir.iterdir():
            if not job.is_dir():
                continue
            
            runs = self.get_job_runs(job.name)
            num_runs = len(runs)
            
            # Get creation time of the job directory
            created_at = datetime.fromtimestamp(job.stat().st_ctime)
            
            job_info = {
                "name": job.name,
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "num_runs": num_runs
            }
            all_jobs.append(job_info)

        # Sort jobs by creation time (newest first)
        all_jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Calculate pagination
        total_jobs = len(all_jobs)
        total_pages = (total_jobs + self.items_per_page - 1) // self.items_per_page
        
        # Get jobs for current page
        start_idx = (page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        paginated_jobs = all_jobs[start_idx:end_idx]
        
        return paginated_jobs, total_pages

    def get_job_runs(self, job_name: str) -> List[str]:
        """
        Get a list of all runs for a specific job.
        
        Args:
            job_name (str): Name of the job
            
        Returns:
            List[str]: List of run timestamps
        """
        job_dir = self.workspace_root / 'jobs' / job_name
        if not job_dir.exists():
            return []
        return sorted([run.name for run in job_dir.iterdir() if run.is_dir()], reverse=True)

    def get_job_stats(self) -> Tuple[int, int, float]:
        """
        Get statistics about jobs.
        
        Returns:
            Tuple[int, int, float]: (active jobs, completed today, average render time in minutes)
        """
        jobs_dir = self.workspace_root / 'jobs'
        if not jobs_dir.exists():
            return (0, 0, 0)

        today = datetime.now().strftime("%Y-%m-%d")
        completed_today = 0
        total_render_time = 0
        total_jobs = 0

        for job in jobs_dir.iterdir():
            if not job.is_dir():
                continue
            
            # Count runs completed today
            for run in job.iterdir():
                if not run.is_dir():
                    continue
                run_date = run.name.split('_')[0]
                if run_date == today:
                    completed_today += 1
                    total_jobs += 1

        avg_render_time = total_render_time / total_jobs if total_jobs > 0 else 0
        active_jobs = len([job for job in jobs_dir.iterdir() if job.is_dir()])

        return (active_jobs, completed_today, avg_render_time)

    def get_run_details(self, job_name: str, run_id: str) -> Tuple[List[Path], List[Path]]:
        """
        Get source files and render outputs for a specific run.
        
        Args:
            job_name (str): Name of the job
            run_id (str): Run timestamp
            
        Returns:
            Tuple[List[Path], List[Path]]: (source files, render outputs)
        """
        run_dir = self.workspace_root / 'jobs' / job_name / run_id
        if not run_dir.exists():
            return ([], [])

        src_dir = run_dir / "src"
        render_dir = run_dir / "render"

        source_files = list(src_dir.glob('*')) if src_dir.exists() else []
        render_files = list(render_dir.glob('*.png')) if render_dir.exists() else []

        return (source_files, render_files)

    def get_run_stats(self, job_name: str, run_id: str) -> Dict:
        """
        Get statistics for a specific run.
        
        Args:
            job_name (str): Name of the job
            run_id (str): Run timestamp
            
        Returns:
            Dict: Run statistics including number of rendered files and total render time
        """
        run_dir = self.workspace_root / 'jobs' / job_name / run_id
        if not run_dir.exists():
            return {"num_files": 0, "render_time": 0}

        render_dir = run_dir / "render"
        if not render_dir.exists():
            return {"num_files": 0, "render_time": 0}

        render_files = list(render_dir.glob('*.png'))
        num_files = len(render_files)

        # Calculate total render time
        if num_files > 0:
            dir_creation_time = datetime.fromtimestamp(run_dir.stat().st_ctime)
            last_render_time = max(datetime.fromtimestamp(f.stat().st_mtime) for f in render_files)
            render_time = (last_render_time - dir_creation_time).total_seconds() / 60  # Convert to minutes
        else:
            render_time = 0

        return {
            "num_files": num_files,
            "render_time": round(render_time, 2)
        }

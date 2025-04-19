from pathlib import Path
from typing import List
import subprocess

class BlenderService:
    """Service class to handle Blender-related operations."""
    
    def __init__(self, workspace_root: Path):
        """
        Initialize blender service.
        
        Args:
            workspace_root (Path): Path to workspace root directory
        """
        self.workspace_root = workspace_root
    
    def render_blend_file(self, blend_file: Path, run_dir: Path, frame_range: str) -> tuple[List[Path], str, str]:
        """
        Create render directory and execute blender render command.
        
        Args:
            blend_file (Path): Path to the .blend file
            run_dir (Path): Path to the run directory
            frame_range (str): Frame range to render
            
        Returns:
            tuple[List[Path], str, str]: Tuple containing:
                - List of paths to rendered PNG files
                - stdout from the render process
                - stderr from the render process
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
            "-P", str(self.workspace_root / "scripts" / "cycles.py"),  # Run GPU setup script
            "--scene", "Scene",
            "--render-output", output_template,
            "--render-format", "PNG",
            "--render-frame", frame_range.replace(' ', ''),
        ]
        
        try:
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Get list of rendered PNG files
            rendered_files = sorted(Path(render_dir).glob("*.png"))
            
            if not rendered_files:
                rendered_files = []

            return rendered_files, process.stdout, process.stderr
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Blender render failed: {e.stderr}")
        except Exception as e:
            raise Exception(f"Error during rendering: {str(e)}")

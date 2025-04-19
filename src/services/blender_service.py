from pathlib import Path
from typing import List, Tuple
import subprocess
from .ffmpeg_service import FFmpegService

class BlenderService:
    """Service class to handle Blender-related operations."""
    
    def __init__(self, workspace_root: Path):
        """
        Initialize blender service.
        
        Args:
            workspace_root (Path): Path to workspace root directory
        """
        self.workspace_root = workspace_root
        self.ffmpeg_service = FFmpegService()
        
    def render_blend_file(self, blend_file: Path, run_dir: Path, mode: str = "still", start_frame: int = 1, end_frame: int = None, frames_input: str = None) -> tuple[List[Tuple[Path, Path]], str, str]:
        """
        Create render directory and execute blender render command.
        
        Args:
            blend_file (Path): Path to the .blend file
            run_dir (Path): Path to the run directory
            mode (str): Render mode - either "still" or "anim"
            start_frame (int): Start frame number (default: 1)
            end_frame (int): End frame number for animation mode (default: None)
            frames_input (str): Render target frames (default: None)
            
        Returns:
            tuple[List[Tuple[Path, Path]], str, str]: Tuple containing:
                - List of tuples:
                  * For still images: (compressed_jpg_path, original_png_path) pairs
                  * For animations: [(source_video, mkv_video)] (single pair)
                - stdout from the render process
                - stderr from the render process
        """
        # Create render directory
        render_dir = run_dir / "render"
        render_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare render output path template
        output_template = str(render_dir / "######")
        
        # Base command
        cmd = [
            "blender",
            "-b",  # background mode
            "-y",  # yes to all
            str(blend_file),
            "-P", str(self.workspace_root / "scripts" / "cycles.py"),  # Run GPU setup script
            "--scene", "Scene",
            "--render-output", output_template,
            "--render-format", "PNG" if mode == "still" else "FFMPEG",
        ]

        # Add mode-specific arguments
        if mode == "still":
            if frames_input:
                cmd.extend(["-f", frames_input])
            else:
                cmd.extend(["-f", 1])
        else:  # anim mode
            cmd.extend(["-s", str(start_frame)])
            if end_frame is not None:
                cmd.extend(["-e", str(end_frame)])
            cmd.append("-a")
        
        try:
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if mode == "still":
                # Get list of rendered PNG files
                rendered_files = sorted(Path(render_dir).glob("*.png"))
                
                if not rendered_files:
                    rendered_files = []

                # Compress rendered files to JPG format
                compressed_pairs = self.ffmpeg_service.compress_images(rendered_files, run_dir)
                
                return compressed_pairs, process.stdout, process.stderr
            else:
                # For animation mode, convert the rendered video to mp4
                rendered_video = next(Path(render_dir).glob("*"), None)
                if rendered_video:
                    video_pair = self.ffmpeg_service.convert_to_mp4(rendered_video, run_dir)
                    return [video_pair], process.stdout, process.stderr
                return [], process.stdout, process.stderr
        except subprocess.CalledProcessError as e:
            raise Exception(f"Blender render failed: {e.stderr}")
        except Exception as e:
            raise Exception(f"Error during rendering: {str(e)}")

from pathlib import Path
from typing import List, Tuple
import subprocess
from blender_on_aws.services.ffmpeg_service import FFmpegService
from blender_on_aws.models.db import Job
from blender_on_aws.models.job import RenderMode


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
        
    def render_blend_file(self, job_dir: Path, job: Job) -> tuple[List[Tuple[Path, Path]], str, str]:
        """
        Create render directory and execute blender render command.
        
        Args:
            job_dir: Job directory
            job: Job definition

        Returns:
            tuple[List[Tuple[Path, Path]], str, str]: Tuple containing:
                - List of tuples:
                  * For still images: (compressed_jpg_path, original_png_path) pairs
                  * For animations: [(source_video, mkv_video)] (single pair)
                - stdout from the render process
                - stderr from the render process
        """
        # Create render directory
        render_dir = job_dir / "render"
        render_dir.mkdir(parents=True, exist_ok=True)

        # Create static directory
        static_dir = job_dir / "static"
        static_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare render output path template
        output_template = str(render_dir / "######")
        
        blend_file = job_dir / 'src' / job.source_file

        # Base command
        cmd = [
            "blender",
            "-b",  # background mode
            "-y",  # yes to all
            str(blend_file),
            "-P", str(self.workspace_root / "scripts" / "cycles.py"),  # Run GPU setup script
            "--render-output", output_template,
            "--render-format", "PNG" if job.mode == RenderMode.still else "FFMPEG",
        ]

        # Add mode-specific arguments
        if job.mode == RenderMode.still:
            cmd.extend(["-f", job.frame_range])
        else:  # anim mode
            frames = str(job.frame_range).split('-')
            cmd.extend(["-s", str(frames[0])])
            if len(frames) > 1:
                cmd.extend(["-e", str(frames[1])])
            cmd.append("-a")
        
        try:
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if job.mode == RenderMode.still:
                # Get list of rendered PNG files
                rendered_files = sorted(render_dir.glob("*.png"))
                
                if not rendered_files:
                    rendered_files = []

                # Compress rendered files to JPG format
                compressed_pairs = self.ffmpeg_service.compress_images(rendered_files, job_dir)
                
                return compressed_pairs, process.stdout, process.stderr
            else:
                # For animation mode, convert the rendered video to mp4
                rendered_video = next(render_dir.glob("*"), None)
                if rendered_video:
                    video_pair = self.ffmpeg_service.convert_to_mp4(rendered_video, job_dir)
                    return [video_pair], process.stdout, process.stderr
                return [], process.stdout, process.stderr
        except subprocess.CalledProcessError as e:
            raise Exception(f"Blender render failed: {e.stderr}")
        except Exception as e:
            raise Exception(f"Error during rendering: {str(e)}")

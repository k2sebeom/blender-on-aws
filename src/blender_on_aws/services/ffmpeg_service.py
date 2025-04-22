from pathlib import Path
from typing import List, Tuple
import subprocess

class FFmpegService:
    """Service class to handle FFmpeg-related operations."""
    
    def __init__(self):
        """Initialize FFmpeg service."""
        pass
    
    def convert_to_mp4(self, video_file: Path, run_dir: Path) -> Tuple[Path, Path]:
        """
        Convert rendered video to MP4 format.
        
        Args:
            video_file (Path): Path to the input video file
            run_dir (Path): Path to the run directory
            
        Returns:
            Path: Path to the converted MP4 file
        """
        # Create static directory for the MP4 file
        static_dir = run_dir / "static"
        static_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output mp4 path
        mp4_filename = video_file.stem + ".mp4"
        mp4_path = static_dir / mp4_filename
        
        # Construct ffmpeg command for video conversion
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output files
            "-i", str(video_file),  # Input file
            "-c:v", "libx264",  # Use H.264 codec
            "-preset", "medium",  # Encoding speed preset
            "-crf", "23",  # Quality (0-51, lower is better)
            "-pix_fmt", "yuv420p",  # Pixel format for better compatibility
            str(mp4_path)  # Output file
        ]
        
        try:
            # Execute ffmpeg command
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return (video_file, mp4_path)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Video conversion failed: {e.stderr}")
        except Exception as e:
            raise Exception(f"Error during video conversion: {str(e)}")
    
    def compress_images(self, png_files: List[Path], run_dir: Path) -> List[Tuple[Path, Path]]:
        """
        Compress PNG images to JPG format with 512px width.
        
        Args:
            png_files (List[Path]): List of paths to PNG files
            run_dir (Path): Path to the run directory
            
        Returns:
            List[Tuple[Path, Path]]: List of tuples containing (compressed_jpg_path, original_png_path)
        """
        # Create static directory for compressed images
        static_dir = run_dir / "static"
        static_dir.mkdir(parents=True, exist_ok=True)
        
        compressed_pairs = []
        
        for png_file in png_files:
            # Generate output jpg path
            jpg_filename = png_file.stem + ".jpg"
            jpg_path = static_dir / jpg_filename
            
            # Construct ffmpeg command for compression
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output files
                "-i", str(png_file),  # Input file
                "-vf", "scale=512:-1",  # Scale width to 512, maintain aspect ratio
                "-q:v", "2",  # High quality (1-31, lower is better)
                str(jpg_path)  # Output file
            ]
            
            try:
                # Execute ffmpeg command
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                compressed_pairs.append((png_file, jpg_path))
            except subprocess.CalledProcessError as e:
                print(f"Error compressing {png_file.name}: {e.stderr}")
                continue
            except Exception as e:
                print(f"Unexpected error compressing {png_file.name}: {str(e)}")
                continue
        
        return compressed_pairs

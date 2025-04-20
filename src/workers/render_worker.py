from threading import Thread
from queue import Queue, Empty
from pathlib import Path
from datetime import datetime, timezone
import time

from src.models.db import Job
from src.services.blender_service import BlenderService
from src.services.db_service import DatabaseService
from src.services.workspace_service import WorkspaceService


class RenderWorker(Thread):
    """Worker thread to process render jobs from a queue."""
    
    def __init__(self, workspace_service: WorkspaceService, db_service: DatabaseService):
        """
        Initialize the render worker.
        
        Args:
            workspace_root (Path): Path to workspace root directory
        """
        super().__init__(daemon=True)
        self._queue = Queue()
        self._running = True
        self.blender_service = BlenderService(workspace_service.workspace_root)
        self.db_service = db_service

        self.workspace_service = workspace_service
        self.db_service = db_service

    def enqueue_job(self, job: Job):
        """
        Add a render job to the queue.
        
        Args:
            job (Job): The render job to queue
        """
        self._queue.put(job)
        
    def stop(self):
        """Stop the worker thread."""
        self._running = False

    def render(self, job: Job):
        return
        print(f"Starting {job.name}-{job.id}")

        job_dir = self.workspace_service.parse_job_directory(job)

        _, stdout, stderr = self.blender_service.render_blend_file(
            job_dir=job_dir,
            job=job,
        )
        (job_dir / 'stdout.log').write_text(stdout)
        (job_dir / 'stderr.log').write_text(stderr)

        self.db_service.update_job(
            job.id,
            finished_at=datetime.now(timezone.utc),
        )
        print(f"Completed Job {job.name}-{job.id}")
        return ""

    def run(self):
        """Process jobs from the queue."""
        queued_jobs = self.db_service.get_queued_jobs()

        for job in queued_jobs:
            self.render(job)

        while self._running:
            try:
                # Get job from queue with timeout to allow checking _running flag
                job: Job = self._queue.get(timeout=1.0)

                self.render(job)

                # Process the job
                    # # Extract job parameters
                    # mode = "still" if job.mode == "Still Frame" else "anim"
                    
                    # # Get the run directory from the source file path
                    # run_dir = Path(job.source_file).parent
                    # blend_file = Path(job.source_file)
                    
                    # # Render the file
                    # rendered_files, stdout, stderr = self.blender_service.render_blend_file(
                    #     blend_file=blend_file,
                    #     run_dir=run_dir,
                    #     mode=mode,
                    #     start_frame=job.start_frame,
                    #     end_frame=job.end_frame,
                    #     frames_input=job.frames_input
                    # )
                    
                    # # Update job with completion info
                    # job.finished_time = datetime.now()
                    # job.num_files = len(rendered_files)
                    # job.render_time = int((job.finished_time - job.created_time).total_seconds())
                
            except Empty:
                time.sleep(1)
                continue

from threading import Thread, Lock
from queue import Queue, Empty
from datetime import datetime, timezone
import time

from blender_on_aws.models.db import Job
from blender_on_aws.services.blender_service import BlenderService
from blender_on_aws.services.db_service import DatabaseService
from blender_on_aws.services.workspace_service import WorkspaceService


class RenderWorker(Thread):
    """Worker thread to process render jobs from a queue. Implements the Singleton pattern."""
    
    _instance = None
    _lock = Lock()
    
    @classmethod
    def get_instance(cls, workspace_service: WorkspaceService = None, db_service: DatabaseService = None):
        """
        Get or create the singleton instance of RenderWorker.
        
        Args:
            workspace_service (WorkspaceService): Required for first initialization
            db_service (DatabaseService): Required for first initialization
            
        Returns:
            RenderWorker: The singleton instance
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    if workspace_service is None or db_service is None:
                        raise ValueError("workspace_service and db_service are required for first initialization")
                    cls._instance = cls.__new__(cls)
                    cls._instance.__init_worker(workspace_service, db_service)
        return cls._instance
    
    def __init__(self, workspace_service: WorkspaceService, db_service: DatabaseService):
        """
        This method is deprecated. Use get_instance() instead.
        """
        raise RuntimeError("Use RenderWorker.get_instance() to get the RenderWorker instance")
    
    def __init_worker(self, workspace_service: WorkspaceService, db_service: DatabaseService):
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
        self.current_job = None

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
                self.current_job = job.id
                self.render(job)
                self.current_job = None
            except Empty:
                time.sleep(1)
                continue

from datetime import datetime, timezone

from blender_on_aws.models.db import Job
from blender_on_aws.services.blender_service import BlenderService
from blender_on_aws.services.db_service import DatabaseService
from blender_on_aws.services.workspace_service import WorkspaceService


class RenderWorker:
    """Worker thread to process render jobs from a queue."""
    
    def __init__(self, workspace_service: WorkspaceService, db_service: DatabaseService):
        """
        Initialize the render worker.
        
        Args:
            workspace_root (Path): Path to workspace root directory
        """
        super().__init__(daemon=True)

        self.blender_service = BlenderService(workspace_service.workspace_root)
        self.db_service = db_service
        self.workspace_service = workspace_service

    def render(self, job: Job):
        print(f"Starting {job.name}-{job.id}")
        self.db_service.update_job(job.id, status='active')

        job_dir = self.workspace_service.parse_job_directory(job)

        _, stdout, stderr = self.blender_service.render_blend_file(
            job_dir=job_dir,
            job=job,
        )
        (job_dir / 'stdout.log').write_text(stdout)
        (job_dir / 'stderr.log').write_text(stderr)

        self.db_service.update_job(
            job.id,
            status='complete',
            finished_at=datetime.now(timezone.utc),
        )
        print(f"Completed Job {job.name}-{job.id}")
        return ""

    def run(self):
        """Process jobs from the queue."""
        while True:
            queued_jobs = self.db_service.get_queued_jobs()
            print(f'Retrieved Queue jobs')
            for job in queued_jobs:
                print(f'- {job.id}: {job.name}')

            for job in queued_jobs:
                self.render(job)

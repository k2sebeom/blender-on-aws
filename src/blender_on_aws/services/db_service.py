import os
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import sessionmaker
from typing import Optional, List

from blender_on_aws.models.db import Base, Job


class DatabaseService:
    def __init__(self, db_path: str):
        """Initialize database service with the given database path.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.engine = None
        self.Session = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the database connection and create tables if they don't exist."""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_job(self, job_name: str, frame_range: str, mode: str, source_file: str) -> Job:
        """Create a new job in the database.
        
        Args:
            job_name (str): Name of the job
            frame_range (str): Frame range for rendering
            mode (str): Rendering mode
            source_file (str): Source file path

        Returns:
            Job: Created job instance
        """
        with self.Session() as session:
            job = Job(
                name=job_name,
                frame_range=frame_range,
                mode=mode,
                source_file=source_file,
                status='queued',
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job
 
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by its ID.
        
        Args:
            job_id (str): ID of the job to retrieve
            
        Returns:
            Optional[Job]: Job if found, None otherwise
        """
        with self.Session() as session:
            return session.query(Job).filter(Job.id == job_id).first()

    def get_all_jobs(self) -> List[Job]:
        """Retrieve all jobs from the database, sorted by creation time (newest first).
        
        Returns:
            List[Job]: List of all jobs ordered by created_at in descending order
        """
        with self.Session() as session:
            return session.query(Job).order_by(Job.created_at.desc()).all()
    
    def get_queued_jobs(self) -> List[Job]:
        """Retrieve all queued (unfinished) jobs from the database, sorted by creation time (newest first).

        Returns:
            List[Job]: List of jobs where finished_at is None, ordered by created_at in descending order
        """
        with self.Session() as session:
            return session.query(Job).filter(Job.status != 'complete').order_by(Job.created_at.desc()).all()

    def update_job(self, job_id: str, **kwargs) -> Optional[Job]:
        """Update a job's attributes.
        
        Args:
            job_id (str): ID of the job to update
            **kwargs: Attributes to update
            
        Returns:
            Optional[Job]: Updated job if found, None otherwise
        """
        with self.Session() as session:
            job = session.query(Job).filter(Job.id == job_id).first()
            if job:
                for key, value in kwargs.items():
                    setattr(job, key, value)
                session.commit()
            return job

    def delete_job(self, job_id: str) -> bool:
        """Delete a job from the database.
        
        Args:
            job_id (str): ID of the job to delete
            
        Returns:
            bool: True if job was deleted, False if not found
        """
        with self.Session() as session:
            job = session.query(Job).filter(Job.id == job_id).first()
            if job:
                session.delete(job)
                session.commit()
                return True
            return False

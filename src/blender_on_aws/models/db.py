from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import timezone

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    frame_range = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    source_file = Column(String, nullable=False)
    status = Column(String, default='complete', nullable=False)

    def __repr__(self):
        return f"<Job(job_id='{self.id}', job_name='{self.name}' created_at='{self.created_at} finished_at='{self.finished_at}' status={self.status})>"

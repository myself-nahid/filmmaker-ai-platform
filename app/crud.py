from sqlalchemy.orm import Session
from .models import models, schemas
from .models.models import TaskStatus

def get_task(db: Session, task_id: str):
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def create_task(db: Session, prompt: str):
    db_task = models.Task(prompt=prompt)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: str, status: TaskStatus, result_url: str = None):
    db_task = get_task(db, task_id)
    if db_task:
        db_task.status = status
        db_task.result_url = result_url
        db.commit()
        db.refresh(db_task)
    return db_task

def link_task_ids(db: Session, internal_task_id: str, external_task_id: str):
    db_task = get_task(db, internal_task_id)
    if db_task:
        db_task.external_id = external_task_id
        db.commit()
        db.refresh(db_task)
    return db_task

def get_task_by_external_id(db: Session, external_id: str):
    return db.query(models.Task).filter(models.Task.external_id == external_id).first()
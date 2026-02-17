from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime
import os
import json
import shutil

from .. import schemas, models, auth
from ..dependencies import get_db
from ..utils.file_handlers import save_upload_file
from ..utils.notifications import notify_new_assignment
from ..config import settings

router = APIRouter()

@router.get("/course/{course_id}", response_model=List[schemas.AssignmentResponse])
async def get_course_assignments(
    course_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get assignments for a course"""
    # Check course access
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if current_user.role == models.UserRole.STUDENT:
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.course_id == course_id,
            models.Enrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
    
    # Get assignments
    query = db.query(models.Assignment).filter(
        models.Assignment.course_id == course_id
    )
    
    # For students, only show published assignments
    if current_user.role == models.UserRole.STUDENT:
        query = query.filter(models.Assignment.published_at <= datetime.utcnow())
    
    assignments = query.order_by(models.Assignment.due_date).all()
    
    # Add submission stats for students
    result = []
    for assignment in assignments:
        assignment_dict = schemas.AssignmentResponse.model_validate(assignment)
        
        if current_user.role == models.UserRole.STUDENT:
            # Get student's submission for this assignment
            submission = db.query(models.Submission).filter(
                models.Submission.assignment_id == assignment.id,
                models.Submission.student_id == current_user.id
            ).first()
            
            if submission:
                assignment_dict.submission_status = submission.status
                if submission.grade:
                    assignment_dict.grade = submission.grade.score
        else:
            # For teachers, get submission counts
            assignment_dict.submissions_count = db.query(models.Submission).filter(
                models.Submission.assignment_id == assignment.id
            ).count()
            
            assignment_dict.graded_count = db.query(models.Grade).filter(
                models.Grade.assignment_id == assignment.id
            ).count()
        
        result.append(assignment_dict)
    
    return result

@router.post("/", response_model=schemas.AssignmentResponse)
async def create_assignment(
    title: str = Form(...),
    description: str = Form(None),
    type: str = Form(...),
    max_score: float = Form(...),
    weight: float = Form(1.0),
    due_date: datetime = Form(...),
    course_id: str = Form(...),
    rubric: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
    current_user: models.User = Depends(auth.require_role(models.UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Create a new assignment with attachments"""
    # Check course ownership
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.teacher_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create assignments in this course"
        )
    
    # Parse rubric if provided
    rubric_data = None
    if rubric:
        try:
            rubric_data = json.loads(rubric)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid rubric JSON"
            )
    
    # Save uploaded files
    attachment_paths = []
    for file in files:
        file_path = await save_upload_file(file, f"assignments/{course_id}")
        attachment_paths.append(file_path)
    
    # Create assignment
    db_assignment = models.Assignment(
        course_id=course_id,
        title=title,
        description=description,
        type=type,
        max_score=max_score,
        weight=weight,
        due_date=due_date,
        rubric=rubric_data,
        attachments=attachment_paths
    )
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    # Notify enrolled students
    await notify_new_assignment(db_assignment)
    
    return db_assignment

@router.put("/{assignment_id}/publish")
async def publish_assignment(
    assignment_id: str,
    current_user: models.User = Depends(auth.require_role(models.UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Publish an assignment"""
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check permission
    course = db.query(models.Course).filter(
        models.Course.id == assignment.course_id,
        models.Course.teacher_id == current_user.id
    ).first()
    
    if not course and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    assignment.published_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Assignment published successfully"}

@router.get("/{assignment_id}", response_model=schemas.AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get assignment details"""
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return assignment
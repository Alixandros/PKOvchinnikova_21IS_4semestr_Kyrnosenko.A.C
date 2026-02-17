from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import os
import magic

from .. import schemas, models, auth
from ..dependencies import get_db
from ..utils.file_handlers import save_upload_file, validate_file
from ..utils.notifications import notify_submission_received
from ..config import settings

router = APIRouter()

@router.post("/", response_model=schemas.SubmissionResponse)
async def submit_work(
    assignment_id: str = Form(...),
    comment: Optional[str] = Form(None),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: models.User = Depends(auth.require_role(models.UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """Submit a student work"""
    # Get assignment
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if student is enrolled in course
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == assignment.course_id,
        models.Enrollment.student_id == current_user.id,
        models.Enrollment.status == "active"
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )
    
    # Validate file
    is_valid, error_msg = await validate_file(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if assignment allows resubmission
    existing_submission = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment_id,
        models.Submission.student_id == current_user.id
    ).order_by(models.Submission.version.desc()).first()
    
    if existing_submission and not assignment.allow_resubmission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resubmission not allowed for this assignment"
        )
    
    if existing_submission and existing_submission.version >= assignment.max_resubmissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum resubmissions ({assignment.max_resubmissions}) reached"
        )
    
    # Save file
    file_path = await save_upload_file(
        file, 
        f"submissions/{assignment.course_id}/{assignment_id}/{current_user.id}"
    )
    
    # Check if submission is late
    is_late = datetime.utcnow() > assignment.due_date
    
    # Create submission
    version = 1
    if existing_submission:
        version = existing_submission.version + 1
    
    db_submission = models.Submission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        file_path=file_path,
        file_name=file.filename,
        file_size=file.size or 0,
        mime_type=magic.from_file(file_path, mime=True),
        comment=comment,
        is_late=is_late,
        version=version
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Send notification in background
    background_tasks.add_task(
        notify_submission_received,
        db_submission.id
    )
    
    return db_submission

@router.get("/assignment/{assignment_id}", response_model=List[schemas.SubmissionResponse])
async def get_assignment_submissions(
    assignment_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all submissions for an assignment"""
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check permissions
    if current_user.role == models.UserRole.STUDENT:
        # Students can only see their own submissions
        submissions = db.query(models.Submission).filter(
            models.Submission.assignment_id == assignment_id,
            models.Submission.student_id == current_user.id
        ).all()
    else:
        # Teachers and admins can see all
        course = db.query(models.Course).filter(
            models.Course.id == assignment.course_id
        ).first()
        
        if current_user.role != models.UserRole.ADMIN and course.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        submissions = db.query(models.Submission).filter(
            models.Submission.assignment_id == assignment_id
        ).all()
        
        # Add student names
        for sub in submissions:
            sub.student_name = sub.student.full_name
    
    return submissions

@router.get("/{submission_id}", response_model=schemas.SubmissionResponse)
async def get_submission(
    submission_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get submission details"""
    submission = db.query(models.Submission).filter(
        models.Submission.id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check permissions
    if current_user.role == models.UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this submission"
        )
    
    if current_user.role == models.UserRole.TEACHER:
        course = db.query(models.Course).filter(
            models.Course.id == submission.assignment.course_id
        ).first()
        if course.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this submission"
            )
    
    return submission
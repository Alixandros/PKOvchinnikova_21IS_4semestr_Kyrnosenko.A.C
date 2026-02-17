from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List
from datetime import datetime

from .. import schemas, models, auth
from ..dependencies import get_db
from ..utils.notifications import notify_grade_posted

router = APIRouter()

@router.post("/", response_model=schemas.GradeResponse)
async def create_grade(
    grade_data: schemas.GradeCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(auth.require_role(models.UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Create a grade for a submission"""
    # Get submission
    submission = db.query(models.Submission).filter(
        models.Submission.id == grade_data.submission_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check if already graded
    existing_grade = db.query(models.Grade).filter(
        models.Grade.submission_id == grade_data.submission_id
    ).first()
    
    if existing_grade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission already graded"
        )
    
    # Check permissions
    course = db.query(models.Course).filter(
        models.Course.id == submission.assignment.course_id
    ).first()
    
    if current_user.role != models.UserRole.ADMIN and course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to grade this submission"
        )
    
    # Create grade
    db_grade = models.Grade(
        submission_id=grade_data.submission_id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        grader_id=current_user.id,
        score=grade_data.score,
        max_score=grade_data.max_score,
        criteria_scores=grade_data.criteria_scores,
        comments=grade_data.comments
    )
    
    db.add(db_grade)
    
    # Update submission status
    submission.status = "graded"
    
    db.commit()
    db.refresh(db_grade)
    
    # Send notification in background
    background_tasks.add_task(
        notify_grade_posted,
        db_grade.id
    )
    
    return db_grade

@router.put("/{grade_id}", response_model=schemas.GradeResponse)
async def update_grade(
    grade_id: str,
    grade_data: schemas.GradeCreate,
    current_user: models.User = Depends(auth.require_role(models.UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Update an existing grade"""
    grade = db.query(models.Grade).filter(
        models.Grade.id == grade_id
    ).first()
    
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )
    
    # Only the original grader can update (or admin)
    if current_user.role != models.UserRole.ADMIN and grade.grader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the original grader can update this grade"
        )
    
    # Save old values for audit
    old_values = {
        "score": grade.score,
        "comments": grade.comments
    }
    
    # Update grade
    grade.score = grade_data.score
    grade.max_score = grade_data.max_score
    grade.criteria_scores = grade_data.criteria_scores
    grade.comments = grade_data.comments
    grade.last_modified = datetime.utcnow()
    
    db.commit()
    db.refresh(grade)
    
    # Create audit log
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="UPDATE_GRADE",
        entity_type="grade",
        entity_id=grade.id,
        old_values=old_values,
        new_values=grade_data.model_dump()
    )
    db.add(audit_log)
    db.commit()
    
    return grade

@router.get("/student/{student_id}/course/{course_id}", response_model=List[schemas.GradeResponse])
async def get_student_grades(
    student_id: str,
    course_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all grades for a student in a course"""
    # Check permissions
    if current_user.role == models.UserRole.STUDENT and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other students' grades"
        )
    
    grades = db.query(models.Grade).join(
        models.Assignment
    ).filter(
        models.Grade.student_id == student_id,
        models.Assignment.course_id == course_id
    ).all()
    
    return grades

@router.post("/{grade_id}/appeal")
async def create_appeal(
    grade_id: str,
    reason: str,
    current_user: models.User = Depends(auth.require_role(models.UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """Create an appeal for a grade"""
    grade = db.query(models.Grade).filter(
        models.Grade.id == grade_id
    ).first()
    
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )
    
    # Check if student owns the grade
    if grade.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot appeal another student's grade"
        )
    
    # Check if already appealed
    existing_appeal = db.query(models.Appeal).filter(
        models.Appeal.grade_id == grade_id,
        models.Appeal.status == "pending"
    ).first()
    
    if existing_appeal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An appeal for this grade is already pending"
        )
    
    appeal = models.Appeal(
        grade_id=grade_id,
        student_id=current_user.id,
        reason=reason
    )
    
    db.add(appeal)
    db.commit()
    
    return {"message": "Appeal created successfully", "appeal_id": appeal.id}
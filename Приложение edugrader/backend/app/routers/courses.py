from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List, Optional
import logging

from .. import schemas, models, auth
from ..dependencies import get_db, pagination_params
from ..utils.notifications import notify_course_update

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[schemas.CourseResponse])
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    semester: Optional[str] = None,
    include_archived: bool = False,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of courses based on user role"""
    query = db.query(models.Course)
    
    # Filter based on user role
    if current_user.role == models.UserRole.STUDENT:
        query = query.join(models.Enrollment).filter(
            models.Enrollment.student_id == current_user.id,
            models.Enrollment.status == "active"
        )
    elif current_user.role == models.UserRole.TEACHER:
        query = query.filter(models.Course.teacher_id == current_user.id)
    
    # Apply filters
    if not include_archived:
        query = query.filter(models.Course.is_archived == False)
    
    if search:
        query = query.filter(
            (models.Course.name_ru.ilike(f"%{search}%")) |
            (models.Course.code.ilike(f"%{search}%"))
        )
    
    if semester:
        query = query.filter(models.Course.semester == semester)
    
    # Add counts
    query = query.outerjoin(
        models.Enrollment,
        and_(models.Enrollment.course_id == models.Course.id, models.Enrollment.status == "active")
    ).outerjoin(
        models.Assignment,
        models.Assignment.course_id == models.Course.id
    ).group_by(models.Course.id).add_columns(
        func.count(models.Enrollment.id.distinct()).label("student_count"),
        func.count(models.Assignment.id.distinct()).label("assignment_count")
    )
    
    courses = query.offset(skip).limit(limit).all()
    
    result = []
    for course, student_count, assignment_count in courses:
        course_dict = schemas.CourseResponse.model_validate(course)
        course_dict.student_count = student_count
        course_dict.assignment_count = assignment_count
        course_dict.teacher_name = course.teacher.full_name if course.teacher else None
        result.append(course_dict)
    
    return result

@router.post("/", response_model=schemas.CourseResponse)
async def create_course(
    course_data: schemas.CourseCreate,
    current_user: models.User = Depends(auth.require_role(models.UserRole.TEACHER, models.UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    # Check if course code is unique
    existing = db.query(models.Course).filter(
        models.Course.code == course_data.code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code already exists"
        )
    
    db_course = models.Course(**course_data.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    # Create audit log
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="CREATE_COURSE",
        entity_type="course",
        entity_id=db_course.id,
        new_values=course_data.model_dump()
    )
    db.add(audit_log)
    db.commit()
    
    return db_course

@router.get("/{course_id}", response_model=schemas.CourseResponse)
async def get_course(
    course_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get course details by ID"""
    course = db.query(models.Course).filter(
        models.Course.id == course_id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check access
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
    
    # Get counts
    student_count = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.Enrollment.status == "active"
    ).count()
    
    assignment_count = db.query(models.Assignment).filter(
        models.Assignment.course_id == course_id
    ).count()
    
    course_dict = schemas.CourseResponse.model_validate(course)
    course_dict.student_count = student_count
    course_dict.assignment_count = assignment_count
    course_dict.teacher_name = course.teacher.full_name if course.teacher else None
    
    return course_dict

@router.put("/{course_id}", response_model=schemas.CourseResponse)
async def update_course(
    course_id: str,
    course_data: schemas.CourseCreate,
    current_user: models.User = Depends(auth.require_role(models.UserRole.TEACHER, models.UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update course details"""
    course = db.query(models.Course).filter(
        models.Course.id == course_id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permission (only teacher of course or admin)
    if current_user.role != models.UserRole.ADMIN and course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this course"
        )
    
    # Save old values for audit
    old_values = {
        "code": course.code,
        "name_ru": course.name_ru,
        "name_en": course.name_en
    }
    
    # Update course
    for key, value in course_data.model_dump().items():
        setattr(course, key, value)
    
    db.commit()
    db.refresh(course)
    
    # Create audit log
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="UPDATE_COURSE",
        entity_type="course",
        entity_id=course.id,
        old_values=old_values,
        new_values=course_data.model_dump()
    )
    db.add(audit_log)
    db.commit()
    
    # Notify enrolled students
    await notify_course_update(course, "updated")
    
    return course

@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    current_user: models.User = Depends(auth.require_role(models.UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Delete course (admin only)"""
    course = db.query(models.Course).filter(
        models.Course.id == course_id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course has assignments
    assignments_count = db.query(models.Assignment).filter(
        models.Assignment.course_id == course_id
    ).count()
    
    if assignments_count > 0:
        # Archive instead of delete
        course.is_archived = True
        db.commit()
        return {"message": "Course archived (has existing assignments)"}
    
    db.delete(course)
    db.commit()
    
    return {"message": "Course deleted successfully"}

@router.post("/{course_id}/enroll/{student_id}")
async def enroll_student(
    course_id: str,
    student_id: str,
    current_user: models.User = Depends(auth.require_role(models.UserRole.TEACHER, models.UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Enroll a student in course"""
    course = db.query(models.Course).filter(
        models.Course.id == course_id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    student = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.role == models.UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if already enrolled
    existing = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.Enrollment.student_id == student_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already enrolled"
        )
    
    # Check max students
    current_count = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.Enrollment.status == "active"
    ).count()
    
    if current_count >= course.max_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course has reached maximum number of students"
        )
    
    enrollment = models.Enrollment(
        course_id=course_id,
        student_id=student_id
    )
    db.add(enrollment)
    db.commit()
    
    return {"message": "Student enrolled successfully"}

@router.post("/{course_id}/enroll/batch")
async def batch_enroll(
    course_id: str,
    student_emails: List[str],
    current_user: models.User = Depends(auth.require_role(models.UserRole.TEACHER, models.UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Batch enroll students by email"""
    course = db.query(models.Course).filter(
        models.Course.id == course_id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    results = {
        "success": [],
        "failed": []
    }
    
    for email in student_emails:
        student = db.query(models.User).filter(
            models.User.email == email,
            models.User.role == models.UserRole.STUDENT
        ).first()
        
        if not student:
            results["failed"].append({"email": email, "reason": "Student not found"})
            continue
        
        # Check existing enrollment
        existing = db.query(models.Enrollment).filter(
            models.Enrollment.course_id == course_id,
            models.Enrollment.student_id == student.id
        ).first()
        
        if existing:
            results["failed"].append({"email": email, "reason": "Already enrolled"})
            continue
        
        enrollment = models.Enrollment(
            course_id=course_id,
            student_id=student.id
        )
        db.add(enrollment)
        results["success"].append(email)
    
    db.commit()
    
    return results
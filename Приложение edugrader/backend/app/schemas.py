from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

# ===== Базовые классы =====
class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    role: UserRole
    group: Optional[str] = None
    faculty: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# ===== НОВЫЕ КЛАССЫ для курсов =====
class CourseBase(BaseModel):
    code: str
    name_ru: str
    name_en: str
    description: Optional[str] = None
    credits: float
    max_students: int = 30
    semester: Optional[str] = None
    academic_year: Optional[str] = None

class CourseCreate(CourseBase):
    teacher_id: str
    department_id: Optional[str] = None

class CourseResponse(CourseBase):
    id: str
    teacher_id: str
    department_id: Optional[str]
    is_archived: bool
    created_at: datetime
    teacher_name: Optional[str] = None
    student_count: Optional[int] = 0
    assignment_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

# ===== НОВЫЕ КЛАССЫ для заданий =====
class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    max_score: float
    weight: float = 1.0
    due_date: datetime
    allow_resubmission: bool = False
    max_resubmissions: int = 1

class AssignmentCreate(AssignmentBase):
    course_id: str

class AssignmentResponse(AssignmentBase):
    id: str
    course_id: str
    created_at: datetime
    published_at: Optional[datetime] = None
    submissions_count: Optional[int] = 0
    graded_count: Optional[int] = 0
    submission_status: Optional[str] = None
    grade: Optional[float] = None
    
    class Config:
        from_attributes = True

# ===== НОВЫЕ КЛАССЫ для сдачи работ =====
class SubmissionBase(BaseModel):
    comment: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    assignment_id: str

class SubmissionResponse(SubmissionBase):
    id: str
    assignment_id: str
    student_id: str
    file_path: str
    file_name: str
    file_size: int
    status: str
    submitted_at: datetime
    is_late: bool
    version: int
    student_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# ===== НОВЫЕ КЛАССЫ для оценок =====
class GradeBase(BaseModel):
    score: float
    max_score: float
    criteria_scores: Optional[Dict[str, float]] = None
    comments: Optional[str] = None

class GradeCreate(GradeBase):
    submission_id: str

class GradeResponse(GradeBase):
    id: str
    submission_id: str
    assignment_id: str
    student_id: str
    grader_id: str
    graded_at: datetime
    last_modified: Optional[datetime] = None
    student_name: Optional[str] = None
    grader_name: Optional[str] = None
    assignment_title: Optional[str] = None
    
    class Config:
        from_attributes = True
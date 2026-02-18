from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    group: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# Course schemas
class CourseBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    academic_year: str
    semester: int

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    teacher_id: int
    is_active: bool
    created_at: datetime
    students: List[User] = []
    
    class Config:
        from_attributes = True

# Assignment schemas
class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    max_grade: float
    deadline: datetime
    allow_late_submissions: bool = False

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    id: int
    course_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Submission schemas
class SubmissionBase(BaseModel):
    file_path: str
    comment: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    pass

class GradeCreate(BaseModel):
    grade: float
    feedback: Optional[str] = None

class Submission(SubmissionBase):
    id: int
    assignment_id: int
    student_id: int
    status: str
    grade: Optional[float] = None
    feedback: Optional[str] = None
    graded_by: Optional[int] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
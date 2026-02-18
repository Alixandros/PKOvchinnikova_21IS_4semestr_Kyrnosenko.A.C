from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: str = "student"
    group: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    group: Optional[str]

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Course schemas
class CourseCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    academic_year: str
    semester: int

class CourseOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    teacher_id: int
    academic_year: str
    semester: int
    students_count: int = 0

# Assignment schemas
class Criteria(BaseModel):
    name: str
    max_score: float

class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    max_score: float = 100
    criteria: List[Criteria]
    deadline: datetime

class AssignmentOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    max_score: float
    criteria: List[Dict]
    deadline: datetime

# Grade schemas
class GradeCreate(BaseModel):
    submission_id: int
    scores: Dict[str, float]
    feedback: str

class GradeOut(BaseModel):
    id: int
    submission_id: int
    total_score: float
    feedback: str
    graded_at: datetime
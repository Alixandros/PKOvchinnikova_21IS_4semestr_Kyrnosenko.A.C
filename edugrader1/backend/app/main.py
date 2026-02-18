from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timedelta
import os
import shutil
from pathlib import Path
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict

# Security
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Database setup - SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./edugrader.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for courses and students
course_students = Table(
    'course_students',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id')),
    Column('student_id', Integer, ForeignKey('users.id'))
)

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default="student")  # admin, teacher, student
    group = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, unique=True)
    description = Column(Text)
    teacher_id = Column(Integer, ForeignKey('users.id'))
    academic_year = Column(String)
    semester = Column(Integer)
    
    teacher = relationship("User", foreign_keys=[teacher_id])
    students = relationship("User", secondary=course_students, backref="enrolled_courses")
    assignments = relationship("Assignment", back_populates="course")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('courses.id'))
    title = Column(String)
    description = Column(Text)
    max_score = Column(Float, default=100)
    criteria = Column(JSON)  # [{"name": "criteria1", "max": 30}, ...]
    deadline = Column(DateTime)
    
    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'))
    student_id = Column(Integer, ForeignKey('users.id'))
    file_path = Column(String)
    file_name = Column(String)
    comment = Column(Text)
    status = Column(String, default="submitted")  # submitted, graded
    submitted_at = Column(DateTime, default=datetime.now)
    
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id])

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey('submissions.id'))
    grader_id = Column(Integer, ForeignKey('users.id'))
    scores = Column(JSON)  # {"criteria1": 25, "criteria2": 15}
    total_score = Column(Float)
    feedback = Column(Text)
    graded_at = Column(DateTime, default=datetime.now)
    
    submission = relationship("Submission")
    grader = relationship("User", foreign_keys=[grader_id])

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic schemas
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

class Token(BaseModel):
    access_token: str
    token_type: str

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

class GradeCreate(BaseModel):
    submission_id: int
    scores: Dict[str, float]
    feedback: str

# App initialization
app = FastAPI(title="EduGrader")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Security functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Routes
@app.post("/api/auth/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        group=user.group
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/api/courses", response_model=list[CourseOut])
def get_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "teacher":
        courses = db.query(Course).filter(Course.teacher_id == current_user.id).all()
    elif current_user.role == "student":
        courses = current_user.enrolled_courses
    else:
        courses = db.query(Course).all()
    
    result = []
    for course in courses:
        course_dict = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description,
            "teacher_id": course.teacher_id,
            "academic_year": course.academic_year,
            "semester": course.semester,
            "students_count": len(course.students)
        }
        result.append(course_dict)
    return result

@app.post("/api/courses", response_model=CourseOut)
def create_course(course: CourseCreate, db: Session = Depends(get_db), 
                  current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_course = Course(
        name=course.name,
        code=course.code,
        description=course.description,
        teacher_id=current_user.id,
        academic_year=course.academic_year,
        semester=course.semester
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.post("/api/courses/{course_id}/enroll")
def enroll_course(course_id: int, db: Session = Depends(get_db), 
                  current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can enroll")
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user not in course.students:
        course.students.append(current_user)
        db.commit()
    
    return {"message": "Enrolled successfully"}

@app.get("/api/assignments/course/{course_id}", response_model=list[AssignmentOut])
def get_course_assignments(course_id: int, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).all()
    return assignments

@app.post("/api/assignments", response_model=AssignmentOut)
def create_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == assignment.course_id).first()
    if not course or course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_assignment = Assignment(
        course_id=assignment.course_id,
        title=assignment.title,
        description=assignment.description,
        max_score=assignment.max_score,
        criteria=[c.dict() for c in assignment.criteria],
        deadline=assignment.deadline
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@app.post("/api/submissions")
async def upload_submission(
    assignment_id: int = Form(...),
    comment: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can submit")
    
    # Save file
    file_path = UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create submission
    submission = Submission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        file_path=str(file_path),
        file_name=file.filename,
        comment=comment
    )
    db.add(submission)
    db.commit()
    
    return {"message": "File uploaded successfully", "id": submission.id}

@app.get("/api/submissions/assignment/{assignment_id}")
def get_submissions(assignment_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    query = db.query(Submission).filter(Submission.assignment_id == assignment_id)
    
    if current_user.role == "student":
        query = query.filter(Submission.student_id == current_user.id)
    
    submissions = query.all()
    result = []
    
    for sub in submissions:
        grade = db.query(Grade).filter(Grade.submission_id == sub.id).first()
        result.append({
            "id": sub.id,
            "student_name": sub.student.full_name,
            "file_name": sub.file_name,
            "submitted_at": sub.submitted_at,
            "status": sub.status,
            "grade": grade.total_score if grade else None,
            "feedback": grade.feedback if grade else None
        })
    
    return result

@app.post("/api/grades")
def create_grade(grade_data: GradeCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    submission = db.query(Submission).filter(Submission.id == grade_data.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    total_score = sum(grade_data.scores.values())
    
    grade = Grade(
        submission_id=grade_data.submission_id,
        grader_id=current_user.id,
        scores=grade_data.scores,
        total_score=total_score,
        feedback=grade_data.feedback
    )
    
    submission.status = "graded"
    
    db.add(grade)
    db.commit()
    
    return {"message": "Grade saved", "total_score": total_score}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
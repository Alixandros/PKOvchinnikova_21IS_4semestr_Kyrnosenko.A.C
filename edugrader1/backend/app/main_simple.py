from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import sqlite3
import os
import shutil
import json
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

# Database setup
DB_PATH = "edugrader.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            username TEXT UNIQUE,
            full_name TEXT,
            hashed_password TEXT,
            role TEXT DEFAULT 'student',
            group_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT UNIQUE,
            description TEXT,
            teacher_id INTEGER,
            academic_year TEXT,
            semester INTEGER,
            FOREIGN KEY (teacher_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_students (
            course_id INTEGER,
            student_id INTEGER,
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            PRIMARY KEY (course_id, student_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT,
            description TEXT,
            max_score FLOAT DEFAULT 100,
            criteria TEXT,
            deadline TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER,
            student_id INTEGER,
            file_path TEXT,
            file_name TEXT,
            comment TEXT,
            status TEXT DEFAULT 'submitted',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assignment_id) REFERENCES assignments (id),
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER,
            grader_id INTEGER,
            scores TEXT,
            total_score FLOAT,
            feedback TEXT,
            graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES submissions (id),
            FOREIGN KEY (grader_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

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

# Security functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return dict(user)

# Routes
@app.post("/api/auth/register", response_model=UserOut)
def register(user: UserCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                  (user.username, user.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Create user
    cursor.execute('''
        INSERT INTO users (email, username, full_name, hashed_password, role, group_name)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user.email, user.username, user.full_name, 
          get_password_hash(user.password), user.role, user.group))
    
    conn.commit()
    user_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    new_user = cursor.fetchone()
    conn.close()
    
    return dict(new_user)

@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user['username']})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=UserOut)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/api/courses", response_model=list[CourseOut])
def get_courses(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    if current_user['role'] == "teacher":
        cursor.execute("SELECT * FROM courses WHERE teacher_id = ?", (current_user['id'],))
    elif current_user['role'] == "student":
        cursor.execute('''
            SELECT c.* FROM courses c
            JOIN course_students cs ON c.id = cs.course_id
            WHERE cs.student_id = ?
        ''', (current_user['id'],))
    else:
        cursor.execute("SELECT * FROM courses")
    
    courses = cursor.fetchall()
    result = []
    
    for course in courses:
        # Get students count
        cursor.execute("SELECT COUNT(*) as count FROM course_students WHERE course_id = ?", 
                      (course['id'],))
        count = cursor.fetchone()['count']
        
        course_dict = dict(course)
        course_dict['students_count'] = count
        result.append(course_dict)
    
    conn.close()
    return result

@app.post("/api/courses", response_model=CourseOut)
def create_course(course: CourseCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO courses (name, code, description, teacher_id, academic_year, semester)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (course.name, course.code, course.description, 
          current_user['id'], course.academic_year, course.semester))
    
    conn.commit()
    course_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    new_course = cursor.fetchone()
    conn.close()
    
    result = dict(new_course)
    result['students_count'] = 0
    return result

@app.post("/api/courses/{course_id}/enroll")
def enroll_course(course_id: int, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="Only students can enroll")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if already enrolled
    cursor.execute('''
        SELECT * FROM course_students 
        WHERE course_id = ? AND student_id = ?
    ''', (course_id, current_user['id']))
    
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO course_students (course_id, student_id)
            VALUES (?, ?)
        ''', (course_id, current_user['id']))
        conn.commit()
    
    conn.close()
    return {"message": "Enrolled successfully"}

@app.get("/api/assignments/course/{course_id}", response_model=list[AssignmentOut])
def get_course_assignments(course_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assignments WHERE course_id = ?", (course_id,))
    assignments = cursor.fetchall()
    
    result = []
    for assignment in assignments:
        assignment_dict = dict(assignment)
        assignment_dict['criteria'] = json.loads(assignment_dict['criteria']) if assignment_dict['criteria'] else []
        result.append(assignment_dict)
    
    conn.close()
    return result

@app.post("/api/assignments", response_model=AssignmentOut)
def create_assignment(assignment: AssignmentCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check course ownership
    cursor.execute("SELECT * FROM courses WHERE id = ? AND teacher_id = ?", 
                  (assignment.course_id, current_user['id']))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized")
    
    cursor.execute('''
        INSERT INTO assignments (course_id, title, description, max_score, criteria, deadline)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (assignment.course_id, assignment.title, assignment.description,
          assignment.max_score, json.dumps([c.dict() for c in assignment.criteria]), 
          assignment.deadline))
    
    conn.commit()
    assignment_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
    new_assignment = cursor.fetchone()
    conn.close()
    
    result = dict(new_assignment)
    result['criteria'] = json.loads(result['criteria'])
    return result

@app.post("/api/submissions")
async def upload_submission(
    assignment_id: int = Form(...),
    comment: str = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="Only students can submit")
    
    # Save file
    file_path = UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO submissions (assignment_id, student_id, file_path, file_name, comment)
        VALUES (?, ?, ?, ?, ?)
    ''', (assignment_id, current_user['id'], str(file_path), file.filename, comment))
    
    conn.commit()
    submission_id = cursor.lastrowid
    conn.close()
    
    return {"message": "File uploaded successfully", "id": submission_id}

@app.get("/api/submissions/assignment/{assignment_id}")
def get_submissions(assignment_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT s.*, u.full_name as student_name FROM submissions s JOIN users u ON s.student_id = u.id WHERE s.assignment_id = ?"
    params = [assignment_id]
    
    if current_user['role'] == "student":
        query += " AND s.student_id = ?"
        params.append(current_user['id'])
    
    cursor.execute(query, params)
    submissions = cursor.fetchall()
    
    result = []
    for sub in submissions:
        sub_dict = dict(sub)
        cursor.execute("SELECT * FROM grades WHERE submission_id = ?", (sub['id'],))
        grade = cursor.fetchone()
        if grade:
            sub_dict['grade'] = grade['total_score']
            sub_dict['feedback'] = grade['feedback']
        conn.close()
    
    conn.close()
    return result

@app.post("/api/grades")
def create_grade(grade_data: GradeCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    conn = get_db()
    cursor = conn.cursor()
    
    total_score = sum(grade_data.scores.values())
    
    cursor.execute('''
        INSERT INTO grades (submission_id, grader_id, scores, total_score, feedback)
        VALUES (?, ?, ?, ?, ?)
    ''', (grade_data.submission_id, current_user['id'], 
          json.dumps(grade_data.scores), total_score, grade_data.feedback))
    
    cursor.execute("UPDATE submissions SET status = 'graded' WHERE id = ?", 
                  (grade_data.submission_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Grade saved", "total_score": total_score}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
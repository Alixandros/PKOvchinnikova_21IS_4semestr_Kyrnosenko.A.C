from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON, Enum, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    group = Column(String, nullable=True)
    faculty = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    courses_teaching = relationship("Course", back_populates="teacher")
    enrollments = relationship("Enrollment", back_populates="student")
    submissions = relationship("Submission", back_populates="student")
    grades_given = relationship("Grade", foreign_keys="Grade.grader_id", back_populates="grader")
    audit_logs = relationship("AuditLog", back_populates="user")

class Faculty(Base):
    __tablename__ = "faculties"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)
    
    # Relationships
    departments = relationship("Department", back_populates="faculty")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    faculty_id = Column(String, ForeignKey("faculties.id"))
    
    # Relationships
    faculty = relationship("Faculty", back_populates="departments")
    courses = relationship("Course", back_populates="department")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False)
    name_ru = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    description = Column(Text)
    credits = Column(Float, nullable=False)
    teacher_id = Column(String, ForeignKey("users.id"), nullable=False)
    department_id = Column(String, ForeignKey("departments.id"))
    max_students = Column(Integer, default=30)
    semester = Column(String)
    academic_year = Column(String)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    teacher = relationship("User", back_populates="courses_teaching")
    department = relationship("Department", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="active")  # active, completed, dropped
    
    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False)  # test, essay, project, lab
    max_score = Column(Float, nullable=False)
    weight = Column(Float, default=1.0)
    due_date = Column(DateTime(timezone=True), nullable=False)
    review_deadline = Column(DateTime(timezone=True))
    allow_resubmission = Column(Boolean, default=False)
    max_resubmissions = Column(Integer, default=1)
    rubric = Column(JSON)  # JSON with criteria
    attachments = Column(JSON)  # JSON array of file paths
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")
    grades = relationship("Grade", back_populates="assignment")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    assignment_id = Column(String, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String)
    comment = Column(Text)
    status = Column(String, default="submitted")  # submitted, late, graded, returned
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    is_late = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    grade = relationship("Grade", uselist=False, back_populates="submission")

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    submission_id = Column(String, ForeignKey("submissions.id"), unique=True)
    assignment_id = Column(String, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    grader_id = Column(String, ForeignKey("users.id"), nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    criteria_scores = Column(JSON)  # JSON with scores per criterion
    comments = Column(Text)
    feedback_files = Column(JSON)  # JSON array of file paths
    graded_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    submission = relationship("Submission", back_populates="grade")
    assignment = relationship("Assignment", back_populates="grades")
    student = relationship("User", foreign_keys=[student_id])
    grader = relationship("User", foreign_keys=[grader_id], back_populates="grades_given")
    appeals = relationship("Appeal", back_populates="grade")

class Appeal(Base):
    __tablename__ = "appeals"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    grade_id = Column(String, ForeignKey("grades.id"), nullable=False)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    supporting_files = Column(JSON)
    status = Column(String, default="pending")  # pending, approved, rejected
    response = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    grade = relationship("Grade", back_populates="appeals")
    student = relationship("User", foreign_keys=[student_id])

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # grade, deadline, appeal, system
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
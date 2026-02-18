from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./edugrader.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for courses and students
course_students = Table(
    'course_students',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id')),
    Column('student_id', Integer, ForeignKey('users.id'))
)

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
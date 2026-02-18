from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="EduGrader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище данных в памяти (временное решение)
users_db = []
courses_db = []
submissions_db = []

@app.get("/")
def root():
    return {"message": "EduGrader API is running!"}

@app.get("/test")
def test():
    return {"status": "ok", "time": datetime.now().isoformat()}

# Аутентификация
@app.post("/api/register")
def register(email: str, password: str, full_name: str, role: str, group: str = None):
    # Проверка на существующего пользователя
    for user in users_db:
        if user["email"] == email:
            return {"error": "Email already registered"}
    
    user = {
        "id": len(users_db) + 1,
        "email": email,
        "password": password,  # В реальном проекте нужно хешировать!
        "full_name": full_name,
        "role": role,
        "group": group,
        "created_at": datetime.now().isoformat()
    }
    users_db.append(user)
    return {"message": "User created", "user": user}

@app.post("/api/token")
def login(email: str, password: str):
    for user in users_db:
        if user["email"] == email and user["password"] == password:
            return {
                "access_token": f"fake-token-{user['id']}",
                "token_type": "bearer"
            }
    return {"error": "Invalid credentials"}

# Курсы
@app.get("/api/courses")
def get_courses():
    return courses_db

@app.post("/api/courses")
def create_course(name: str, code: str, academic_year: str, semester: int):
    course = {
        "id": len(courses_db) + 1,
        "name": name,
        "code": code,
        "academic_year": academic_year,
        "semester": semester,
        "teacher_id": 1,  # Заглушка
        "created_at": datetime.now().isoformat()
    }
    courses_db.append(course)
    return course

# Задания
@app.get("/api/courses/{course_id}/assignments")
def get_assignments(course_id: int):
    return []  # Заглушка

@app.post("/api/courses/{course_id}/assignments")
def create_assignment(course_id: int, title: str, max_grade: float, deadline: str):
    return {
        "id": 1,
        "title": title,
        "max_grade": max_grade,
        "deadline": deadline,
        "course_id": course_id
    }

# Оценки
@app.get("/api/my-grades")
def get_my_grades():
    return []  # Заглушка

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
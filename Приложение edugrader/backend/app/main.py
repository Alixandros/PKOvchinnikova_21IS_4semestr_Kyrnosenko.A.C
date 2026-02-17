from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime

from .routers import (
    auth, users, courses, assignments, 
    submissions, grades, analytics
)
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="EduGrader API",
    description="API for educational grading system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# В main.py измените теги:
app.include_router(auth.router, prefix="/api/v1/auth", tags=["🔐 Аутентификация"])
app.include_router(users.router, prefix="/api/v1/users", tags=["👥 Пользователи"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["📚 Курсы"])
app.include_router(assignments.router, prefix="/api/v1/assignments", tags=["📝 Задания"])
app.include_router(submissions.router, prefix="/api/v1/submissions", tags=["📤 Сдача работ"])
app.include_router(grades.router, prefix="/api/v1/grades", tags=["📊 Оценки"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["📈 Аналитика"])

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return {"message": "Welcome to EduGrader API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
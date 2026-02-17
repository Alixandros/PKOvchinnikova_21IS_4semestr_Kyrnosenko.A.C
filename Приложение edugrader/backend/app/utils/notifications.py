import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Временная заглушка для отправки email
async def send_verification_email(email: str, user_id: str):
    """
    Отправка письма для подтверждения email
    Временная заглушка, которая просто логирует действие
    """
    logger.info(f"📧 Отправка письма для подтверждения на {email} для пользователя {user_id}")
    logger.info(f"🔗 Ссылка для подтверждения: http://localhost:8000/api/v1/auth/verify-email/{user_id}")
    # В реальном проекте здесь будет отправка через SMTP
    return True

async def notify_course_update(course, action: str):
    """Уведомление об обновлении курса"""
    logger.info(f"📢 Курс {course.name_ru} {action}")

async def notify_new_assignment(assignment):
    """Уведомление о новом задании"""
    logger.info(f"📢 Новое задание: {assignment.title}")

async def notify_submission_received(submission_id: str):
    """Уведомление о получении работы"""
    logger.info(f"📢 Работа {submission_id} получена")

async def notify_grade_posted(grade_id: str):
    """Уведомление о выставлении оценки"""
    logger.info(f"📢 Оценка {grade_id} выставлена")
import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
from datetime import datetime
import aiofiles
from ..config import settings

# Попытка импорта magic с обработкой ошибки
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("⚠️  python-magic не установлен. Функции определения MIME-типов будут ограничены.")

async def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file"""
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        return False, f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
    
    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = {".pdf", ".doc", ".docx", ".zip", ".rar", ".jpg", ".jpeg", ".png", ".py", ".java", ".txt"}
    
    if ext not in allowed_extensions:
        return False, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
    
    return True, ""

async def save_upload_file(upload_file: UploadFile, subdirectory: str = "") -> str:
    """Save uploaded file to disk"""
    # Create directory structure
    date_str = datetime.utcnow().strftime("%Y/%m/%d")
    upload_dir = os.path.join(settings.UPLOAD_DIR, subdirectory, date_str)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    original_name = Path(upload_file.filename).stem
    ext = Path(upload_file.filename).suffix
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{original_name}_{timestamp}{ext}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)
    
    return file_path

def delete_file(file_path: str):
    """Delete file from disk"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

def get_file_info(file_path: str) -> dict:
    """Get file information"""
    stat = os.stat(file_path)
    file_info = {
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime),
        "modified": datetime.fromtimestamp(stat.st_mtime),
    }
    
    # Add MIME type if magic is available
    if MAGIC_AVAILABLE:
        try:
            file_info["mime_type"] = magic.from_file(file_path, mime=True)
        except:
            file_info["mime_type"] = "unknown"
    
    return file_info
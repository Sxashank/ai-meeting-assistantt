from pathlib import Path
import aiofiles
import os
import logging
from fastapi import UploadFile
import shutil
import time

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.max_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
        logger.info(f"FileHandler initialized. Upload dir: {self.upload_dir.absolute()}")
    
    async def save_upload(self, file: UploadFile, meeting_id: str) -> str:
        try:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                raise ValueError(f"File type not allowed: {file_ext}")
            
            meeting_dir = self.upload_dir / meeting_id
            meeting_dir.mkdir(exist_ok=True)
            safe_filename = f"{meeting_id}{file_ext}"
            file_path = meeting_dir / safe_filename
            logger.info(f"Saving upload to: {file_path}")
            
            async with aiofiles.open(file_path, 'wb') as f:
                chunk_size = 1024 * 1024  # 1MB chunks
                total_size = 0
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > self.max_size:
                        os.remove(file_path)
                        raise ValueError(f"File too large. Max size: {self.max_size / (1024*1024)}MB")
                    await f.write(chunk)
            
            logger.info(f"File saved successfully. Size: {total_size / (1024*1024):.2f}MB")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise
    
    def cleanup_file(self, file_path: str):
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                parent = path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
                logger.info(f"Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        logger.info(f"Cleaning up files older than {max_age_hours} hours")
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for meeting_dir in self.upload_dir.iterdir():
            if not meeting_dir.is_dir():
                continue
            dir_age = current_time - meeting_dir.stat().st_mtime
            if dir_age > max_age_seconds:
                shutil.rmtree(meeting_dir)
                deleted_count += 1
                logger.info(f"Deleted old directory: {meeting_dir.name}")
        
        logger.info(f"Cleanup complete. Deleted {deleted_count} directories")
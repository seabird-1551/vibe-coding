import os
import pandas as pd
import uuid
from typing import Tuple, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file uploads and processing for CSV and Excel files"""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Supported file extensions
        self.supported_extensions = {'.csv', '.xlsx', '.xls'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB default
    
    def validate_file(self, file_path: str, file_size: int) -> Tuple[bool, str]:
        """Validate uploaded file"""
        try:
            # Check file size
            if file_size > self.max_file_size:
                return False, f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)"
            
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_extensions:
                return False, f"Unsupported file type: {file_ext}. Supported types: {', '.join(self.supported_extensions)}"
            
            return True, "File validation successful"
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False, f"File validation failed: {str(e)}"
    
    def save_uploaded_file(self, file_content: bytes, original_filename: str) -> Tuple[str, str]:
        """Save uploaded file and return file path and unique ID"""
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            file_ext = Path(original_filename).suffix.lower()
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{file_id}_{timestamp}{file_ext}"
            file_path = self.upload_dir / safe_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"File saved successfully: {file_path}")
            return str(file_path), file_id
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise Exception(f"Failed to save file: {str(e)}")
    
    def load_dataframe(self, file_path: str) -> pd.DataFrame:
        """Load data from file into pandas DataFrame"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                # Try different encodings for CSV files
                encodings = ['utf-8', 'latin-1', 'cp1252']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.info(f"Successfully loaded CSV with encoding: {encoding}")
                        return df
                    except UnicodeDecodeError:
                        continue
                raise Exception("Could not decode CSV file with any supported encoding")
            
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                logger.info(f"Successfully loaded Excel file: {file_path}")
                return df
            
            else:
                raise Exception(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            logger.error(f"Error loading dataframe: {str(e)}")
            raise Exception(f"Failed to load data from file: {str(e)}")
    
    def get_file_info(self, file_path: str) -> dict:
        """Get basic file information"""
        try:
            file_stat = os.stat(file_path)
            return {
                'file_size': file_stat.st_size,
                'created_time': datetime.fromtimestamp(file_stat.st_ctime),
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime)
            }
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {}
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old uploaded files"""
        try:
            current_time = datetime.now()
            for file_path in self.upload_dir.glob("*"):
                if file_path.is_file():
                    file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age.total_seconds() > max_age_hours * 3600:
                        file_path.unlink()
                        logger.info(f"Cleaned up old file: {file_path}")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a specific file"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False 

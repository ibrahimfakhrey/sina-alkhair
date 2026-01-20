import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Database - use absolute path for PythonAnywhere compatibility
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "charity.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # File Upload - use absolute path
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB for images
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

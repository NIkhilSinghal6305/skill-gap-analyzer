"""
Configuration for the Skill Gap Analyzer application.
Update MYSQL_PASSWORD with your actual MySQL root password before running.
"""
import os


class Config:
    # Flask secret key for session management and flash messages
    SECRET_KEY = os.environ.get('SECRET_KEY', 'skill-gap-analyzer-secret-key-2024')

    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')  # <-- Change this to your MySQL password
    MYSQL_DATABASE = 'skill_gap_analyzer'
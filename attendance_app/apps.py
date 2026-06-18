"""
Attendance App Configuration
"""
from django.apps import AppConfig


class AttendanceAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance_app'
    verbose_name = 'Smart Attendance System'

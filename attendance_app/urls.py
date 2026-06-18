"""

Smart Attendance System - URL Configuration

"""

from django.urls import path

from . import views

from . import salary_views

from . import incentive_views

from . import task_views
from . import push_views



urlpatterns = [

    # Home & Authentication

    path('', views.home, name='home'),

    path('admin/login/', views.admin_login, name='admin_login'),

    path('employee/login/', views.employee_login, name='employee_login'),

    path('logout/', views.user_logout, name='logout'),

    

    # Admin URLs

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    

    # Employee Management

    path('admin/employees/', views.employee_list, name='employee_list'),

    path('admin/employees/add/', views.employee_add, name='employee_add'),

    path('admin/employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),

    path('admin/employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    path('admin/employees/<int:pk>/profile/', views.employee_profile, name='employee_profile'),

    path('admin/employee/<int:pk>/toggle-status/', views.employee_toggle_status, name='employee_toggle_status'),

    

    # Attendance Management

    path('admin/attendance/', views.attendance_list, name='attendance_list'),

    path('admin/attendance/export/', views.attendance_export, name='attendance_export'),

    

    # Leave Management

    path('admin/leaves/', views.leave_requests, name='leave_requests'),

    path('admin/leaves/<int:pk>/review/', views.leave_review, name='leave_review'),

    

    # Old Salary Management (Keep for backward compatibility)

    path('admin/salary/', views.salary_report, name='salary_report'),

    path('admin/salary/export/', views.salary_export, name='salary_export'),

    

    # New Salary Management with Payment Tracking

    path('admin/salary-cycle-settings/', salary_views.salary_cycle_settings, name='salary_cycle_settings'),

    path('admin/salary-management/', salary_views.salary_management, name='salary_management'),

    path('admin/salary-management/generate/', salary_views.generate_salary_for_cycle, name='generate_salary_for_cycle'),

    path('admin/salary/<int:salary_id>/detail/', salary_views.salary_detail, name='salary_detail'),

    path('admin/salary/<int:salary_id>/add-payment/', salary_views.add_payment, name='add_payment'),

    path('admin/salary/payment/<int:payment_id>/delete/', salary_views.delete_payment, name='delete_payment'),



    # Monthly Calendar Report

    path('admin/monthly-report/', views.monthly_attendance_report, name='monthly_attendance_report'),

    path('admin/monthly-report/pdf/', views.export_monthly_report_pdf, name='export_monthly_report_pdf'),



    # Office Location

    path('admin/office-location/', views.office_location_settings, name='office_location_settings'),

    

    # Week Off Management

    path('admin/week-off/', views.week_off_settings, name='week_off_settings'),

    

    # Holiday Management

    path('admin/holidays/', views.holiday_list, name='holiday_list'),

    path('admin/holidays/create/', views.holiday_create, name='holiday_create'),

    path('admin/holidays/<int:pk>/edit/', views.holiday_edit, name='holiday_edit'),

    path('admin/holidays/<int:pk>/delete/', views.holiday_delete, name='holiday_delete'),

    

    # Shift Management

    path('admin/shifts/', views.shift_list, name='shift_list'),

    path('admin/shifts/create/', views.shift_create, name='shift_create'),

    path('admin/shifts/<int:pk>/edit/', views.shift_edit, name='shift_edit'),

    path('admin/shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),

    path('admin/employees/<int:pk>/assign-shift/', views.employee_shift_assign, name='employee_shift_assign'),

    

    # Incentive Management

    path('admin/incentives/', incentive_views.incentive_list, name='incentive_list'),

    path('admin/incentives/add/', incentive_views.incentive_add, name='incentive_add'),

    path('admin/incentives/<int:pk>/edit/', incentive_views.incentive_edit, name='incentive_edit'),

    path('admin/incentives/<int:pk>/delete/', incentive_views.incentive_delete, name='incentive_delete'),

    path('admin/employees/<int:employee_id>/incentives/', incentive_views.employee_incentives, name='employee_incentives'),



    # Employee URLs

    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),

    path('employee/punch/', views.punch_in_out, name='punch_in_out'),

    path('employee/process-punch/', views.process_punch, name='process_punch'),

    path('employee/leaves/', views.employee_leaves, name='employee_leaves'),

    path('employee/attendance/', views.employee_attendance_history, name='employee_attendance_history'),

    # Task Management - Admin
    path('admin/tasks/', task_views.admin_task_list, name='admin_task_list'),
    path('admin/tasks/create/', task_views.admin_task_create, name='admin_task_create'),
    path('admin/tasks/<int:pk>/edit/', task_views.admin_task_edit, name='admin_task_edit'),
    path('admin/tasks/<int:pk>/delete/', task_views.admin_task_delete, name='admin_task_delete'),
    path('admin/tasks/<int:pk>/detail/', task_views.admin_task_detail, name='admin_task_detail'),
    path('admin/work-logs/', task_views.admin_work_logs, name='admin_work_logs'),

    # Task Management - Employee
    path('employee/tasks/', task_views.employee_task_list, name='employee_task_list'),
    path('employee/tasks/<int:pk>/', task_views.employee_task_detail, name='employee_task_detail'),
    path('employee/tasks/<int:pk>/status/', task_views.employee_task_status_update, name='employee_task_status_update'),
    path('employee/tasks/unseen-count/', task_views.get_unseen_task_count, name='get_unseen_task_count'),
    # Web Push Notifications
    path('push/vapid-public-key/', push_views.get_vapid_public_key, name='vapid_public_key'),
    path('push/save-subscription/', push_views.save_subscription, name='save_push_subscription'),
    path('push/delete-subscription/', push_views.delete_subscription, name='delete_push_subscription'),
    # In-App Notifications
    path('notifications/count/', push_views.get_notification_count, name='notification_count'),
    path('notifications/', push_views.get_notifications, name='get_notifications'),
    path('notifications/read-all/', push_views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/<int:notif_id>/read/', push_views.mark_one_read, name='mark_one_notification_read'),
]


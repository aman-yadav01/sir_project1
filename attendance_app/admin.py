"""

Django Admin Configuration

"""

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Employee, Attendance, Leave, OfficeLocation, Salary, SalaryPayment, SalaryCycleSettings, Incentive, Task, WorkLog





@admin.register(User)

class UserAdmin(BaseUserAdmin):

    list_display = ['username', 'email', 'role', 'employee_id', 'is_active']

    list_filter = ['role', 'is_active']

    search_fields = ['username', 'email', 'employee_id']

    

    fieldsets = BaseUserAdmin.fieldsets + (

        ('Additional Info', {'fields': ('role', 'employee_id', 'mobile_number')}),

    )





@admin.register(Employee)

class EmployeeAdmin(admin.ModelAdmin):

    list_display = ['employee_id', 'full_name', 'designation', 'email', 'base_salary', 'is_active']

    list_filter = ['is_active', 'designation']

    search_fields = ['employee_id', 'full_name', 'email']

    readonly_fields = ['date_joined']





@admin.register(Attendance)

class AttendanceAdmin(admin.ModelAdmin):

    list_display = ['employee', 'date', 'punch_in', 'punch_out', 'status', 'is_late']

    list_filter = ['status', 'is_late', 'date']

    search_fields = ['employee__full_name', 'employee__employee_id']

    date_hierarchy = 'date'





@admin.register(Leave)

class LeaveAdmin(admin.ModelAdmin):

    list_display = ['employee', 'start_date', 'end_date', 'status', 'applied_on']

    list_filter = ['status', 'start_date']

    search_fields = ['employee__full_name', 'employee__employee_id']

    date_hierarchy = 'applied_on'





@admin.register(OfficeLocation)

class OfficeLocationAdmin(admin.ModelAdmin):

    list_display = ['name', 'latitude', 'longitude', 'radius', 'is_active']

    list_filter = ['is_active']





@admin.register(Salary)

class SalaryAdmin(admin.ModelAdmin):

    list_display = ['employee', 'cycle_start_date', 'cycle_end_date', 'final_salary', 'total_paid', 'pending_amount', 'payment_status']

    list_filter = ['payment_status', 'cycle_start_date']

    search_fields = ['employee__full_name', 'employee__employee_id']





@admin.register(SalaryPayment)

class SalaryPaymentAdmin(admin.ModelAdmin):

    list_display = ['salary', 'amount', 'payment_date', 'payment_method', 'reference_number', 'paid_by']

    list_filter = ['payment_method', 'payment_date']

    search_fields = ['salary__employee__full_name', 'reference_number']





@admin.register(SalaryCycleSettings)

class SalaryCycleSettingsAdmin(admin.ModelAdmin):

    list_display = ['cycle_name', 'cycle_start_day', 'is_active', 'updated_at']

    list_filter = ['is_active']





@admin.register(Incentive)

class IncentiveAdmin(admin.ModelAdmin):

    list_display = ['employee', 'title', 'incentive_type', 'amount', 'incentive_date', 'added_by']

    list_filter = ['incentive_type', 'incentive_date']

    search_fields = ['employee__full_name', 'employee__employee_id', 'title']

    date_hierarchy = 'incentive_date'



@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'assigned_by', 'priority', 'status', 'deadline', 'created_at']
    list_filter = ['status', 'priority', 'deadline']
    search_fields = ['title', 'assigned_to__full_name', 'assigned_to__employee_id']
    date_hierarchy = 'created_at'


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'task', 'log_date', 'hours_worked', 'is_seen_by_admin', 'created_at']
    list_filter = ['log_date', 'is_seen_by_admin']
    search_fields = ['employee__full_name', 'task__title']
    date_hierarchy = 'log_date'

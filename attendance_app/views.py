"""

Smart Attendance System - Views

Complete views for Admin and Employee

"""

from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.decorators import login_required

from django.contrib import messages

from django.http import JsonResponse, HttpResponse

from django.db.models import Q, Count

from django.utils import timezone

from datetime import datetime, date, timedelta

import json

import csv

import face_recognition

import numpy as np

import cv2

import base64

from decimal import Decimal



from .models import User, Employee, Attendance, Leave, OfficeLocation, Salary, Shift, WeekOff, Holiday

from .forms import (

    AdminLoginForm, EmployeeLoginForm, EmployeeRegistrationForm,

    EmployeeUpdateForm, EmployeePhotoUpdateForm, LeaveRequestForm,

    LeaveReviewForm, OfficeLocationForm,

    AttendanceFilterForm, DateRangeForm, ShiftForm, EmployeeShiftAssignForm,

    HolidayForm

)





# ==================== AUTHENTICATION VIEWS ====================



def admin_login(request):

    """Admin Login View"""

    if request.user.is_authenticated and request.user.role == 'admin':

        return redirect('admin_dashboard')



    if request.method == 'POST':

        form = AdminLoginForm(request, data=request.POST)

        if form.is_valid():

            user = form.get_user()

            if user.role == 'admin':

                login(request, user)

                messages.success(request, 'Welcome Admin!')

                return redirect('admin_dashboard')

            else:

                messages.error(request, 'Access denied. Admin only.')

    else:

        form = AdminLoginForm()



    return render(request, 'admin/login.html', {'form': form})





def employee_login(request):

    """Employee Login View"""

    if request.user.is_authenticated and request.user.role == 'employee':

        return redirect('employee_dashboard')



    if request.method == 'POST':

        form = EmployeeLoginForm(request.POST)

        if form.is_valid():

            employee_id = form.cleaned_data['employee_id']

            password = form.cleaned_data['password']



            try:

                user = User.objects.get(employee_id=employee_id, role='employee')

                

                # Check if employee is active

                if hasattr(user, 'employee_profile') and not user.employee_profile.is_active:

                    messages.error(request, 'Your account has been deactivated. Please contact admin.')

                    return render(request, 'employee/login.html', {'form': form})

                

                user = authenticate(username=user.username, password=password)



                if user:

                    login(request, user)

                    messages.success(request, f'Welcome {user.employee_profile.full_name}!')

                    return redirect('employee_dashboard')

                else:

                    messages.error(request, 'Invalid credentials')

            except User.DoesNotExist:

                messages.error(request, 'Employee ID not found')

    else:

        form = EmployeeLoginForm()



    return render(request, 'employee/login.html', {'form': form})





def user_logout(request):

    """Logout View"""

    logout(request)

    messages.success(request, 'Logged out successfully')

    return redirect('home')





def auto_punch_out_expired_shifts():

    """

    Utility function to automatically punch out employees

    whose shift has ended but haven't punched out

    """

    from django.utils import timezone

    

    today = date.today()

    current_time = timezone.now().time()

    

    # Get all attendance records for today with punch_in but no punch_out

    pending_attendances = Attendance.objects.filter(

        date=today,

        punch_in__isnull=False,

        punch_out__isnull=True

    ).select_related('employee', 'employee__shift')

    

    auto_punched_count = 0

    

    for attendance in pending_attendances:

        employee = attendance.employee

        

        # Check if employee has a shift assigned

        if employee.shift:

            shift_end_time = employee.shift.punch_out_time

            

            # Check if current time has passed shift end time

            # Handle night shift (crosses midnight)

            if shift_end_time < employee.shift.punch_in_start:

                # Night shift - check if we're past midnight and past end time

                if current_time >= shift_end_time:

                    # Auto punch out

                    punch_out_datetime = datetime.combine(today, shift_end_time)

                    attendance.punch_out = timezone.make_aware(punch_out_datetime)

                    attendance.punch_out_location = attendance.punch_in_location

                    attendance.notes = "Auto punch out - Shift ended"

                    attendance.save()

                    auto_punched_count += 1

            else:

                # Day shift - simple comparison

                if current_time >= shift_end_time:

                    # Auto punch out

                    punch_out_datetime = datetime.combine(today, shift_end_time)

                    attendance.punch_out = timezone.make_aware(punch_out_datetime)

                    attendance.punch_out_location = attendance.punch_in_location

                    attendance.notes = "Auto punch out - Shift ended"

                    attendance.save()

                    auto_punched_count += 1

    

    return auto_punched_count





def home(request):

    """Home Page"""

    return render(request, 'home.html')





# ==================== ADMIN DASHBOARD ====================



@login_required

def admin_dashboard(request):

    """Admin Dashboard with Statistics"""

    if request.user.role != 'admin':

        messages.error(request, 'Access denied')

        return redirect('home')



    # Auto punch out expired shifts

    auto_punch_out_expired_shifts()

    

    today = date.today()



    # Statistics

    total_employees = Employee.objects.filter(is_active=True).count()



    present_today = Attendance.objects.filter(

        date=today,

        status__in=['present', 'late']

    ).count()



    absent_today = total_employees - present_today



    late_today = Attendance.objects.filter(

        date=today,

        is_late=True

    ).count()



    on_leave_today = Leave.objects.filter(

        start_date__lte=today,

        end_date__gte=today,

        status='approved'

    ).count()



    pending_leaves = Leave.objects.filter(status='pending').count()



    # Calculate total monthly payroll

    current_month = today.month

    current_year = today.year

    total_payroll = 0



    for emp in Employee.objects.filter(is_active=True):

        salary_data = emp.calculate_monthly_salary(current_year, current_month)

        total_payroll += salary_data['final_salary']



    # Recent attendance

    recent_attendance = Attendance.objects.select_related('employee').filter(

        date=today

    ).order_by('-punch_in')[:10]



    # Pending leave requests

    pending_leave_requests = Leave.objects.select_related('employee').filter(

        status='pending'

    ).order_by('-applied_on')[:5]

    # ===== BIRTHDAY LOGIC =====
    from datetime import timedelta
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    # Aaj jinaka birthday hai
    todays_birthdays = Employee.objects.filter(
        is_active=True,
        date_of_birth__isnull=False,
        date_of_birth__day=today.day,
        date_of_birth__month=today.month,
    )

    # 2 din baad birthday wale (admin ko advance alert)
    upcoming_birthdays = Employee.objects.filter(
        is_active=True,
        date_of_birth__isnull=False,
    ).exclude(
        date_of_birth__day=today.day,
        date_of_birth__month=today.month,
    ).filter(
        date_of_birth__day__in=[tomorrow.day, day_after.day],
        date_of_birth__month__in=[tomorrow.month, day_after.month],
    )
    # Filter more precisely (month match bhi chahiye)
    upcoming_birthdays = [
        emp for emp in Employee.objects.filter(is_active=True, date_of_birth__isnull=False)
        if emp.days_until_birthday() in [1, 2]
    ]

    context = {

        'total_employees': total_employees,

        'present_today': present_today,

        'absent_today': absent_today,

        'late_today': late_today,

        'on_leave_today': on_leave_today,

        'pending_leaves': pending_leaves,

        'total_payroll': total_payroll,

        'recent_attendance': recent_attendance,

        'pending_leave_requests': pending_leave_requests,

        'today': today,

        'todays_birthdays': todays_birthdays,

        'upcoming_birthdays': upcoming_birthdays,

    }



    return render(request, 'admin/dashboard.html', context)





# ==================== EMPLOYEE MANAGEMENT ====================



@login_required

def employee_list(request):

    """List all employees"""

    if request.user.role != 'admin':

        return redirect('home')



    employees = Employee.objects.all().order_by('employee_id')

    # ===== BIRTHDAY LOGIC FOR EMPLOYEE PANEL =====
    today = date.today()
    todays_birthdays = [
        emp for emp in employees if emp.is_birthday_today()
    ]
    upcoming_birthdays = [
        emp for emp in employees if emp.date_of_birth and emp.days_until_birthday() in [1, 2]
    ]

    return render(request, 'admin/employee_list.html', {
        'employees': employees,
        'todays_birthdays': todays_birthdays,
        'upcoming_birthdays': upcoming_birthdays,
    })





@login_required

def employee_add(request):

    """Add new employee"""

    if request.user.role != 'admin':

        return redirect('home')



    if request.method == 'POST':

        form = EmployeeRegistrationForm(request.POST, request.FILES)

        if form.is_valid():

            employee = form.save()

            messages.success(request, f'Employee {employee.full_name} added successfully!')

            return redirect('employee_list')

    else:

        form = EmployeeRegistrationForm()



    return render(request, 'admin/employee_form.html', {'form': form, 'action': 'Add'})





@login_required

def employee_edit(request, pk):

    """Edit employee details"""

    if request.user.role != 'admin':

        return redirect('home')



    employee = get_object_or_404(Employee, pk=pk)



    if request.method == 'POST':

        form = EmployeeUpdateForm(request.POST, request.FILES, instance=employee)

        if form.is_valid():

            form.save()

            messages.success(request, 'Employee updated successfully!')

            return redirect('employee_list')

    else:

        form = EmployeeUpdateForm(instance=employee)



    return render(request, 'admin/employee_form.html', {

        'form': form,

        'employee': employee,

        'action': 'Edit'

    })





@login_required

@login_required

def employee_delete(request, pk):

    """Delete employee"""

    if request.user.role != 'admin':

        return redirect('home')



    employee = get_object_or_404(Employee, pk=pk)



    if request.method == 'POST':

        employee.user.delete()  # This will cascade delete employee

        messages.success(request, 'Employee deleted successfully!')

        return redirect('employee_list')



    return render(request, 'admin/employee_confirm_delete.html', {'employee': employee})





@login_required

def employee_toggle_status(request, pk):

    """Toggle employee active status via AJAX"""

    if request.user.role != 'admin':

        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    

    if request.method == 'POST':

        try:

            employee = get_object_or_404(Employee, pk=pk)

            data = json.loads(request.body)

            is_active = data.get('is_active', False)

            

            # Update employee status

            employee.is_active = is_active

            employee.save()

            

            # Update user status

            employee.user.is_active = is_active

            employee.user.save()

            

            return JsonResponse({

                'success': True,

                'message': 'Employee status updated successfully',

                'is_active': is_active

            })

        except Exception as e:

            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)





@login_required

def employee_profile(request, pk):

    """View employee profile"""

    if request.user.role != 'admin':

        return redirect('home')



    employee = get_object_or_404(Employee, pk=pk)



    # Get current month attendance

    today = date.today()

    attendance_records = Attendance.objects.filter(

        employee=employee,

        date__month=today.month,

        date__year=today.year

    ).order_by('-date')



    # Calculate salary

    salary_data = employee.calculate_monthly_salary(today.year, today.month)



    context = {

        'employee': employee,

        'attendance_records': attendance_records,

        'salary_data': salary_data,

    }



    return render(request, 'admin/employee_profile.html', context)





# ==================== ATTENDANCE MANAGEMENT ====================



@login_required

def attendance_list(request):

    """View attendance records with filters"""

    if request.user.role != 'admin':

        return redirect('home')



    attendances = Attendance.objects.select_related('employee').all()



    # Apply filters

    if request.GET:

        form = AttendanceFilterForm(request.GET)

        if form.is_valid():

            if form.cleaned_data.get('date'):

                attendances = attendances.filter(date=form.cleaned_data['date'])

            if form.cleaned_data.get('employee'):

                attendances = attendances.filter(employee=form.cleaned_data['employee'])

            if form.cleaned_data.get('status'):

                attendances = attendances.filter(status=form.cleaned_data['status'])

    else:

        form = AttendanceFilterForm()

        # Default: today's attendance

        attendances = attendances.filter(date=date.today())



    attendances = attendances.order_by('-date', '-punch_in')



    return render(request, 'admin/attendance_list.html', {

        'attendances': attendances,

        'form': form

    })





@login_required

def attendance_export(request):

    """Export attendance to CSV"""

    if request.user.role != 'admin':

        return redirect('home')



    response = HttpResponse(content_type='text/csv')

    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'



    writer = csv.writer(response)

    writer.writerow([

        'Employee ID', 'Employee Name', 'Date', 'Punch In',

        'Punch Out', 'Status', 'Working Hours'

    ])



    attendances = Attendance.objects.select_related('employee').all()



    # Apply filters if provided

    if request.GET.get('date'):

        attendances = attendances.filter(date=request.GET['date'])



    for att in attendances:

        writer.writerow([

            att.employee.employee_id,

            att.employee.full_name,

            att.date,

            att.punch_in.strftime('%H:%M:%S') if att.punch_in else '',

            att.punch_out.strftime('%H:%M:%S') if att.punch_out else '',

            att.status,

            att.get_working_hours()

        ])



    return response





# ==================== LEAVE MANAGEMENT ====================



@login_required

def leave_requests(request):

    """View all leave requests"""

    if request.user.role != 'admin':

        return redirect('home')



    status_filter = request.GET.get('status', 'pending')



    leaves = Leave.objects.select_related('employee').filter(

        status=status_filter

    ).order_by('-applied_on')



    return render(request, 'admin/leave_requests.html', {

        'leaves': leaves,

        'status_filter': status_filter

    })





@login_required

def leave_review(request, pk):

    """Approve or reject leave"""

    if request.user.role != 'admin':

        return redirect('home')



    leave = get_object_or_404(Leave, pk=pk)



    if request.method == 'POST':

        form = LeaveReviewForm(request.POST, instance=leave)

        if form.is_valid():

            leave = form.save(commit=False)

            leave.reviewed_by = request.user

            leave.reviewed_on = timezone.now()

            leave.save()



            messages.success(request, f'Leave request {leave.status}!')

            # Send push notification to employee
            try:
                from .push_views import send_push_to_employee
                status_text = 'Approved ✅' if leave.status == 'approved' else 'Rejected ❌'
                send_push_to_employee(
                    leave.employee,
                    title=f'Leave {status_text}',
                    body=f'{leave.start_date} to {leave.end_date}',
                    url='/employee/leaves/'
                )
            except Exception:
                pass

            return redirect('leave_requests')

    else:

        form = LeaveReviewForm(instance=leave)



    return render(request, 'admin/leave_review.html', {

        'form': form,

        'leave': leave

    })





# ==================== SALARY MANAGEMENT ====================



@login_required

def salary_report(request):

    """Monthly salary report"""

    if request.user.role != 'admin':

        return redirect('home')



    today = date.today()

    month = int(request.GET.get('month', today.month))

    year = int(request.GET.get('year', today.year))



    employees = Employee.objects.filter(is_active=True)

    salary_data = []

    total_payroll = 0



    for emp in employees:

        data = emp.calculate_monthly_salary(year, month)

        data['employee'] = emp

        salary_data.append(data)

        total_payroll += data['final_salary']



    context = {

        'salary_data': salary_data,

        'total_payroll': total_payroll,

        'month': month,

        'year': year,

    }



    return render(request, 'admin/salary_report.html', context)





@login_required

def salary_export(request):

    """Export salary report to CSV"""

    if request.user.role != 'admin':

        return redirect('home')



    today = date.today()

    month = int(request.GET.get('month', today.month))

    year = int(request.GET.get('year', today.year))



    response = HttpResponse(content_type='text/csv')

    response['Content-Disposition'] = f'attachment; filename="salary_report_{month}_{year}.csv"'



    writer = csv.writer(response)

    writer.writerow([

        'Employee ID', 'Name', 'Designation', 'Base Salary',

        'Present Days', 'Approved Leaves', 'Total Working Days',

        'Per Day Salary', 'Final Salary', 'Deduction'

    ])



    employees = Employee.objects.filter(is_active=True)



    for emp in employees:

        data = emp.calculate_monthly_salary(year, month)

        writer.writerow([

            emp.employee_id,

            emp.full_name,

            emp.designation,

            data['base_salary'],

            data['present_days'],

            data['approved_leaves'],

            data['total_working_days'],

            data['per_day_salary'],

            data['final_salary'],

            data['deduction']

        ])



    return response





# ==================== OFFICE LOCATION (GEOFENCE) ====================



@login_required

def office_location_settings(request):

    """Manage office location for geofence"""

    if request.user.role != 'admin':

        return redirect('home')



    office_location = OfficeLocation.objects.filter(is_active=True).first()



    if request.method == 'POST':

        if office_location:

            form = OfficeLocationForm(request.POST, instance=office_location)

        else:

            form = OfficeLocationForm(request.POST)



        if form.is_valid():

            form.save()

            messages.success(request, 'Office location updated!')

            return redirect('office_location_settings')

    else:

        if office_location:

            form = OfficeLocationForm(instance=office_location)

        else:

            form = OfficeLocationForm()



    return render(request, 'admin/office_location.html', {

        'form': form,

        'office_location': office_location

    })





@login_required

def week_off_settings(request):

    """Manage week off days"""

    if request.user.role != 'admin':

        return redirect('home')

    

    # Get all week off settings

    week_offs = WeekOff.objects.all()

    

    # Create default week offs if none exist

    if not week_offs.exists():

        # Create all days, Sunday as default week off

        for day in range(7):

            WeekOff.objects.create(

                weekday=day,

                is_active=(day == 6)  # Sunday is active by default

            )

        week_offs = WeekOff.objects.all()

    

    if request.method == 'POST':

        # Update week off status

        for week_off in week_offs:

            is_active = request.POST.get(f'weekday_{week_off.weekday}') == 'on'

            week_off.is_active = is_active

            week_off.save()

        

        messages.success(request, 'Week off settings updated successfully!')

        return redirect('week_off_settings')

    

    return render(request, 'admin/week_off_settings.html', {

        'week_offs': week_offs

    })





@login_required

def holiday_list(request):

    """List all holidays"""

    if request.user.role != 'admin':

        return redirect('home')

    

    holidays = Holiday.objects.all()

    

    return render(request, 'admin/holiday_list.html', {

        'holidays': holidays

    })





@login_required

def holiday_create(request):

    """Create new holiday"""

    if request.user.role != 'admin':

        return redirect('home')

    

    if request.method == 'POST':

        form = HolidayForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(request, 'Holiday created successfully!')

            return redirect('holiday_list')

    else:

        form = HolidayForm()

    

    return render(request, 'admin/holiday_form.html', {

        'form': form,

        'title': 'Add New Holiday'

    })





@login_required

def holiday_edit(request, pk):

    """Edit existing holiday"""

    if request.user.role != 'admin':

        return redirect('home')

    

    holiday = get_object_or_404(Holiday, pk=pk)

    

    if request.method == 'POST':

        form = HolidayForm(request.POST, instance=holiday)

        if form.is_valid():

            form.save()

            messages.success(request, 'Holiday updated successfully!')

            return redirect('holiday_list')

    else:

        form = HolidayForm(instance=holiday)

    

    return render(request, 'admin/holiday_form.html', {

        'form': form,

        'title': 'Edit Holiday',

        'holiday': holiday

    })





@login_required

def holiday_delete(request, pk):

    """Delete holiday"""

    if request.user.role != 'admin':

        return redirect('home')

    

    holiday = get_object_or_404(Holiday, pk=pk)

    

    if request.method == 'POST':

        holiday.delete()

        messages.success(request, 'Holiday deleted successfully!')

        return redirect('holiday_list')

    

    return render(request, 'admin/holiday_confirm_delete.html', {

        'holiday': holiday

    })





# ==================== EMPLOYEE DASHBOARD ====================



@login_required

def employee_dashboard(request):

    """Employee Dashboard"""

    if request.user.role != 'employee':

        return redirect('home')



    employee = request.user.employee_profile

    

    # Check if employee is active

    if not employee.is_active:

        logout(request)

        messages.error(request, 'Your account has been deactivated. Please contact admin.')

        return redirect('employee_login')

    

    # Auto punch out expired shifts

    auto_punch_out_expired_shifts()

    

    today = date.today()



    # Get today's attendance

    today_attendance = Attendance.objects.filter(

        employee=employee,

        date=today

    ).first()



    # Monthly statistics

    present_count = Attendance.objects.filter(

        employee=employee,

        date__month=today.month,

        date__year=today.year,

        status__in=['present', 'late']

    ).count()



    leave_count = Leave.objects.filter(

        employee=employee,

        start_date__month=today.month,

        start_date__year=today.year,

        status='approved'

    ).count()



    # Calculate current month salary

    salary_data = employee.calculate_monthly_salary(today.year, today.month)



    # Current month incentives

    from .models import Incentive

    from django.db.models import Sum

    current_incentive = Incentive.objects.filter(

        employee=employee,

        incentive_date__year=today.year,

        incentive_date__month=today.month,

    ).aggregate(total=Sum('amount'))['total'] or 0

    total_salary_with_incentive = salary_data['final_salary'] + current_incentive



    # Recent attendance

    recent_attendance = Attendance.objects.filter(

        employee=employee

    ).order_by('-date')[:10]



    # Get office location for geofence

    office_location = OfficeLocation.objects.filter(is_active=True).first()

    # ===== BIRTHDAY - aaj jinaka birthday hai (saare active employees) =====
    todays_birthdays = [
        emp for emp in Employee.objects.filter(is_active=True, date_of_birth__isnull=False)
        if emp.is_birthday_today()
    ]
    upcoming_birthdays = [
        emp for emp in Employee.objects.filter(is_active=True, date_of_birth__isnull=False)
        if emp.days_until_birthday() in [1, 2]
    ]

    context = {

        'employee': employee,

        'today_attendance': today_attendance,

        'present_count': present_count,

        'leave_count': leave_count,

        'salary_data': salary_data,

        'current_incentive': current_incentive,

        'total_salary_with_incentive': total_salary_with_incentive,

        'recent_attendance': recent_attendance,

        'office_location': office_location,

        'todays_birthdays': todays_birthdays,

        'upcoming_birthdays': upcoming_birthdays,

    }



    return render(request, 'employee/dashboard.html', context)





# ==================== PUNCH IN/OUT WITH FACE RECOGNITION ====================



@login_required

def punch_in_out(request):

    """Punch In/Out page with camera"""

    if request.user.role != 'employee':

        return redirect('home')



    employee = request.user.employee_profile

    

    # Check if employee is active

    if not employee.is_active:

        logout(request)

        messages.error(request, 'Your account has been deactivated. Please contact admin.')

        return redirect('employee_login')

    

    today = date.today()



    attendance = Attendance.objects.filter(

        employee=employee,

        date=today

    ).first()



    office_location = OfficeLocation.objects.filter(is_active=True).first()



    context = {

        'employee': employee,

        'attendance': attendance,

        'office_location': office_location,

    }



    return render(request, 'employee/punch_in_out.html', context)





@login_required

def process_punch(request):

    """Process punch in/out with face recognition and geofence"""

    if request.method != 'POST' or request.user.role != 'employee':

        return JsonResponse({'success': False, 'message': 'Invalid request'})



    try:

        employee = request.user.employee_profile

        

        # Check if employee is active

        if not employee.is_active:

            return JsonResponse({

                'success': False,

                'message': 'Your account has been deactivated. Please contact admin.'

            })

        

        # Check if shift is assigned

        if not employee.shift:

            return JsonResponse({

                'success': False,

                'message': 'No shift assigned to you. Please contact admin to assign a shift.'

            })

        

        data = json.loads(request.body)

        action = data.get('action')  # 'punch_in' or 'punch_out'

        image_data = data.get('image')

        latitude = data.get('latitude')

        longitude = data.get('longitude')



        today = date.today()



        # Step 1: Validate Geofence

        office_location = OfficeLocation.objects.filter(is_active=True).first()



        if office_location:

            from math import radians, sin, cos, sqrt, atan2



            # Haversine formula to calculate distance

            lat1, lon1 = radians(float(office_location.latitude)), radians(float(office_location.longitude))

            lat2, lon2 = radians(float(latitude)), radians(float(longitude))



            dlat = lat2 - lat1

            dlon = lon2 - lon1



            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2

            c = 2 * atan2(sqrt(a), sqrt(1-a))

            distance = 6371000 * c  # Earth radius in meters



            if distance > office_location.radius:

                return JsonResponse({

                    'success': False,

                    'message': f'You are {int(distance)}m away from office. Must be within {office_location.radius}m.'

                })



        # Step 2: Face Recognition

        if not employee.face_encoding:

            return JsonResponse({

                'success': False,

                'message': 'Face encoding not found. Contact admin.'

            })



        # Decode base64 image

        image_data = image_data.split(',')[1]

        image_bytes = base64.b64decode(image_data)

        nparr = np.frombuffer(image_bytes, np.uint8)

        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)



        # Detect face

        face_locations = face_recognition.face_locations(rgb_frame)



        if not face_locations:

            return JsonResponse({

                'success': False,

                'message': 'No face detected. Please position your face clearly.'

            })



        # Get face encoding

        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)



        if not face_encodings:

            return JsonResponse({

                'success': False,

                'message': 'Could not process face. Try again.'

            })



        # Compare with stored encoding

        stored_encoding = np.array(json.loads(employee.face_encoding))

        matches = face_recognition.compare_faces([stored_encoding], face_encodings[0], tolerance=0.45)



        if not matches[0]:

            return JsonResponse({

                'success': False,

                'message': 'Face not matched. Authentication failed.'

            })



        # Step 3: Validate Shift Timing

        if action == 'punch_in' and employee.shift:

            # Get current time in local timezone

            from django.utils import timezone as tz

            local_now = tz.localtime(tz.now())

            current_time = local_now.time()

            shift = employee.shift

            

            # Check if current time is before shift start

            if current_time < shift.punch_in_start:

                shift_name = shift.get_name_display()

                shift_start = shift.punch_in_start.strftime('%I:%M %p')

                return JsonResponse({

                    'success': False,

                    'message': f'Your {shift_name} starts at {shift_start}. Please wait until shift starts. Current time: {current_time.strftime("%I:%M %p")}'

                })

        

        # Step 4: Process Punch In/Out

        location_str = f"{latitude},{longitude}"



        if action == 'punch_in':

            # Check if already punched in

            existing = Attendance.objects.filter(employee=employee, date=today).first()



            if existing and existing.punch_in:

                return JsonResponse({

                    'success': False,

                    'message': 'Already punched in today.'

                })



            # Create or update attendance

            attendance, created = Attendance.objects.get_or_create(

                employee=employee,

                date=today,

                defaults={

                    'punch_in': timezone.now(),

                    'punch_in_location': location_str

                }

            )



            if not created:

                attendance.punch_in = timezone.now()

                attendance.punch_in_location = location_str

                attendance.save()



            return JsonResponse({

                'success': True,

                'message': 'Punch In successful!',

                'time': attendance.punch_in.strftime('%I:%M %p'),

                'status': attendance.status

            })



        elif action == 'punch_out':

            attendance = Attendance.objects.filter(employee=employee, date=today).first()



            if not attendance or not attendance.punch_in:

                return JsonResponse({

                    'success': False,

                    'message': 'Please punch in first.'

                })



            if attendance.punch_out:

                return JsonResponse({

                    'success': False,

                    'message': 'Already punched out today.'

                })

            

            # No strict validation for punch out timing

            # Employees can punch out anytime after punch in



            attendance.punch_out = timezone.now()

            attendance.punch_out_location = location_str

            attendance.save()



            return JsonResponse({

                'success': True,

                'message': 'Punch Out successful!',

                'time': attendance.punch_out.strftime('%I:%M %p'),

                'working_hours': attendance.get_working_hours()

            })



    except Exception as e:

        return JsonResponse({

            'success': False,

            'message': f'Error: {str(e)}'

        })





# ==================== EMPLOYEE LEAVE MANAGEMENT ====================



@login_required

def employee_leaves(request):

    """Employee leave management"""

    if request.user.role != 'employee':

        return redirect('home')



    employee = request.user.employee_profile

    

    # Check if employee is active

    if not employee.is_active:

        logout(request)

        messages.error(request, 'Your account has been deactivated. Please contact admin.')

        return redirect('employee_login')



    if request.method == 'POST':

        form = LeaveRequestForm(request.POST)

        if form.is_valid():

            leave = form.save(commit=False)

            leave.employee = employee

            leave.save()

            messages.success(request, 'Leave request submitted!')

            return redirect('employee_leaves')

    else:

        form = LeaveRequestForm()



    leaves = Leave.objects.filter(employee=employee).order_by('-applied_on')



    # Calculate counts by status

    pending_count = leaves.filter(status='pending').count()

    approved_count = leaves.filter(status='approved').count()

    rejected_count = leaves.filter(status='rejected').count()



    return render(request, 'employee/leaves.html', {

        'form': form,

        'leaves': leaves,

        'pending_count': pending_count,

        'approved_count': approved_count,

        'rejected_count': rejected_count,

    })





@login_required

def employee_attendance_history(request):

    """Employee attendance history"""

    if request.user.role != 'employee':

        return redirect('home')



    employee = request.user.employee_profile

    

    # Check if employee is active

    if not employee.is_active:

        logout(request)

        messages.error(request, 'Your account has been deactivated. Please contact admin.')

        return redirect('employee_login')



    attendances = Attendance.objects.filter(

        employee=employee

    ).order_by('-date')[:30]



    # Calculate average working hours

    total_hours = 0

    count = 0

    late_count = 0

    

    for att in attendances:

        hours = att.get_working_hours()

        if hours > 0:

            total_hours += hours

            count += 1

        if att.is_late or att.status == 'late':

            late_count += 1

    

    avg_hours = round(total_hours / count, 1) if count > 0 else 0



    return render(request, 'employee/attendance_history.html', {

        'attendances': attendances,

        'avg_hours': avg_hours,

        'late_count': late_count

    })





# ==================== MONTHLY CALENDAR REPORT ====================



@login_required

def monthly_attendance_report(request):

    """Monthly calendar view attendance report"""

    if request.user.role != 'admin':

        return redirect('home')



    today = date.today()

    month = int(request.GET.get('month', today.month))

    year = int(request.GET.get('year', today.year))

    employee_id = request.GET.get('employee')



    # Get all active employees

    employees = Employee.objects.filter(is_active=True).order_by('employee_id')



    # Filter by specific employee if selected

    if employee_id:

        employees = employees.filter(id=employee_id)



    # Generate calendar data for each employee

    import calendar

    # Set first day of week to Sunday (6)

    calendar.setfirstweekday(calendar.SUNDAY)

    cal = calendar.monthcalendar(year, month)

    month_name = calendar.month_name[month]



    employee_reports = []



    for employee in employees:

        # Get all attendance for this month

        attendances = Attendance.objects.filter(

            employee=employee,

            date__year=year,

            date__month=month

        )



        # Create attendance dict by date

        attendance_dict = {}

        for att in attendances:

            # Determine status based on is_late and punch_in

            if att.punch_in:

                status = 'late' if att.is_late else 'present'

            else:

                status = 'absent'

            

            attendance_dict[att.date.day] = {

                'status': status,

                'punch_in': att.punch_in,

                'punch_out': att.punch_out,

                'is_late': att.is_late

            }



        # Build calendar weeks

        calendar_weeks = []

        for week in cal:

            week_days = []

            for day in week:

                if day == 0:

                    week_days.append({'day': '', 'status': None})

                else:

                    check_date = date(year, month, day)

                    

                    # Check if week off

                    is_week_off = WeekOff.is_week_off(check_date)

                    

                    # Check if holiday

                    is_holiday = Holiday.is_holiday(check_date)

                    

                    day_data = attendance_dict.get(day, {'status': 'absent'})

                    

                    # Override status if week off or holiday

                    if is_week_off:

                        status = 'week_off'

                    elif is_holiday:

                        status = 'holiday'

                    else:

                        status = day_data.get('status', 'absent')

                    

                    week_days.append({

                        'day': day,

                        'status': status,

                        'punch_in': day_data.get('punch_in'),

                        'is_late': day_data.get('is_late', False),

                        'is_week_off': is_week_off,

                        'is_holiday': is_holiday

                    })

            calendar_weeks.append(week_days)



        # Calculate stats

        present_count = attendances.filter(punch_in__isnull=False, is_late=False).count()

        late_count = attendances.filter(is_late=True).count()

        total_days_in_month = calendar.monthrange(year, month)[1]

        absent_count = total_days_in_month - attendances.filter(punch_in__isnull=False).count()



        employee_reports.append({

            'employee': employee,

            'calendar_weeks': calendar_weeks,

            'present_count': present_count,

            'late_count': late_count,

            'absent_count': absent_count,

            'total_days': calendar.monthrange(year, month)[1]

        })



    context = {

        'employee_reports': employee_reports,

        'month': month,

        'year': year,

        'month_name': month_name,

        'all_employees': Employee.objects.filter(is_active=True),

        'selected_employee': employee_id,

    }



    return render(request, 'admin/monthly_attendance_report.html', context)





@login_required

def export_monthly_report_pdf(request):

    """Export monthly attendance report as PDF"""

    if request.user.role != 'admin':

        return redirect('home')



    from reportlab.lib.pagesizes import A4, landscape

    from reportlab.lib import colors

    from reportlab.lib.units import inch

    from reportlab.platypus import (

        SimpleDocTemplate, Table, TableStyle, Paragraph,

        Spacer, PageBreak

    )

    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    from io import BytesIO

    import calendar



    today = date.today()

    month = int(request.GET.get('month', today.month))

    year = int(request.GET.get('year', today.year))

    employee_id = request.GET.get('employee')



    # Create PDF

    buffer = BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        pagesize=landscape(A4),

        rightMargin=30,

        leftMargin=30,

        topMargin=30,

        bottomMargin=30

    )



    elements = []

    styles = getSampleStyleSheet()



    # Title style

    title_style = ParagraphStyle(

        'CustomTitle',

        parent=styles['Heading1'],

        fontSize=18,

        textColor=colors.HexColor('#6C63FF'),

        spaceAfter=30,

        alignment=TA_CENTER

    )



    # Get employees

    employees = Employee.objects.filter(is_active=True).order_by('employee_id')

    if employee_id:

        employees = employees.filter(id=employee_id)



    employees_list = list(employees)  # Convert to list

    month_name = calendar.month_name[month]

    num_days = calendar.monthrange(year, month)[1]



    # Title

    title = Paragraph(

        f"Monthly Attendance Report - {month_name} {year}",

        title_style

    )

    elements.append(title)

    elements.append(Spacer(1, 0.3 * inch))



    for idx, employee in enumerate(employees_list):

        # Get attendance data first for summary

        attendances = Attendance.objects.filter(

            employee=employee,

            date__year=year,

            date__month=month

        )



        attendance_dict = {}

        for att in attendances:

            attendance_dict[att.date.day] = att.status



        # Calculate stats

        present_count = attendances.filter(status='present').count()

        late_count = attendances.filter(status='late').count()

        absent_count = num_days - attendances.count()



        # Employee header with summary in one line

        emp_style = ParagraphStyle(

            'EmpHeader',

            parent=styles['Heading2'],

            fontSize=12,

            textColor=colors.HexColor('#FF6B35'),

            spaceAfter=10

        )

        

        # Create header table with employee info and summary

        header_data = [[

            Paragraph(f"<b>Employee:</b> {employee.full_name} ({employee.employee_id})", emp_style),

            Paragraph(f"<b>Summary:</b> Present: {present_count} | Late: {late_count} | Absent: {absent_count}", styles['Normal'])

        ]]

        

        header_table = Table(header_data, colWidths=[4.5*inch, 4.5*inch])

        header_table.setStyle(TableStyle([

            ('ALIGN', (0, 0), (0, 0), 'LEFT'),

            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),

            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ]))

        elements.append(header_table)

        elements.append(Spacer(1, 0.1 * inch))



        # Get attendance data for table (already fetched above)

        # attendance_dict already populated



        # Create table data - Horizontal format

        table_data = []



        # Header row with dates

        header_row = ['Date']

        for day in range(1, num_days + 1):

            header_row.append(str(day))

        table_data.append(header_row)



        # Status row

        status_row = ['Status']

        for day in range(1, num_days + 1):

            status = attendance_dict.get(day, 'absent')

            if status == 'present':

                status_row.append('P')

            elif status == 'late':

                status_row.append('L')

            else:

                status_row.append('A')

        table_data.append(status_row)



        # Create table

        table = Table(table_data, colWidths=[0.8 * inch] + [0.25 * inch] * num_days)



        # Table style

        table_style = TableStyle([

            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C63FF')),

            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),

            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

            ('FONTSIZE', (0, 0), (-1, 0), 8),

            ('FONTSIZE', (0, 1), (-1, -1), 7),

            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        ])



        # Color code cells

        for day in range(1, num_days + 1):

            col = day

            status = attendance_dict.get(day, 'absent')

            if status == 'present':

                table_style.add('BACKGROUND', (col, 1), (col, 1),

                              colors.HexColor('#4CAF50'))

                table_style.add('TEXTCOLOR', (col, 1), (col, 1),

                              colors.whitesmoke)

            elif status == 'late':

                table_style.add('BACKGROUND', (col, 1), (col, 1),

                              colors.HexColor('#FF9800'))

                table_style.add('TEXTCOLOR', (col, 1), (col, 1),

                              colors.whitesmoke)

            else:

                table_style.add('BACKGROUND', (col, 1), (col, 1),

                              colors.HexColor('#FF6B6B'))

                table_style.add('TEXTCOLOR', (col, 1), (col, 1),

                              colors.whitesmoke)



        table.setStyle(table_style)

        elements.append(table)



        # Legend only

        legend_text = """

        <b>Legend:</b>

        <font color='green'><b>Green = Present</b></font> |

        <font color='orange'><b>Orange = Late</b></font> |

        <font color='red'><b>Red = Absent</b></font>

        """

        legend_para = Paragraph(legend_text, styles['Normal'])

        elements.append(Spacer(1, 0.1 * inch))

        elements.append(legend_para)



        # Space between employees (no page break)

        if idx < len(employees_list) - 1:  # Not the last employee

            elements.append(Spacer(1, 0.5 * inch))



    # Build PDF

    doc.build(elements)

    buffer.seek(0)



    # Return PDF response

    response = HttpResponse(buffer, content_type='application/pdf')

    response['Content-Disposition'] = f'attachment; filename="attendance_report_{month}_{year}.pdf"'



    return response







# ==================== SHIFT MANAGEMENT VIEWS ====================



@login_required

def shift_list(request):

    """List all shifts"""

    if request.user.role != 'admin':

        return redirect('home')

    

    shifts = Shift.objects.all()

    context = {

        'shifts': shifts,

    }

    return render(request, 'admin/shift_list.html', context)





@login_required

def shift_create(request):

    """Create new shift"""

    if request.user.role != 'admin':

        return redirect('home')

    

    if request.method == 'POST':

        form = ShiftForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(request, 'Shift created successfully!')

            return redirect('shift_list')

    else:

        form = ShiftForm()

    

    context = {

        'form': form,

        'title': 'Create Shift',

    }

    return render(request, 'admin/shift_form.html', context)





@login_required

def shift_edit(request, pk):

    """Edit existing shift"""

    if request.user.role != 'admin':

        return redirect('home')

    

    shift = get_object_or_404(Shift, pk=pk)

    

    if request.method == 'POST':

        form = ShiftForm(request.POST, instance=shift)

        if form.is_valid():

            form.save()

            messages.success(request, 'Shift updated successfully!')

            return redirect('shift_list')

    else:

        form = ShiftForm(instance=shift)

    

    context = {

        'form': form,

        'shift': shift,

        'title': 'Edit Shift',

    }

    return render(request, 'admin/shift_form.html', context)





@login_required

def shift_delete(request, pk):

    """Delete shift"""

    if request.user.role != 'admin':

        return redirect('home')

    

    shift = get_object_or_404(Shift, pk=pk)

    

    if request.method == 'POST':

        shift.delete()

        messages.success(request, 'Shift deleted successfully!')

        return redirect('shift_list')

    

    context = {

        'shift': shift,

    }

    return render(request, 'admin/shift_confirm_delete.html', context)





@login_required

def employee_shift_assign(request, pk):

    """Assign or change employee shift"""

    if request.user.role != 'admin':

        return redirect('home')

    

    employee = get_object_or_404(Employee, pk=pk)

    

    if request.method == 'POST':

        form = EmployeeShiftAssignForm(request.POST, instance=employee)

        if form.is_valid():

            form.save()

            messages.success(request, f'Shift assigned to {employee.full_name} successfully!')

            return redirect('employee_list')

    else:

        form = EmployeeShiftAssignForm(instance=employee)

    

    context = {

        'form': form,

        'employee': employee,

    }

    return render(request, 'admin/employee_shift_assign.html', context)


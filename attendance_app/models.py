"""

Smart Attendance System - Database Models

Complete schema for attendance management with face recognition

"""

from django.db import models

from django.contrib.auth.models import AbstractUser

from django.core.validators import MinValueValidator

from datetime import date, datetime, time
from decimal import Decimal




class Shift(models.Model):

    """

    Shift Model

    Defines morning and night shift timings

    """

    SHIFT_CHOICES = (

        ('morning', 'Morning Shift'),

        ('night', 'Night Shift'),

    )

    

    name = models.CharField(max_length=20, choices=SHIFT_CHOICES, unique=True)

    punch_in_start = models.TimeField(help_text='Earliest punch in time')

    punch_in_end = models.TimeField(help_text='Latest punch in time (after this = Late)')

    punch_out_time = models.TimeField(help_text='Expected punch out time')

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    

    class Meta:

        verbose_name = 'Shift'

        verbose_name_plural = 'Shifts'

        ordering = ['name']

    

    def __str__(self):

        return f"{self.get_name_display()} ({self.punch_in_start.strftime('%I:%M %p')} - {self.punch_out_time.strftime('%I:%M %p')})"

    

    def get_working_hours(self):

        """Calculate total working hours for the shift (from punch in start to punch out)"""

        from datetime import timedelta

        

        # Create datetime objects for calculation

        # Working hours = punch_in_start to punch_out_time

        start = datetime.combine(datetime.today(), self.punch_in_start)

        end = datetime.combine(datetime.today(), self.punch_out_time)

        

        # Handle night shift (crosses midnight)

        if end < start:

            end += timedelta(days=1)

        

        # Calculate duration

        duration = end - start

        hours = duration.total_seconds() / 3600

        

        return round(hours, 1)





class User(AbstractUser):

    """

    Custom User Model extending Django's AbstractUser

    Supports both Admin and Employee roles

    """

    ROLE_CHOICES = (

        ('admin', 'Admin'),

        ('employee', 'Employee'),

    )

    

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')

    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    mobile_number = models.CharField(max_length=15, blank=True)

    

    class Meta:

        verbose_name = 'User'

        verbose_name_plural = 'Users'

    

    def __str__(self):

        return f"{self.username} ({self.get_role_display()})"





class Employee(models.Model):

    """

    Employee Profile Model

    Stores employee details and face encoding for recognition

    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')

    employee_id = models.CharField(max_length=20, unique=True)

    full_name = models.CharField(max_length=200)

    designation = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    mobile_number = models.CharField(max_length=15)

    photo = models.ImageField(upload_to='employee_photos/')

    face_encoding = models.TextField(blank=True, help_text='Face encoding for recognition')

    shift = models.ForeignKey('Shift', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', help_text='Assigned shift')

    date_of_birth = models.DateField(null=True, blank=True, help_text='Date of birth')

    base_salary = models.DecimalField(

        max_digits=10, 

        decimal_places=2,

        validators=[MinValueValidator(0)],

        help_text='Monthly base salary'

    )

    date_joined = models.DateField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    

    class Meta:

        verbose_name = 'Employee'

        verbose_name_plural = 'Employees'

        ordering = ['employee_id']

    

    def __str__(self):

        return f"{self.employee_id} - {self.full_name}"

    

    def get_per_day_salary(self):

        """Calculate per day salary (Base Salary / 30)"""

        return self.base_salary / 30

    def is_birthday_today(self):
        """Check if today is employee's birthday"""
        if not self.date_of_birth:
            return False
        today = date.today()
        return (self.date_of_birth.day == today.day and
                self.date_of_birth.month == today.month)

    def days_until_birthday(self):
        """Days remaining until next birthday (0 = today)"""
        if not self.date_of_birth:
            return None
        today = date.today()
        try:
            this_year_bday = date(today.year, self.date_of_birth.month, self.date_of_birth.day)
        except ValueError:
            return None
        if this_year_bday < today:
            this_year_bday = date(today.year + 1, self.date_of_birth.month, self.date_of_birth.day)
        return (this_year_bday - today).days

    

    def get_monthly_attendance_count(self, year, month):

        """Get present days count for a specific month"""

        return Attendance.objects.filter(

            employee=self,

            date__year=year,

            date__month=month,

            punch_in__isnull=False

        ).count()

    

    def calculate_monthly_salary(self, year, month):

        """

        Calculate monthly salary based on attendance with penalties

        

        Rules:

        1. 3 Late = 1 Half Day cut (0.5 day deduction)

        2. 1 Absent (without leave) = 2 Days cut

        3. 1 Hour+ late = Half Day (0.5 day count)

        4. Leaves = Per day cut (not counted as working days)

        """

        from datetime import timedelta

        

        # Get all attendance records for the month

        attendances = Attendance.objects.filter(

            employee=self,

            date__year=year,

            date__month=month

        )

        

        # Initialize counters

        present_days = 0

        late_count = 0

        very_late_count = 0  # 1+ hour late

        half_day_deductions = 0

        

        # Process each attendance

        for att in attendances:

            if att.punch_in:

                # Check if very late (1+ hour after punch_in_end)

                if self.shift and att.is_late:

                    punch_in_time = att.punch_in.time()

                    shift_end_time = self.shift.punch_in_end

                    

                    # Calculate how late

                    punch_in_datetime = datetime.combine(att.date, punch_in_time)

                    shift_end_datetime = datetime.combine(att.date, shift_end_time)

                    late_duration = punch_in_datetime - shift_end_datetime

                    

                    # If 1+ hour late, count as half day

                    if late_duration >= timedelta(hours=1):

                        very_late_count += 1

                        present_days += 0.5  # Half day only

                    else:

                        # Normal late (less than 1 hour)

                        late_count += 1

                        present_days += 1

                else:

                    # On time

                    present_days += 1

        

        # Calculate late penalties: 3 lates = 1 half day cut

        late_penalty_days = (late_count // 3) * 0.5

        

        # Get total days in month

        import calendar

        total_days_in_month = calendar.monthrange(year, month)[1]

        

        # Get approved leaves (these will be deducted, not added)

        approved_leaves = Leave.objects.filter(

            employee=self,

            start_date__year=year,

            start_date__month=month,

            status='approved'

        ).count()

        

        # Calculate absent days (days without punch in and without leave)

        attendance_dates = set(attendances.filter(

            punch_in__isnull=False

        ).values_list('date', flat=True))

        

        leave_dates = set()

        leaves = Leave.objects.filter(

            employee=self,

            start_date__year=year,

            start_date__month=month,

            status='approved'

        )

        for leave in leaves:

            current_date = leave.start_date

            while current_date <= leave.end_date:

                if current_date.year == year and current_date.month == month:

                    leave_dates.add(current_date)

                current_date += timedelta(days=1)

        

        # Count absent days (excluding week offs, holidays and leaves)

        absent_days = 0

        for day in range(1, total_days_in_month + 1):

            check_date = date(year, month, day)

            # Skip if week off

            if WeekOff.is_week_off(check_date):

                continue

            # Skip if holiday

            if Holiday.is_holiday(check_date):

                continue

            if check_date not in attendance_dates and check_date not in leave_dates:

                absent_days += 1

        

        # Absent penalty: 1 absent = 2 days cut

        absent_penalty_days = absent_days * 2

        

        # Calculate final working days

        # Start with present days, subtract penalties

        effective_working_days = present_days - late_penalty_days

        

        # Subtract absent penalties

        effective_working_days -= absent_penalty_days

        

        # Subtract leave days (leaves are not paid)

        effective_working_days -= approved_leaves

        

        # Ensure not negative

        if effective_working_days < 0:

            effective_working_days = 0

        

        # Calculate salary

        per_day_salary = self.get_per_day_salary()

        #final_salary = effective_working_days * per_day_salary
        final_salary = Decimal(str(effective_working_days)) * per_day_salary

        

        # Ensure salary doesn't exceed base salary

        if final_salary > self.base_salary:

            final_salary = self.base_salary

        

        return {

            'present_days': present_days,

            'late_count': late_count,

            'very_late_count': very_late_count,

            'late_penalty_days': late_penalty_days,

            'absent_days': absent_days,

            'absent_penalty_days': absent_penalty_days,

            'approved_leaves': approved_leaves,

            'effective_working_days': round(effective_working_days, 2),

            'per_day_salary': per_day_salary,

            'final_salary': round(final_salary, 2),

            'base_salary': self.base_salary,

            'deduction': round(self.base_salary - final_salary, 2)

        }





class Attendance(models.Model):

    """

    Attendance Model

    Tracks daily punch in/out with geolocation validation

    """

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')

    date = models.DateField(default=date.today)

    punch_in = models.DateTimeField(null=True, blank=True)

    punch_out = models.DateTimeField(null=True, blank=True)

    punch_in_location = models.CharField(max_length=200, blank=True, help_text='Lat,Long')

    punch_out_location = models.CharField(max_length=200, blank=True, help_text='Lat,Long')

    is_late = models.BooleanField(default=False)

    status = models.CharField(

        max_length=20,

        choices=(

            ('present', 'Present'),

            ('absent', 'Absent'),

            ('late', 'Late'),

            ('on_leave', 'On Leave'),

        ),

        default='absent'

    )

    notes = models.TextField(blank=True)

    

    class Meta:

        verbose_name = 'Attendance'

        verbose_name_plural = 'Attendance Records'

        unique_together = ['employee', 'date']

        ordering = ['-date', '-punch_in']

    

    def __str__(self):

        return f"{self.employee.full_name} - {self.date} ({self.status})"

    

    def save(self, *args, **kwargs):

        """Auto-calculate late status based on employee's shift timing"""

        if self.punch_in and self.employee.shift:

            # Convert punch_in to local time before comparing

            from django.utils import timezone as tz

            local_punch_in = tz.localtime(self.punch_in)

            punch_in_time = local_punch_in.time()

            shift = self.employee.shift

            

            # Check if punch in is within shift's valid range

            if shift.punch_in_start <= punch_in_time <= shift.punch_in_end:

                self.is_late = False

                self.status = 'present'

            elif punch_in_time > shift.punch_in_end:

                self.is_late = True

                self.status = 'late'

            else:

                # Before shift start time - mark as late (invalid time)

                self.is_late = True

                self.status = 'late'

        elif self.punch_in:

            # Fallback to default timing if no shift assigned

            from django.utils import timezone as tz

            local_punch_in = tz.localtime(self.punch_in)

            punch_in_time = local_punch_in.time()

            start_time = time(6, 0, 0)

            late_threshold = time(10, 0, 0)

            

            if start_time <= punch_in_time <= late_threshold:

                self.is_late = False

                self.status = 'present'

            else:

                self.is_late = True

                self.status = 'late'

        

        super().save(*args, **kwargs)

    

    def get_working_hours(self):

        """Calculate total working hours"""

        if self.punch_in and self.punch_out:

            duration = self.punch_out - self.punch_in

            hours = duration.total_seconds() / 3600

            return round(hours, 2)

        return 0





class Leave(models.Model):

    """

    Leave Request Model

    Manages employee leave applications

    """

    STATUS_CHOICES = (

        ('pending', 'Pending'),

        ('approved', 'Approved'),

        ('rejected', 'Rejected'),

    )

    

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')

    start_date = models.DateField()

    end_date = models.DateField()

    reason = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    applied_on = models.DateTimeField(auto_now_add=True)

    reviewed_by = models.ForeignKey(

        User, 

        on_delete=models.SET_NULL, 

        null=True, 

        blank=True,

        related_name='reviewed_leaves'

    )

    reviewed_on = models.DateTimeField(null=True, blank=True)

    admin_remarks = models.TextField(blank=True)

    

    class Meta:

        verbose_name = 'Leave'

        verbose_name_plural = 'Leave Requests'

        ordering = ['-applied_on']

    

    def __str__(self):

        return f"{self.employee.full_name} - {self.start_date} to {self.end_date}"

    

    def get_total_days(self):

        """Calculate total leave days"""

        delta = self.end_date - self.start_date

        return delta.days + 1





class OfficeLocation(models.Model):

    """

    Office Location Model for GeoFence

    Stores office coordinates and allowed radius

    """

    name = models.CharField(max_length=200, default='Main Office')

    latitude = models.DecimalField(max_digits=9, decimal_places=6)

    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    radius = models.IntegerField(

        default=200,

        help_text='Allowed radius in meters'

    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    

    class Meta:

        verbose_name = 'Office Location'

        verbose_name_plural = 'Office Locations'

    

    def __str__(self):

        return f"{self.name} ({self.latitude}, {self.longitude})"





class WeekOff(models.Model):

    """

    Week Off Configuration Model

    Manages weekly off days (e.g., Sunday)

    """

    WEEKDAY_CHOICES = (

        (0, 'Monday'),

        (1, 'Tuesday'),

        (2, 'Wednesday'),

        (3, 'Thursday'),

        (4, 'Friday'),

        (5, 'Saturday'),

        (6, 'Sunday'),

    )

    

    weekday = models.IntegerField(

        choices=WEEKDAY_CHOICES,

        unique=True,

        help_text='Day of the week (0=Monday, 6=Sunday)'

    )

    is_active = models.BooleanField(

        default=True,

        help_text='Is this day a week off?'

    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    

    class Meta:

        verbose_name = 'Week Off'

        verbose_name_plural = 'Week Off Settings'

        ordering = ['weekday']

    

    def __str__(self):

        return f"{self.get_weekday_display()} - {'Active' if self.is_active else 'Inactive'}"

    

    @classmethod

    def is_week_off(cls, date_obj):

        """Check if a given date is a week off"""

        weekday = date_obj.weekday()  # 0=Monday, 6=Sunday

        return cls.objects.filter(weekday=weekday, is_active=True).exists()







class Salary(models.Model):

    """

    Salary Record Model

    Stores monthly salary calculations with payment tracking

    """

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')

    

    # Salary Cycle Dates

    cycle_start_date = models.DateField(help_text='Salary cycle start date (e.g., 10th of month)')

    cycle_end_date = models.DateField(help_text='Salary cycle end date (e.g., 9th of next month)')

    

    # Salary Calculation

    base_salary = models.DecimalField(max_digits=10, decimal_places=2)

    present_days = models.IntegerField(default=0)

    approved_leaves = models.IntegerField(default=0)

    total_working_days = models.IntegerField(default=0)

    per_day_salary = models.DecimalField(max_digits=10, decimal_places=2)

    final_salary = models.DecimalField(max_digits=10, decimal_places=2)

    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    

    # Incentive

    incentive_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Total incentive added to this salary')



    # Payment Tracking

    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Total amount paid so far')

    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Remaining amount to be paid')

    

    # Status

    payment_status = models.CharField(

        max_length=20,

        choices=(

            ('pending', 'Pending'),

            ('partial', 'Partially Paid'),

            ('completed', 'Fully Paid'),

        ),

        default='pending'

    )

    

    # Timestamps

    generated_on = models.DateTimeField(auto_now_add=True)

    last_payment_on = models.DateTimeField(null=True, blank=True)

    

    class Meta:

        verbose_name = 'Salary'

        verbose_name_plural = 'Salary Records'

        ordering = ['-cycle_start_date']

    

    def __str__(self):

        return f"{self.employee.full_name} - {self.cycle_start_date.strftime('%d %b')} to {self.cycle_end_date.strftime('%d %b %Y')}"

    

    def get_total_salary(self):

        """Final salary + incentives"""

        return self.final_salary + self.incentive_amount



    def update_payment_status(self):

        """Update payment status based on total paid"""

        total_salary = self.get_total_salary()

        if self.total_paid >= total_salary:

            self.payment_status = 'completed'

            self.pending_amount = 0

        elif self.total_paid > 0:

            self.payment_status = 'partial'

            self.pending_amount = total_salary - self.total_paid

        else:

            self.payment_status = 'pending'

            self.pending_amount = total_salary

        self.save()





class SalaryPayment(models.Model):

    """

    Individual Salary Payment Record

    Tracks each payment made for a salary

    """

    salary = models.ForeignKey(Salary, on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_date = models.DateField()

    payment_method = models.CharField(

        max_length=50,

        choices=(

            ('cash', 'Cash'),

            ('bank_transfer', 'Bank Transfer'),

            ('cheque', 'Cheque'),

            ('upi', 'UPI'),

            ('other', 'Other'),

        ),

        default='bank_transfer'

    )

    reference_number = models.CharField(max_length=100, blank=True, help_text='Transaction ID / Cheque Number')

    notes = models.TextField(blank=True)

    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='salary_payments_made')

    created_at = models.DateTimeField(auto_now_add=True)

    

    class Meta:

        verbose_name = 'Salary Payment'

        verbose_name_plural = 'Salary Payments'

        ordering = ['-payment_date', '-created_at']

    

    def __str__(self):

        return f"₹{self.amount} - {self.salary.employee.full_name} - {self.payment_date}"

    

    def save(self, *args, **kwargs):

        """Update salary total_paid when payment is saved"""

        is_new = self.pk is None

        super().save(*args, **kwargs)

        

        if is_new:

            # Update salary total_paid

            self.salary.total_paid += self.amount

            self.salary.last_payment_on = self.created_at

            self.salary.update_payment_status()





class SalaryCycleSettings(models.Model):

    """

    Salary Cycle Configuration

    Defines when salary cycle starts and ends

    """

    cycle_start_day = models.IntegerField(

        default=10,

        help_text='Day of month when salary cycle starts (1-31)'

    )

    cycle_name = models.CharField(

        max_length=100,

        default='Monthly Salary Cycle',

        help_text='Name for this cycle configuration'

    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    

    class Meta:

        verbose_name = 'Salary Cycle Setting'

        verbose_name_plural = 'Salary Cycle Settings'

    

    def __str__(self):

        return f"{self.cycle_name} - Starts on {self.cycle_start_day}th"

    

    @classmethod

    def get_active_cycle(cls):

        """Get the active salary cycle settings"""

        return cls.objects.filter(is_active=True).first()

    

    def get_cycle_dates(self, reference_date=None):

        """

        Calculate cycle start and end dates based on reference date

        Example: If cycle_start_day = 10

        - Reference: 15 Feb 2026 → Cycle: 10 Feb to 9 Mar

        - Reference: 5 Feb 2026 → Cycle: 10 Jan to 9 Feb

        """

        from datetime import date, timedelta

        from dateutil.relativedelta import relativedelta

        

        if reference_date is None:

            reference_date = date.today()

        

        # If current day >= cycle_start_day, cycle is current month to next month

        if reference_date.day >= self.cycle_start_day:

            cycle_start = date(reference_date.year, reference_date.month, self.cycle_start_day)

            cycle_end = (cycle_start + relativedelta(months=1)) - timedelta(days=1)

        else:

            # If current day < cycle_start_day, cycle is previous month to current month

            cycle_start = date(reference_date.year, reference_date.month, self.cycle_start_day) - relativedelta(months=1)

            cycle_end = date(reference_date.year, reference_date.month, self.cycle_start_day) - timedelta(days=1)

        

        return cycle_start, cycle_end







class Incentive(models.Model):

    """

    Incentive Model

    Admin can add incentives to employees which get added to their salary

    """

    INCENTIVE_TYPE_CHOICES = (

        ('performance', 'Performance Bonus'),

        ('festival', 'Festival Bonus'),

        ('target', 'Target Achievement'),

        ('overtime', 'Overtime'),

        ('special', 'Special Allowance'),

        ('other', 'Other'),

    )



    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='incentives')

    incentive_type = models.CharField(max_length=20, choices=INCENTIVE_TYPE_CHOICES, default='performance')

    title = models.CharField(max_length=200, help_text='Short title for the incentive')

    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])

    incentive_date = models.DateField(help_text='Date of incentive')

    reason = models.TextField(blank=True, help_text='Reason / description')

    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='incentives_added')

    salary = models.ForeignKey(

        'Salary', on_delete=models.SET_NULL, null=True, blank=True,

        related_name='incentives', help_text='Linked salary record (auto-assigned)'

    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)



    class Meta:

        verbose_name = 'Incentive'

        verbose_name_plural = 'Incentives'

        ordering = ['-incentive_date', '-created_at']



    def __str__(self):

        return f"{self.employee.full_name} - {self.title} - ₹{self.amount}"





class Task(models.Model):
    """
    Task Model
    Admin assigns tasks to employees with deadline and priority
    """
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    STATUS_CHOICES = (
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(help_text='Detailed task description')
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks_assigned')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    deadline = models.DateField(null=True, blank=True)
    is_seen = models.BooleanField(default=False, help_text='Employee ne task dekha ya nahi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.assigned_to.full_name}"

    def get_unseen_logs_count(self):
        """Admin ke liye unseen work logs count"""
        return self.work_logs.filter(is_seen_by_admin=False).count()


class WorkLog(models.Model):
    """
    Work Log Model
    Employee daily work update bhejta hai admin ko
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='work_logs')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='work_logs')
    log_date = models.DateField(default=date.today)
    description = models.TextField(help_text='Aaj kya kiya - detailed update')
    hours_worked = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        help_text='Kitne ghante kaam kiya (optional)'
    )
    # Task proof photo - gallery ya live camera se
    photo = models.ImageField(
        upload_to='task_photos/',
        null=True, blank=True,
        help_text='Task ka proof photo (optional)'
    )
    is_seen_by_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Work Log'
        verbose_name_plural = 'Work Logs'
        ordering = ['-log_date', '-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.task.title} - {self.log_date}"


class Notification(models.Model):
    """
    In-App Notification Model
    Har user ke notifications store karta hai
    """
    NOTIF_TYPES = (
        ('task',    'New Task'),
        ('leave',   'Leave Update'),
        ('general', 'General'),
    )
    user       = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES, default='general')
    url        = models.CharField(max_length=200, blank=True, default='/')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.title}"


class PushSubscription(models.Model):
    """Web Push Notification Subscription"""
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='push_subscriptions'
    )
    endpoint = models.TextField(unique=True)
    p256dh   = models.TextField()
    auth     = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Push Subscription'
        verbose_name_plural = 'Push Subscriptions'

    def __str__(self):
        return f"{self.user.username} - push sub"


class Holiday(models.Model):

    """

    Holiday Management Model

    Manages company holidays (e.g., Republic Day, Diwali, etc.)

    """

    name = models.CharField(

        max_length=200,

        help_text='Holiday name (e.g., Republic Day, Diwali)'

    )

    start_date = models.DateField(

        help_text='Holiday start date'

    )

    end_date = models.DateField(

        help_text='Holiday end date (same as start for single day)'

    )

    description = models.TextField(

        blank=True,

        help_text='Optional description'

    )

    is_active = models.BooleanField(

        default=True,

        help_text='Is this holiday active?'

    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    

    class Meta:

        verbose_name = 'Holiday'

        verbose_name_plural = 'Holidays'

        ordering = ['-start_date']

    

    def __str__(self):

        if self.start_date == self.end_date:

            return f"{self.name} ({self.start_date})"

        return f"{self.name} ({self.start_date} to {self.end_date})"

    

    def get_total_days(self):

        """Calculate total holiday days"""

        delta = self.end_date - self.start_date

        return delta.days + 1

    

    @classmethod

    def is_holiday(cls, date_obj):

        """Check if a given date is a holiday"""

        return cls.objects.filter(

            start_date__lte=date_obj,

            end_date__gte=date_obj,

            is_active=True

        ).exists()

    

    @classmethod

    def get_holiday_dates(cls, year, month):

        """Get all holiday dates for a specific month"""

        from datetime import date, timedelta

        import calendar

        

        # Get first and last day of month

        first_day = date(year, month, 1)

        last_day = date(year, month, calendar.monthrange(year, month)[1])

        

        # Get all holidays that overlap with this month

        holidays = cls.objects.filter(

            is_active=True,

            start_date__lte=last_day,

            end_date__gte=first_day

        )

        

        # Collect all dates

        holiday_dates = set()

        for holiday in holidays:

            current_date = max(holiday.start_date, first_day)

            end_date = min(holiday.end_date, last_day)

            

            while current_date <= end_date:

                holiday_dates.add(current_date)

                current_date += timedelta(days=1)

        

        return holiday_dates


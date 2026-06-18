"""
Salary Management Views
Complete salary cycle and payment tracking
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

from .models import (
    Employee, Salary, SalaryPayment, SalaryCycleSettings,
    Attendance, Leave, WeekOff, Holiday, Incentive
)
from .forms import SalaryCycleSettingsForm, SalaryPaymentForm


# ==================== SALARY CYCLE SETTINGS ====================

@login_required
def salary_cycle_settings(request):
    """Manage salary cycle configuration"""
    if request.user.role != 'admin':
        return redirect('home')
    
    cycle_settings = SalaryCycleSettings.get_active_cycle()
    
    if request.method == 'POST':
        if cycle_settings:
            form = SalaryCycleSettingsForm(request.POST, instance=cycle_settings)
        else:
            form = SalaryCycleSettingsForm(request.POST)
        
        if form.is_valid():
            # Deactivate all other cycles
            SalaryCycleSettings.objects.all().update(is_active=False)
            
            # Save new/updated cycle
            cycle = form.save(commit=False)
            cycle.is_active = True
            cycle.save()
            
            messages.success(request, 'Salary cycle settings updated successfully!')
            return redirect('salary_cycle_settings')
    else:
        if cycle_settings:
            form = SalaryCycleSettingsForm(instance=cycle_settings)
        else:
            form = SalaryCycleSettingsForm()
    
    # Show current cycle dates
    if cycle_settings:
        cycle_start, cycle_end = cycle_settings.get_cycle_dates()
    else:
        cycle_start = cycle_end = None
    
    context = {
        'form': form,
        'cycle_settings': cycle_settings,
        'cycle_start': cycle_start,
        'cycle_end': cycle_end,
    }
    
    return render(request, 'admin/salary_cycle_settings.html', context)


# ==================== SALARY MANAGEMENT ====================

@login_required
def salary_management(request):
    """Main salary management dashboard"""
    if request.user.role != 'admin':
        return redirect('home')
    
    # Get cycle settings
    cycle_settings = SalaryCycleSettings.get_active_cycle()
    
    if not cycle_settings:
        messages.warning(request, 'Please configure salary cycle settings first!')
        return redirect('salary_cycle_settings')
    
    # Get cycle dates from request or use current
    if request.GET.get('cycle_start') and request.GET.get('cycle_end'):
        cycle_start = date.fromisoformat(request.GET['cycle_start'])
        cycle_end = date.fromisoformat(request.GET['cycle_end'])
    else:
        cycle_start, cycle_end = cycle_settings.get_cycle_dates()
    
    # Get all salary records for this cycle
    salaries = Salary.objects.filter(
        cycle_start_date=cycle_start,
        cycle_end_date=cycle_end
    ).select_related('employee').order_by('employee__employee_id')
    
    # Calculate totals
    total_payroll = sum(s.final_salary for s in salaries)
    total_paid = sum(s.total_paid for s in salaries)
    total_pending = sum(s.pending_amount for s in salaries)
    
    # Count by status
    pending_count = salaries.filter(payment_status='pending').count()
    partial_count = salaries.filter(payment_status='partial').count()
    completed_count = salaries.filter(payment_status='completed').count()
    
    context = {
        'cycle_settings': cycle_settings,
        'cycle_start': cycle_start,
        'cycle_end': cycle_end,
        'salaries': salaries,
        'total_payroll': total_payroll,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'pending_count': pending_count,
        'partial_count': partial_count,
        'completed_count': completed_count,
    }
    
    return render(request, 'admin/salary_management.html', context)


@login_required
def generate_salary_for_cycle(request):
    """Generate salary records for a specific cycle"""
    if request.user.role != 'admin':
        return redirect('home')
    
    if request.method == 'POST':
        cycle_start = date.fromisoformat(request.POST['cycle_start'])
        cycle_end = date.fromisoformat(request.POST['cycle_end'])
        
        employees = Employee.objects.filter(is_active=True)
        generated_count = 0
        updated_count = 0
        skipped_count = 0
        
        for emp in employees:
            # Check if already exists
            existing = Salary.objects.filter(
                employee=emp,
                cycle_start_date=cycle_start,
                cycle_end_date=cycle_end
            ).first()
            
            if existing and existing.payment_status == 'completed':
                skipped_count += 1
                continue
            
            # Calculate attendance for this cycle
            attendances = Attendance.objects.filter(
                employee=emp,
                date__gte=cycle_start,
                date__lte=cycle_end
            )
            
            # Count present days
            present_days = 0
            late_count = 0
            very_late_count = 0
            
            for att in attendances:
                if att.punch_in:
                    if emp.shift and att.is_late:
                        punch_in_time = att.punch_in.time()
                        shift_end_time = emp.shift.punch_in_end
                        
                        punch_in_datetime = datetime.combine(att.date, punch_in_time)
                        shift_end_datetime = datetime.combine(att.date, shift_end_time)
                        late_duration = punch_in_datetime - shift_end_datetime
                        
                        if late_duration >= timedelta(hours=1):
                            very_late_count += 1
                            present_days += 0.5
                        else:
                            late_count += 1
                            present_days += 1
                    else:
                        present_days += 1
            
            # Calculate penalties
            late_penalty_days = (late_count // 3) * 0.5
            
            # Count absents
            total_days = (cycle_end - cycle_start).days + 1
            attendance_dates = set(attendances.filter(punch_in__isnull=False).values_list('date', flat=True))
            
            # Get leave dates
            leave_dates = set()
            leaves = Leave.objects.filter(
                employee=emp,
                status='approved',
                start_date__lte=cycle_end,
                end_date__gte=cycle_start
            )
            
            approved_leaves = 0
            for leave in leaves:
                current_date = max(leave.start_date, cycle_start)
                end_date = min(leave.end_date, cycle_end)
                while current_date <= end_date:
                    leave_dates.add(current_date)
                    approved_leaves += 1
                    current_date += timedelta(days=1)
            
            # Count absents
            absent_days = 0
            current_date = cycle_start
            while current_date <= cycle_end:
                if not WeekOff.is_week_off(current_date) and not Holiday.is_holiday(current_date):
                    if current_date not in attendance_dates and current_date not in leave_dates:
                        absent_days += 1
                current_date += timedelta(days=1)
            
            absent_penalty_days = absent_days * 2
            
            # Calculate final salary
            effective_working_days = present_days - late_penalty_days - absent_penalty_days - approved_leaves
            if effective_working_days < 0:
                effective_working_days = 0
            
            per_day_salary = emp.base_salary / 30
            final_salary = Decimal(str(effective_working_days)) * per_day_salary
            
            if final_salary > emp.base_salary:
                final_salary = emp.base_salary
            
            deduction = emp.base_salary - final_salary
            
            if existing:
                # Update existing
                existing.base_salary = emp.base_salary
                existing.present_days = int(present_days)
                existing.approved_leaves = approved_leaves
                existing.total_working_days = int(effective_working_days)
                existing.per_day_salary = per_day_salary
                existing.final_salary = final_salary
                existing.deduction = deduction
                existing.pending_amount = final_salary - existing.total_paid
                existing.save()
                updated_count += 1
            else:
                # Create new
                Salary.objects.create(
                    employee=emp,
                    cycle_start_date=cycle_start,
                    cycle_end_date=cycle_end,
                    base_salary=emp.base_salary,
                    present_days=int(present_days),
                    approved_leaves=approved_leaves,
                    total_working_days=int(effective_working_days),
                    per_day_salary=per_day_salary,
                    final_salary=final_salary,
                    deduction=deduction,
                    incentive_amount=0,
                    total_paid=0,
                    pending_amount=final_salary,
                    payment_status='pending'
                )
                generated_count += 1
        
        messages.success(
            request,
            f'Salary generated! New: {generated_count}, Updated: {updated_count}, Skipped: {skipped_count}'
        )
        return redirect(f'/admin/salary-management/?cycle_start={cycle_start}&cycle_end={cycle_end}')
    
    return redirect('salary_management')


# ==================== PAYMENT MANAGEMENT ====================

@login_required
def salary_detail(request, salary_id):
    """View salary details with payment history"""
    if request.user.role != 'admin':
        return redirect('home')

    salary = get_object_or_404(Salary, pk=salary_id)
    payments = salary.payments.all().order_by('-payment_date', '-created_at')
    incentives = salary.incentives.all().order_by('-incentive_date')

    context = {
        'salary': salary,
        'payments': payments,
        'incentives': incentives,
    }

    return render(request, 'admin/salary_detail.html', context)


@login_required
def add_payment(request, salary_id):
    """Add a payment to salary"""
    if request.user.role != 'admin':
        return redirect('home')
    
    salary = get_object_or_404(Salary, pk=salary_id)
    
    if salary.payment_status == 'completed':
        messages.error(request, 'This salary is already fully paid!')
        return redirect('salary_detail', salary_id=salary_id)
    
    if request.method == 'POST':
        form = SalaryPaymentForm(request.POST, salary=salary)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.salary = salary
            payment.paid_by = request.user
            payment.save()
            
            messages.success(request, f'Payment of ₹{payment.amount} added successfully!')
            return redirect('salary_detail', salary_id=salary_id)
    else:
        form = SalaryPaymentForm(salary=salary)
    
    context = {
        'form': form,
        'salary': salary,
    }
    
    return render(request, 'admin/add_payment.html', context)


@login_required
def delete_payment(request, payment_id):
    """Delete a payment"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            payment = get_object_or_404(SalaryPayment, pk=payment_id)
            salary = payment.salary
            amount = payment.amount
            
            # Delete payment
            payment.delete()
            
            # Update salary totals
            salary.total_paid -= amount
            if salary.total_paid < 0:
                salary.total_paid = 0
            salary.update_payment_status()
            
            return JsonResponse({
                'success': True,
                'message': f'Payment of ₹{amount} deleted successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)

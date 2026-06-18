"""
Incentive Management Views
Admin can add incentives to employees - they get added to salary automatically
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import date

from .models import Employee, Incentive, Salary, SalaryCycleSettings
from .forms import IncentiveForm


def _link_incentive_to_salary(incentive):
    """
    Auto-link incentive to the salary record whose cycle covers incentive_date.
    Also updates salary.incentive_amount and pending_amount.
    """
    cycle_settings = SalaryCycleSettings.get_active_cycle()
    if not cycle_settings:
        return

    # Find salary record for this employee that covers the incentive date
    salary = Salary.objects.filter(
        employee=incentive.employee,
        cycle_start_date__lte=incentive.incentive_date,
        cycle_end_date__gte=incentive.incentive_date,
    ).first()

    if salary:
        incentive.salary = salary
        incentive.save(update_fields=['salary'])
        # Recalculate incentive_amount for that salary
        _recalculate_salary_incentive(salary)


def _recalculate_salary_incentive(salary):
    """Sum all incentives linked to a salary and update salary fields."""
    total_incentive = salary.incentives.aggregate(total=Sum('amount'))['total'] or 0
    salary.incentive_amount = total_incentive
    # Recalculate pending
    total_salary = salary.final_salary + salary.incentive_amount
    if salary.total_paid >= total_salary:
        salary.payment_status = 'completed'
        salary.pending_amount = 0
    elif salary.total_paid > 0:
        salary.payment_status = 'partial'
        salary.pending_amount = total_salary - salary.total_paid
    else:
        salary.payment_status = 'pending'
        salary.pending_amount = total_salary
    salary.save()


# ==================== INCENTIVE LIST ====================

@login_required
def incentive_list(request):
    """List all incentives with filter by employee"""
    if request.user.role != 'admin':
        return redirect('home')

    employee_id = request.GET.get('employee')
    incentives = Incentive.objects.select_related('employee', 'added_by').order_by('-incentive_date', '-created_at')

    employees = Employee.objects.filter(is_active=True).order_by('employee_id')
    selected_employee = None

    if employee_id:
        incentives = incentives.filter(employee__id=employee_id)
        selected_employee = get_object_or_404(Employee, pk=employee_id)

    total_incentive = incentives.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'incentives': incentives,
        'employees': employees,
        'selected_employee': selected_employee,
        'total_incentive': total_incentive,
    }
    return render(request, 'admin/incentive_list.html', context)


# ==================== ADD INCENTIVE ====================

@login_required
def incentive_add(request):
    """Add a new incentive for an employee"""
    if request.user.role != 'admin':
        return redirect('home')

    # Pre-select employee if passed via GET
    initial = {}
    emp_id = request.GET.get('employee')
    if emp_id:
        try:
            initial['employee'] = Employee.objects.get(pk=emp_id)
        except Employee.DoesNotExist:
            pass

    if request.method == 'POST':
        form = IncentiveForm(request.POST)
        if form.is_valid():
            incentive = form.save(commit=False)
            incentive.added_by = request.user
            incentive.save()
            # Auto-link to salary
            _link_incentive_to_salary(incentive)
            messages.success(
                request,
                f'Incentive of ₹{incentive.amount} added for {incentive.employee.full_name}!'
            )
            return redirect('incentive_list')
    else:
        form = IncentiveForm(initial=initial)

    context = {'form': form, 'title': 'Add Incentive'}
    return render(request, 'admin/incentive_form.html', context)


# ==================== EDIT INCENTIVE ====================

@login_required
def incentive_edit(request, pk):
    """Edit an existing incentive"""
    if request.user.role != 'admin':
        return redirect('home')

    incentive = get_object_or_404(Incentive, pk=pk)
    old_salary = incentive.salary  # keep reference to recalculate old salary

    if request.method == 'POST':
        form = IncentiveForm(request.POST, instance=incentive)
        if form.is_valid():
            incentive = form.save(commit=False)
            incentive.added_by = request.user
            incentive.save()
            # Recalculate old salary if salary changed
            if old_salary and old_salary != incentive.salary:
                _recalculate_salary_incentive(old_salary)
            _link_incentive_to_salary(incentive)
            messages.success(request, 'Incentive updated successfully!')
            return redirect('incentive_list')
    else:
        form = IncentiveForm(instance=incentive)

    context = {'form': form, 'title': 'Edit Incentive', 'incentive': incentive}
    return render(request, 'admin/incentive_form.html', context)


# ==================== DELETE INCENTIVE ====================

@login_required
def incentive_delete(request, pk):
    """Delete an incentive"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            incentive = get_object_or_404(Incentive, pk=pk)
            salary = incentive.salary
            amount = incentive.amount
            emp_name = incentive.employee.full_name
            incentive.delete()
            # Recalculate salary incentive
            if salary:
                _recalculate_salary_incentive(salary)
            return JsonResponse({
                'success': True,
                'message': f'Incentive of ₹{amount} for {emp_name} deleted.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)


# ==================== EMPLOYEE INCENTIVES (for salary detail) ====================

@login_required
def employee_incentives(request, employee_id):
    """View all incentives for a specific employee"""
    if request.user.role != 'admin':
        return redirect('home')

    employee = get_object_or_404(Employee, pk=employee_id)
    incentives = Incentive.objects.filter(employee=employee).order_by('-incentive_date')
    total = incentives.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'employee': employee,
        'incentives': incentives,
        'total': total,
    }
    return render(request, 'admin/employee_incentives.html', context)

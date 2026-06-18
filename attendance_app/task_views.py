"""
Task Management Views
Admin assigns tasks, employees submit daily work logs
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count

from .models import Employee, Task, WorkLog
from .forms import TaskForm, WorkLogForm


# ==================== ADMIN VIEWS ====================

@login_required
def admin_task_list(request):
    """Admin: Saare tasks dekho with filters"""
    if request.user.role != 'admin':
        return redirect('home')

    status_filter = request.GET.get('status', '')
    employee_filter = request.GET.get('employee', '')
    priority_filter = request.GET.get('priority', '')

    tasks = Task.objects.select_related('assigned_to', 'assigned_by').prefetch_related('work_logs')

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if employee_filter:
        tasks = tasks.filter(assigned_to__id=employee_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    # Stats
    total = Task.objects.count()
    assigned_count = Task.objects.filter(status='assigned').count()
    in_progress_count = Task.objects.filter(status='in_progress').count()
    completed_count = Task.objects.filter(status='completed').count()

    # Unseen work logs count for badge
    unseen_logs = WorkLog.objects.filter(is_seen_by_admin=False).count()

    employees = Employee.objects.filter(is_active=True).order_by('employee_id')

    context = {
        'tasks': tasks,
        'employees': employees,
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'priority_filter': priority_filter,
        'total': total,
        'assigned_count': assigned_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'unseen_logs': unseen_logs,
    }
    return render(request, 'admin/task_list.html', context)


@login_required
def admin_task_create(request):
    """Admin: Naya task create karo aur employee ko assign karo"""
    if request.user.role != 'admin':
        return redirect('home')

    # Pre-select employee if passed in GET
    initial = {}
    emp_id = request.GET.get('employee')
    if emp_id:
        try:
            initial['assigned_to'] = Employee.objects.get(pk=emp_id)
        except Employee.DoesNotExist:
            pass

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.status = 'assigned'
            task.is_seen = False
            task.save()
            # Send push notification to employee
            try:
                from .push_views import send_push_to_employee
                send_push_to_employee(
                    task.assigned_to,
                    title=f'📋 Naya Task Mila!',
                    body=f'"{task.title}" — {task.get_priority_display()} priority',
                    url=f'/employee/tasks/{task.pk}/'
                )
            except Exception:
                pass
            messages.success(request, f'Task "{task.title}" successfully assigned to {task.assigned_to.full_name}!')
            return redirect('admin_task_list')
    else:
        form = TaskForm(initial=initial)

    context = {'form': form, 'title': 'Assign New Task'}
    return render(request, 'admin/task_form.html', context)


@login_required
def admin_task_edit(request, pk):
    """Admin: Task edit karo"""
    if request.user.role != 'admin':
        return redirect('home')

    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('admin_task_list')
    else:
        form = TaskForm(instance=task)

    context = {'form': form, 'title': 'Edit Task', 'task': task}
    return render(request, 'admin/task_form.html', context)


@login_required
def admin_task_delete(request, pk):
    """Admin: Task delete karo"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            task = get_object_or_404(Task, pk=pk)
            title = task.title
            task.delete()
            return JsonResponse({'success': True, 'message': f'Task "{title}" deleted.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)


@login_required
def admin_task_detail(request, pk):
    """Admin: Task detail + saare work logs dekho"""
    if request.user.role != 'admin':
        return redirect('home')

    task = get_object_or_404(Task, pk=pk)
    work_logs = task.work_logs.select_related('employee').order_by('-log_date', '-created_at')

    # Mark all work logs as seen by admin
    task.work_logs.filter(is_seen_by_admin=False).update(is_seen_by_admin=True)

    # Status update from admin
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['assigned', 'in_progress', 'completed']:
            task.status = new_status
            task.save()
            messages.success(request, f'Task status updated to {task.get_status_display()}!')
            return redirect('admin_task_detail', pk=pk)

    context = {
        'task': task,
        'work_logs': work_logs,
    }
    return render(request, 'admin/task_detail.html', context)


@login_required
def admin_work_logs(request):
    """Admin: Saare employees ke work logs ek jagah dekho"""
    if request.user.role != 'admin':
        return redirect('home')

    employee_filter = request.GET.get('employee', '')
    logs = WorkLog.objects.select_related('employee', 'task').order_by('-log_date', '-created_at')

    if employee_filter:
        logs = logs.filter(employee__id=employee_filter)

    # Mark as seen
    logs.filter(is_seen_by_admin=False).update(is_seen_by_admin=True)

    employees = Employee.objects.filter(is_active=True).order_by('employee_id')

    context = {
        'logs': logs,
        'employees': employees,
        'employee_filter': employee_filter,
    }
    return render(request, 'admin/work_logs.html', context)


# ==================== EMPLOYEE VIEWS ====================

@login_required
def employee_task_list(request):
    """Employee: Apne saare assigned tasks dekho"""
    if request.user.role != 'employee':
        return redirect('home')

    try:
        employee = request.user.employee_profile
    except Exception:
        return redirect('home')

    tasks = Task.objects.filter(assigned_to=employee).order_by('-created_at')

    # Mark all tasks as seen (notification clear)
    unseen_tasks = tasks.filter(is_seen=False)
    unseen_count = unseen_tasks.count()
    unseen_tasks.update(is_seen=True)

    context = {
        'tasks': tasks,
        'unseen_count': unseen_count,
    }
    return render(request, 'employee/task_list.html', context)


@login_required
def employee_task_detail(request, pk):
    """Employee: Task detail dekho aur work log submit karo"""
    if request.user.role != 'employee':
        return redirect('home')

    try:
        employee = request.user.employee_profile
    except Exception:
        return redirect('home')

    task = get_object_or_404(Task, pk=pk, assigned_to=employee)

    # Mark task as seen
    if not task.is_seen:
        task.is_seen = True
        task.save(update_fields=['is_seen'])

    work_logs = task.work_logs.filter(employee=employee).order_by('-log_date')

    if request.method == 'POST':
        form = WorkLogForm(request.POST, request.FILES)
        if form.is_valid():
            log = form.save(commit=False)
            log.task = task
            log.employee = employee
            # Live camera se aaya base64 image handle karo
            camera_data = request.POST.get('camera_photo_data', '').strip()
            if camera_data and not form.cleaned_data.get('photo'):
                import base64
                from django.core.files.base import ContentFile
                from django.utils import timezone as tz
                import re
                # data:image/jpeg;base64,.... strip karo
                match = re.match(r'data:image/(\w+);base64,(.*)', camera_data, re.DOTALL)
                if match:
                    ext = match.group(1)
                    img_data = base64.b64decode(match.group(2))
                    filename = f"task_{task.pk}_emp_{employee.pk}_{tz.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                    log.photo.save(filename, ContentFile(img_data), save=False)
            log.save()
            # Auto update task status to in_progress if it was just assigned
            if task.status == 'assigned':
                task.status = 'in_progress'
                task.save(update_fields=['status'])
            messages.success(request, 'Work log submit ho gaya!')
            return redirect('employee_task_detail', pk=pk)
    else:
        form = WorkLogForm()

    context = {
        'task': task,
        'work_logs': work_logs,
        'form': form,
    }
    return render(request, 'employee/task_detail.html', context)


@login_required
def employee_task_status_update(request, pk):
    """Employee: Task status update karo (In Progress / Completed)"""
    if request.user.role != 'employee':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        employee = request.user.employee_profile
    except Exception:
        return JsonResponse({'success': False, 'error': 'Employee not found'}, status=400)

    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk, assigned_to=employee)
        new_status = request.POST.get('status')
        if new_status in ['in_progress', 'completed']:
            task.status = new_status
            task.save(update_fields=['status'])
            return JsonResponse({'success': True, 'status': task.get_status_display()})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)


# ==================== API: Unseen task count for navbar badge ====================

@login_required
def get_unseen_task_count(request):
    """Employee ke liye unseen task count return karo (navbar badge ke liye)"""
    if request.user.role != 'employee':
        return JsonResponse({'count': 0})
    try:
        employee = request.user.employee_profile
        count = Task.objects.filter(assigned_to=employee, is_seen=False).count()
        return JsonResponse({'count': count})
    except Exception:
        return JsonResponse({'count': 0})

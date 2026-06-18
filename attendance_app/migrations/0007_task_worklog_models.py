from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('attendance_app', '0006_incentive_salary_incentive_amount'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(help_text='Detailed task description')),
                ('priority', models.CharField(
                    choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')],
                    default='medium', max_length=10
                )),
                ('status', models.CharField(
                    choices=[('assigned', 'Assigned'), ('in_progress', 'In Progress'), ('completed', 'Completed')],
                    default='assigned', max_length=20
                )),
                ('deadline', models.DateField(blank=True, null=True)),
                ('is_seen', models.BooleanField(default=False, help_text='Employee ne task dekha ya nahi')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tasks_assigned',
                    to=settings.AUTH_USER_MODEL
                )),
                ('assigned_to', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tasks',
                    to='attendance_app.employee'
                )),
            ],
            options={
                'verbose_name': 'Task',
                'verbose_name_plural': 'Tasks',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('log_date', models.DateField(default=datetime.date.today)),
                ('description', models.TextField(help_text='Aaj kya kiya - detailed update')),
                ('hours_worked', models.DecimalField(
                    blank=True, decimal_places=1, max_digits=4, null=True,
                    help_text='Kitne ghante kaam kiya (optional)'
                )),
                ('is_seen_by_admin', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='work_logs',
                    to='attendance_app.employee'
                )),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='work_logs',
                    to='attendance_app.task'
                )),
            ],
            options={
                'verbose_name': 'Work Log',
                'verbose_name_plural': 'Work Logs',
                'ordering': ['-log_date', '-created_at'],
            },
        ),
    ]

# Generated migration for new salary system

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attendance_app', '0004_holiday'),
    ]

    operations = [
        # Create SalaryCycleSettings model first
        migrations.CreateModel(
            name='SalaryCycleSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cycle_start_day', models.IntegerField(default=10, help_text='Day of month when salary cycle starts (1-31)')),
                ('cycle_name', models.CharField(default='Monthly Salary Cycle', help_text='Name for this cycle configuration', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Salary Cycle Setting',
                'verbose_name_plural': 'Salary Cycle Settings',
            },
        ),
        
        # Create SalaryPayment model
        migrations.CreateModel(
            name='SalaryPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateField()),
                ('payment_method', models.CharField(
                    choices=[
                        ('cash', 'Cash'),
                        ('bank_transfer', 'Bank Transfer'),
                        ('cheque', 'Cheque'),
                        ('upi', 'UPI'),
                        ('other', 'Other')
                    ],
                    default='bank_transfer',
                    max_length=50
                )),
                ('reference_number', models.CharField(blank=True, help_text='Transaction ID / Cheque Number', max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='salary_payments_made', to=settings.AUTH_USER_MODEL)),
                ('salary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='attendance_app.salary')),
            ],
            options={
                'verbose_name': 'Salary Payment',
                'verbose_name_plural': 'Salary Payments',
                'ordering': ['-payment_date', '-created_at'],
            },
        ),
        
        # Add new fields to Salary (before removing old ones)
        migrations.AddField(
            model_name='salary',
            name='cycle_start_date',
            field=models.DateField(help_text='Salary cycle start date (e.g., 10th of month)', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='salary',
            name='cycle_end_date',
            field=models.DateField(help_text='Salary cycle end date (e.g., 9th of next month)', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='salary',
            name='total_paid',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Total amount paid so far', max_digits=10),
        ),
        migrations.AddField(
            model_name='salary',
            name='pending_amount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Remaining amount to be paid', max_digits=10),
        ),
        migrations.AddField(
            model_name='salary',
            name='payment_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('partial', 'Partially Paid'), ('completed', 'Fully Paid')],
                default='pending',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='salary',
            name='last_payment_on',
            field=models.DateTimeField(null=True, blank=True),
        ),
        
        # Remove unique_together constraint first
        migrations.AlterUniqueTogether(
            name='salary',
            unique_together=set(),
        ),
        
        # Now remove old fields
        migrations.RemoveField(
            model_name='salary',
            name='month',
        ),
        migrations.RemoveField(
            model_name='salary',
            name='year',
        ),
        migrations.RemoveField(
            model_name='salary',
            name='paid',
        ),
        migrations.RemoveField(
            model_name='salary',
            name='paid_on',
        ),
        
        # Update ordering
        migrations.AlterModelOptions(
            name='salary',
            options={'ordering': ['-cycle_start_date'], 'verbose_name': 'Salary', 'verbose_name_plural': 'Salary Records'},
        ),
    ]

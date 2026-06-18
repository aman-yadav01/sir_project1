from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attendance_app', '0005_salary_system_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='salary',
            name='incentive_amount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Total incentive added to this salary', max_digits=10),
        ),
        migrations.CreateModel(
            name='Incentive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('incentive_type', models.CharField(
                    choices=[
                        ('performance', 'Performance Bonus'),
                        ('festival', 'Festival Bonus'),
                        ('target', 'Target Achievement'),
                        ('overtime', 'Overtime'),
                        ('special', 'Special Allowance'),
                        ('other', 'Other'),
                    ],
                    default='performance',
                    max_length=20,
                )),
                ('title', models.CharField(help_text='Short title for the incentive', max_length=200)),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    max_digits=10,
                    validators=[django.core.validators.MinValueValidator(1)],
                )),
                ('incentive_date', models.DateField(help_text='Date of incentive')),
                ('reason', models.TextField(blank=True, help_text='Reason / description')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('added_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='incentives_added',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='incentives',
                    to='attendance_app.employee',
                )),
                ('salary', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='incentives',
                    to='attendance_app.salary',
                )),
            ],
            options={
                'verbose_name': 'Incentive',
                'verbose_name_plural': 'Incentives',
                'ordering': ['-incentive_date', '-created_at'],
            },
        ),
    ]

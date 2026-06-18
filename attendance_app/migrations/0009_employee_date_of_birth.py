from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance_app', '0008_worklog_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='date_of_birth',
            field=models.DateField(
                blank=True,
                null=True,
                help_text='Date of birth'
            ),
        ),
    ]

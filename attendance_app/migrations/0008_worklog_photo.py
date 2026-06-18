from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance_app', '0007_task_worklog_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='worklog',
            name='photo',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='task_photos/',
                help_text='Task ka proof photo (optional)'
            ),
        ),
    ]

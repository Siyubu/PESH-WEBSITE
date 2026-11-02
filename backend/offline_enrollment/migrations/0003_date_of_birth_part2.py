import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("offline_enrollment", "0002_date_of_birth_part1")]

    operations = [
        migrations.AlterField(model_name="offlinelearner", name="date_of_birth", field=models.DateField()),
        migrations.RemoveField(model_name="offlinelearner", name="age"),
        migrations.AlterField(
            model_name="offlinelearner",
            name="grade",
            field=models.CharField(blank=True, help_text="e.g. P5, S3. Required when the learner is a student.", max_length=50),
        ),
        migrations.AddField(
            model_name="offlinelearner",
            name="client_updated_at",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                help_text="When the phone last edited this record. A sync only overwrites the server copy if it is newer.",
            ),
        ),
    ]

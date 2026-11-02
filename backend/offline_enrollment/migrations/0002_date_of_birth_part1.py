from datetime import date

from django.db import migrations, models


def estimate_date_of_birth(apps, schema_editor):
    """Old rows only stored an age. Estimate 1 January of the birth year; staff can correct it in the admin or app."""
    Learner = apps.get_model("offline_enrollment", "OfflineLearner")
    for learner in Learner.objects.all():
        learner.date_of_birth = date(learner.created_at.year - learner.age, 1, 1)
        learner.save(update_fields=["date_of_birth"])


class Migration(migrations.Migration):

    dependencies = [("offline_enrollment", "0001_initial")]

    operations = [
        migrations.AddField(model_name="offlinelearner", name="date_of_birth", field=models.DateField(null=True)),
        migrations.RunPython(estimate_date_of_birth, migrations.RunPython.noop),
    ]

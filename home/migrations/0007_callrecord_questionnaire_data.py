from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0006_auditlog_sessionsnapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="callrecord",
            name="questionnaire_data",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]


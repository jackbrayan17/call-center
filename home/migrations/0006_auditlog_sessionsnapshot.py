from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('home', '0005_recording_mime_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('method', models.CharField(max_length=8)),
                ('path', models.TextField()),
                ('status_code', models.PositiveSmallIntegerField()),
                ('user_agent', models.TextField(blank=True)),
                ('duration_ms', models.PositiveIntegerField(default=0)),
                ('payload_summary', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SessionSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(max_length=64, unique=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('login_at', models.DateTimeField()),
                ('last_activity', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='session_snapshots', to='auth.user')),
            ],
            options={
                'ordering': ['-last_activity'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['created_at'], name='home_audit_created_4e2897_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['path'], name='home_audit_path_0bcc51_idx'),
        ),
        migrations.AddIndex(
            model_name='sessionsnapshot',
            index=models.Index(fields=['last_activity'], name='home_sessio_last_ac_07acc7_idx'),
        ),
        migrations.AddIndex(
            model_name='sessionsnapshot',
            index=models.Index(fields=['session_key'], name='home_sessio_session_b2cd2a_idx'),
        ),
    ]

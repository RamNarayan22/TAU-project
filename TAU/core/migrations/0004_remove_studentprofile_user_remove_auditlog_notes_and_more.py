# Generated by Django 5.2.1 on 2025-05-28 09:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_departmentprofile_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentprofile',
            name='user',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='user',
        ),
        migrations.RemoveField(
            model_name='complaint',
            name='sla_due',
        ),
        migrations.RemoveField(
            model_name='complaint',
            name='title',
        ),
        migrations.AddField(
            model_name='auditlog',
            name='performed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='complaint',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='core.complaint'),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Resolved', 'Resolved'), ('Rejected', 'Rejected')], default='Pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='ticket_id',
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_admin', models.BooleanField(default=False)),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.department')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='DepartmentProfile',
        ),
        migrations.DeleteModel(
            name='StudentProfile',
        ),
    ]

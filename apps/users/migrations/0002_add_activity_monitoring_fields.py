# Generated by Django 5.1.6 on 2025-02-27 14:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="failed_login_attempts",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="last_failed_login",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

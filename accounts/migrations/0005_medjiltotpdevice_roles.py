# Generated by Django 4.1.9 on 2024-04-29 03:47

import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("otp_totp", "0003_add_timestamps"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("accounts", "0004_load_report_notes"),
    ]

    operations = [
        migrations.CreateModel(
            name="MedjilTOTPDevice",
            fields=[
                (
                    "totpdevice_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="otp_totp.totpdevice",
                    ),
                ),
                ("session_key", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "abstract": False,
            },
            bases=("otp_totp.totpdevice",),
        ),
        migrations.CreateModel(
            name="Roles",
            fields=[],
            options={
                "verbose_name": "Roles",
                "verbose_name_plural": "Roles",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("auth.group",),
            managers=[
                ("objects", django.contrib.auth.models.GroupManager()),
            ],
        ),
    ]
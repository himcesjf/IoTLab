# Generated by Django 5.0.2 on 2025-05-21 10:05

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("devices", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnomalyDetection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("critical", "Critical"),
                        ],
                        max_length=20,
                    ),
                ),
                ("description", models.TextField()),
                ("data", models.JSONField()),
                ("resolved", models.BooleanField(default=False)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="devices.device"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Telemetry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("data", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="devices.device"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Telemetry",
                "indexes": [
                    models.Index(
                        fields=["device", "timestamp"],
                        name="telemetry_t_device__68496d_idx",
                    ),
                    models.Index(
                        fields=["timestamp"], name="telemetry_t_timesta_e8cd0f_idx"
                    ),
                ],
            },
        ),
    ]

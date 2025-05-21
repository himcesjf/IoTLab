from django.db import models
from django.utils import timezone
from telemetrix_lab.ingest_api.devices.models import Device

class Telemetry(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Telemetry"
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Telemetry for {self.device.name} at {self.timestamp}"

class AnomalyDetection(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    data = models.JSONField()
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Anomaly for {self.device.name} at {self.timestamp}"

    def resolve(self):
        self.resolved = True
        self.resolved_at = timezone.now()
        self.save(update_fields=['resolved', 'resolved_at']) 
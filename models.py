import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_timescaledb.models import TimescaleModel

from telemetrix_lab.ingest_api.devices.models import Device


class DeviceType(models.Model):
    """Model representing types of IoT devices."""
    
    name = models.CharField(_("Device Type"), max_length=50, unique=True)
    description = models.TextField(_("Description"), blank=True)
    schema = models.JSONField(_("Data Schema"), 
                             help_text=_("JSON schema defining the device data structure"))
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Device Type")
        verbose_name_plural = _("Device Types")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Device(models.Model):
    """Model representing individual IoT devices."""
    
    STATUS_CHOICES = [
        ('online', _('Online')),
        ('offline', _('Offline')),
        ('maintenance', _('Maintenance')),
        ('error', _('Error')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Device Name"), max_length=100)
    device_type = models.ForeignKey(
        DeviceType, 
        on_delete=models.CASCADE,
        related_name='devices'
    )
    status = models.CharField(
        _("Status"), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default='offline'
    )
    location = models.CharField(_("Location"), max_length=100, blank=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    
    last_seen = models.DateTimeField(_("Last Seen"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        ordering = ['name']
        indexes = [
            models.Index(fields=['device_type']),
            models.Index(fields=['status']),
            models.Index(fields=['last_seen']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.id})"
    
    def update_last_seen(self):
        """Update the last_seen timestamp to current time."""
        from django.utils import timezone
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class DeviceConfig(models.Model):
    """Model for storing device configuration parameters."""
    
    device = models.OneToOneField(
        Device, 
        on_delete=models.CASCADE,
        related_name='config'
    )
    config = models.JSONField(_("Configuration"), default=dict)
    
    publishing_interval = models.PositiveIntegerField(
        _("Publishing Interval (seconds)"), 
        default=60
    )
    failure_rate = models.FloatField(
        _("Simulated Failure Rate"),
        default=0.01,
        help_text=_("Probability of failure (0-1)")
    )
    noise_factor = models.FloatField(
        _("Noise Factor"),
        default=0.05,
        help_text=_("Amount of noise to add to simulated data (0-1)")
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Device Configuration")
        verbose_name_plural = _("Device Configurations")
    
    def __str__(self):
        return f"Config for {self.device.name}"


class Telemetry(TimescaleModel):
    """
    Model for storing telemetry data from IoT devices.
    Uses TimescaleDB for efficient time-series data storage.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        Device, 
        on_delete=models.CASCADE,
        related_name='telemetry'
    )
    timestamp = models.DateTimeField(_("Timestamp"), db_index=True)
    data = models.JSONField(_("Telemetry Data"))
    
    class Meta:
        verbose_name = _("Telemetry")
        verbose_name_plural = _("Telemetry")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Telemetry from {self.device.name} at {self.timestamp}"


class AnomalyDetection(models.Model):
    """Model for storing anomaly detection results."""
    
    SEVERITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]
    
    telemetry = models.ForeignKey(
        Telemetry,
        on_delete=models.CASCADE,
        related_name='anomalies'
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='anomalies'
    )
    timestamp = models.DateTimeField(_("Detection Time"), auto_now_add=True)
    severity = models.CharField(
        _("Severity"), 
        max_length=10, 
        choices=SEVERITY_CHOICES,
        default='medium'
    )
    description = models.TextField(_("Description"))
    anomaly_data = models.JSONField(_("Anomaly Data"), blank=True, default=dict)
    acknowledged = models.BooleanField(_("Acknowledged"), default=False)
    
    class Meta:
        verbose_name = _("Anomaly Detection")
        verbose_name_plural = _("Anomaly Detections")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['severity']),
            models.Index(fields=['acknowledged']),
        ]
    
    def __str__(self):
        return f"{self.severity.upper()} anomaly for {self.device.name} at {self.timestamp}"


class Notification(models.Model):
    """Model for storing notification events."""
    
    TYPE_CHOICES = [
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('push', _('Push Notification')),
        ('slack', _('Slack')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
    ]
    
    anomaly = models.ForeignKey(
        AnomalyDetection,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        _("Notification Type"), 
        max_length=10, 
        choices=TYPE_CHOICES
    )
    recipient = models.CharField(_("Recipient"), max_length=255)
    subject = models.CharField(_("Subject"), max_length=255)
    message = models.TextField(_("Message"))
    status = models.CharField(
        _("Status"), 
        max_length=10, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    sent_at = models.DateTimeField(_("Sent At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.device.name}" 
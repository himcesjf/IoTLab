import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.utils import timezone
from django.db.models import Count, Avg, Max
from django.contrib.auth.decorators import login_required

from telemetrix_lab.ingest_api.devices.models import Device, DeviceType
from telemetrix_lab.ingest_api.telemetry.models import Telemetry, AnomalyDetection


def index(request):
    return render(request, 'index.html')


def device_list(request):
    """View for listing all devices with filtering options."""
    # Get query parameters for filtering
    device_type = request.GET.get('type')
    status = request.GET.get('status')
    location = request.GET.get('location')
    
    # Build the queryset with filters
    devices = Device.objects.select_related('device_type').all()
    
    if device_type:
        devices = devices.filter(device_type__name=device_type)
    if status:
        devices = devices.filter(status=status)
    if location:
        # Filter location from metadata
        devices = devices.filter(metadata__location=location)
    
    # Order by last_seen
    devices = devices.order_by('-last_seen')
    
    # Get unique filter options for the UI
    device_types = DeviceType.objects.all()
    status_choices = [choice[0] for choice in Device.STATUS_CHOICES]
    # Get unique locations from metadata
    locations = Device.objects.values_list('metadata__location', flat=True).distinct()
    
    context = {
        'devices': devices,
        'device_types': device_types,
        'status_choices': status_choices,
        'locations': locations,
        'active_filters': {
            'type': device_type,
            'status': status,
            'location': location,
        }
    }
    
    return render(request, 'dashboard/device_list.html', context)


def device_detail(request, device_id):
    device = Device.objects.get(id=device_id)
    return render(request, 'devices/detail.html', {'device': device})


def anomaly_list(request):
    return render(request, 'anomalies/list.html')


def telemetry_stream(request):
    """
    Server-Sent Events endpoint for streaming telemetry updates to the dashboard.
    Used with EventSource in the browser.
    """
    def event_stream():
        """Generator for SSE events."""
        yield "data: connected\n\n"
        
        # This implementation uses Server-Sent Events (SSE) to stream real-time updates.
        # In a production environment, this would be integrated with:
        # 1. Django Channels for WebSocket support
        # 2. Redis as a message broker
        # 3. MQTT client for IoT device communication
        # For now, we're sending a heartbeat every 30 seconds to maintain the connection.
        while True:
            # Wait for 30 seconds
            yield "event: heartbeat\ndata: {}\n\n"
            
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable Nginx buffering
    return response


def index(request):
    """Main dashboard view showing high-level system metrics."""
    # Count active devices by type
    device_types = DeviceType.objects.annotate(
        device_count=Count('devices')
    ).values('name', 'device_count')
    
    # Get recent anomaly counts
    recent_time = timezone.now() - timedelta(hours=24)
    anomaly_count = AnomalyDetection.objects.filter(
        timestamp__gte=recent_time
    ).count()
    critical_anomalies = AnomalyDetection.objects.filter(
        timestamp__gte=recent_time,
        severity='critical'
    ).count()
    
    # Calculate device status counts
    devices_total = Device.objects.count()
    status_counts = Device.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Calculate online vs not online devices
    active_devices = Device.objects.filter(
        status='online'
    ).count()
    inactive_devices = devices_total - active_devices
    
    # Get recent telemetry count
    telemetry_count = Telemetry.objects.filter(
        timestamp__gte=recent_time
    ).count()
    
    # Get the most recent anomalies
    recent_anomalies = AnomalyDetection.objects.select_related('device').order_by(
        '-timestamp'
    )[:5]
    
    context = {
        'device_types': device_types,
        'anomaly_count': anomaly_count,
        'critical_anomalies': critical_anomalies,
        'active_devices': active_devices,
        'inactive_devices': inactive_devices,
        'status_counts': status_counts,
        'devices_total': devices_total,
        'telemetry_count': telemetry_count,
        'recent_anomalies': recent_anomalies,
    }
    
    return render(request, 'dashboard/index.html', context)


def device_detail(request, device_id):
    """Detailed view for a specific device."""
    device = get_object_or_404(Device.objects.select_related('device_type'), id=device_id)
    
    # Get time range from query parameters
    hours = request.GET.get('hours', 24)
    try:
        hours = int(hours)
    except ValueError:
        hours = 24  # Default to 24 hours if invalid
    
    time_range = timezone.now() - timedelta(hours=hours)
    
    # Get recent telemetry for this device
    telemetry = Telemetry.objects.filter(
        device=device,
        timestamp__gte=time_range
    ).order_by('-timestamp')[:100]
    
    # Get recent anomalies for this device
    anomalies = AnomalyDetection.objects.filter(
        device=device,
        timestamp__gte=time_range
    ).order_by('-timestamp')
    
    # Prepare telemetry data for charts
    telemetry_data = {}
    timestamps = []
    
    # Determine what fields we need to extract based on device type
    if device.device_type.name == 'temperature':
        fields = ['temperature', 'humidity', 'battery']
    elif device.device_type.name == 'vibration':
        fields = ['velocity_rms', 'frequency', 'temperature']
    elif device.device_type.name == 'flow':
        fields = ['flow_rate', 'pressure', 'temperature']
    else:
        fields = []
    
    # Initialize data structure
    for field in fields:
        telemetry_data[field] = []
    
    # Extract telemetry data
    for item in reversed(telemetry):  # Reverse to get chronological order
        if 'status' in item.data and item.data['status'] == 'error':
            continue  # Skip error readings
            
        timestamps.append(item.timestamp.isoformat())
        
        for field in fields:
            if field in item.data:
                telemetry_data[field].append(item.data[field])
            else:
                telemetry_data[field].append(None)
    
    context = {
        'device': device,
        'telemetry': telemetry,
        'anomalies': anomalies,
        'hours': hours,
        'telemetry_data': json.dumps(telemetry_data),
        'timestamps': json.dumps(timestamps),
        'fields': fields,
    }
    
    return render(request, 'dashboard/device_detail.html', context)


def anomaly_list(request):
    """View for listing all anomalies with filtering options."""
    # Get query parameters for filtering
    severity = request.GET.get('severity')
    device_type = request.GET.get('device_type')
    acknowledged = request.GET.get('acknowledged')
    
    # Build the queryset with filters
    anomalies = AnomalyDetection.objects.select_related('device', 'device__device_type').all()
    
    if severity:
        anomalies = anomalies.filter(severity=severity)
    if device_type:
        anomalies = anomalies.filter(device__device_type__name=device_type)
    if acknowledged:
        is_acknowledged = acknowledged.lower() == 'true'
        anomalies = anomalies.filter(acknowledged=is_acknowledged)
    
    # Order by timestamp (newest first)
    anomalies = anomalies.order_by('-timestamp')
    
    # Get unique filter options for the UI
    device_types = DeviceType.objects.all()
    severity_choices = [choice[0] for choice in AnomalyDetection.SEVERITY_CHOICES]
    
    context = {
        'anomalies': anomalies,
        'device_types': device_types,
        'severity_choices': severity_choices,
        'active_filters': {
            'severity': severity,
            'device_type': device_type,
            'acknowledged': acknowledged,
        }
    }
    
    return render(request, 'dashboard/anomaly_list.html', context)


def metrics_dashboard(request):
    """View for monitoring system-wide metrics."""
    # Get time range from query parameters
    days = request.GET.get('days', 7)
    try:
        days = int(days)
    except ValueError:
        days = 7  # Default to 7 days if invalid
    
    time_range = timezone.now() - timedelta(days=days)
    
    # Calculate daily telemetry counts
    daily_counts = []
    for day in range(days):
        day_start = time_range + timedelta(days=day)
        day_end = day_start + timedelta(days=1)
        count = Telemetry.objects.filter(
            timestamp__gte=day_start,
            timestamp__lt=day_end
        ).count()
        daily_counts.append({
            'date': day_start.date().isoformat(),
            'count': count
        })
    
    # Calculate daily anomaly counts by severity
    severity_data = []
    for severity in ['low', 'medium', 'high', 'critical']:
        daily_data = []
        for day in range(days):
            day_start = time_range + timedelta(days=day)
            day_end = day_start + timedelta(days=1)
            count = AnomalyDetection.objects.filter(
                timestamp__gte=day_start,
                timestamp__lt=day_end,
                severity=severity
            ).count()
            daily_data.append({
                'date': day_start.date().isoformat(),
                'count': count
            })
        severity_data.append({
            'severity': severity,
            'data': daily_data
        })
    
    # Calculate device type distribution
    device_counts = DeviceType.objects.annotate(
        count=Count('devices')
    ).values('name', 'count')
    
    # Calculate device status distribution
    status_counts = Device.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    context = {
        'days': days,
        'daily_counts': json.dumps(daily_counts),
        'severity_counts': json.dumps(severity_data),
        'device_counts': json.dumps(list(device_counts)),
        'status_counts': json.dumps(list(status_counts))
    }
    
    return render(request, 'dashboard/metrics.html', context)


def acknowledge_anomaly(request, anomaly_id):
    """Handle anomaly acknowledgment."""
    if request.method == 'POST':
        anomaly = get_object_or_404(AnomalyDetection, id=anomaly_id)
        anomaly.acknowledged = True
        anomaly.acknowledged_at = timezone.now()
        anomaly.save()
        return redirect('dashboard:anomaly_list')
    return redirect('dashboard:anomaly_list') 
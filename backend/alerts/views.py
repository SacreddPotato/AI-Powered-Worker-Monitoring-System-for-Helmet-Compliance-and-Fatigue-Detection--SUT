from django.utils import timezone
from django.http import HttpResponse
from django.utils.dateparse import parse_date, parse_datetime
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from collections import OrderedDict
from datetime import datetime, time, timedelta
import csv
from io import StringIO
import re
from cameras.models import Camera
from detection.models import ModelSetting
from .models import Alert, CameraAlertSeverity
from .serializers import AlertSerializer
from .services import SEVERITY_MAP

VALID_SEVERITIES = {'high', 'medium', 'low'}


@api_view(['GET'])
def alert_severity_matrix_view(request):
    model_keys = list(ModelSetting.objects.order_by('key').values_list('key', flat=True))
    if not model_keys:
        model_keys = sorted(SEVERITY_MAP.keys())

    defaults = {key: SEVERITY_MAP.get(key, 'low') for key in model_keys}
    camera_rows = list(Camera.objects.order_by('id').values('id', 'name'))

    matrix = {
        row['id']: {key: defaults[key] for key in model_keys}
        for row in camera_rows
    }

    overrides = CameraAlertSeverity.objects.filter(camera_id__in=matrix.keys(), model_key__in=model_keys)
    for override in overrides:
        matrix.setdefault(override.camera_id, {})[override.model_key] = override.severity

    return Response({
        'model_keys': model_keys,
        'defaults': defaults,
        'matrix': matrix,
        'cameras': camera_rows,
    })


@api_view(['PUT'])
def camera_alert_severity_view(request, camera_id, model_key):
    camera = get_object_or_404(Camera, pk=camera_id)
    if not ModelSetting.objects.filter(key=model_key).exists():
        return Response({'error': f'Unknown model key: {model_key}'}, status=status.HTTP_400_BAD_REQUEST)

    severity = str(request.data.get('severity', '')).strip().lower()
    if severity not in VALID_SEVERITIES:
        return Response({'error': 'severity must be one of high|medium|low'}, status=status.HTTP_400_BAD_REQUEST)

    override, _ = CameraAlertSeverity.objects.get_or_create(
        camera=camera,
        model_key=model_key,
        defaults={'severity': severity},
    )
    override.severity = severity
    override.save()

    return Response({'camera': camera.id, 'model_key': model_key, 'severity': severity})


@api_view(['POST'])
def apply_global_alert_severity_override_view(request):
    severities = request.data.get('severities')
    if not isinstance(severities, dict) or not severities:
        return Response({'error': 'Payload must include non-empty severities object'}, status=status.HTTP_400_BAD_REQUEST)

    valid_model_keys = set(ModelSetting.objects.values_list('key', flat=True))
    updates = []
    for model_key, raw_severity in severities.items():
        severity = str(raw_severity).strip().lower()
        if model_key not in valid_model_keys:
            return Response({'error': f'Unknown model key: {model_key}'}, status=status.HTTP_400_BAD_REQUEST)
        if severity not in VALID_SEVERITIES:
            return Response({'error': f'severity for {model_key} must be one of high|medium|low'}, status=status.HTTP_400_BAD_REQUEST)
        updates.append((model_key, severity))

    camera_ids = list(Camera.objects.values_list('id', flat=True))
    updated_count = 0
    for camera_id in camera_ids:
        for model_key, severity in updates:
            CameraAlertSeverity.objects.update_or_create(
                camera_id=camera_id,
                model_key=model_key,
                defaults={'severity': severity},
            )
            updated_count += 1

    return Response({'updated': updated_count, 'camera_count': len(camera_ids), 'model_count': len(updates)})

class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.select_related('camera', 'detection').all()
    serializer_class = AlertSerializer
    filterset_fields = ['camera', 'model_key', 'severity', 'status']

    @staticmethod
    def _parse_query_datetime(value, end_of_day=False):
        if not value:
            return None

        dt = parse_datetime(value)
        if dt is not None:
            return dt if timezone.is_aware(dt) else timezone.make_aware(dt)

        d = parse_date(value)
        if d is None:
            return None

        t = time.max if end_of_day else time.min
        return timezone.make_aware(datetime.combine(d, t))

    def _apply_date_filters(self, queryset, params):
        now = timezone.now()
        date_range = params.get('date_range', '').lower().strip()

        if date_range == 'today':
            start = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
            queryset = queryset.filter(created_at__gte=start)
        elif date_range == 'week':
            queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
        elif date_range == 'month':
            queryset = queryset.filter(created_at__gte=now - timedelta(days=30))
        elif date_range == 'custom':
            start = self._parse_query_datetime(params.get('start'), end_of_day=False)
            end = self._parse_query_datetime(params.get('end'), end_of_day=True)
            if start is not None:
                queryset = queryset.filter(created_at__gte=start)
            if end is not None:
                queryset = queryset.filter(created_at__lte=end)

        return queryset

    def get_queryset(self):
        queryset = Alert.objects.select_related('camera', 'detection').all()
        params = self.request.query_params

        camera_id = params.get('camera')
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)

        model_key = params.get('model_key')
        if model_key:
            queryset = queryset.filter(model_key=model_key)

        severity = params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        status_value = params.get('status')
        if status_value:
            queryset = queryset.filter(status=status_value)

        queryset = self._apply_date_filters(queryset, params)

        return queryset

    @action(detail=True, methods=['patch'], url_path='acknowledge')
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.save()

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'alerts',
                {'type': 'alert.acknowledged', 'alert_id': alert.id}
            )

        return Response(AlertSerializer(alert).data)

    @action(detail=False, methods=['get'], url_path='export/excel')
    def export_excel(self, request):
        workbook_cls = None
        try:
            from openpyxl import Workbook
            workbook_cls = Workbook
        except Exception:
            workbook_cls = None

        alerts = list(self.get_queryset().order_by('-created_at'))

        if workbook_cls is None:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Camera', 'Alert ID', 'Model', 'Severity', 'Status', 'Message', 'Confidence', 'Created At'])

            if not alerts:
                writer.writerow(['(no alerts)', '', '', '', '', '', '', ''])

            grouped = OrderedDict()
            for alert in alerts:
                grouped.setdefault(alert.camera.name, []).append(alert)

            for camera_name, items in grouped.items():
                for alert in items:
                    confidence = ''
                    if alert.detection is not None and alert.detection.confidence is not None:
                        confidence = float(alert.detection.confidence)
                    writer.writerow([
                        camera_name,
                        alert.id,
                        alert.model_key,
                        alert.severity,
                        alert.status,
                        alert.message,
                        confidence,
                        alert.created_at.isoformat(),
                    ])

            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="alerts_by_camera_{timestamp}.csv"'
            return response

        wb = workbook_cls()
        summary = wb.active
        summary.title = 'Summary'
        summary.append(['Camera', 'Total Alerts', 'Open', 'Acknowledged', 'High', 'Medium', 'Low'])

        grouped = OrderedDict()
        for alert in alerts:
            camera_name = alert.camera.name
            grouped.setdefault(camera_name, []).append(alert)

        for camera_name, items in grouped.items():
            total = len(items)
            open_count = len([a for a in items if a.status == 'open'])
            ack_count = len([a for a in items if a.status == 'acknowledged'])
            high = len([a for a in items if a.severity == 'high'])
            medium = len([a for a in items if a.severity == 'medium'])
            low = len([a for a in items if a.severity == 'low'])
            summary.append([camera_name, total, open_count, ack_count, high, medium, low])

            sheet_title = re.sub(r'[\\/*?:\[\]]', '_', camera_name)[:31] or f'Camera_{items[0].camera_id}'
            sheet = wb.create_sheet(title=sheet_title)
            sheet.append(['Alert ID', 'Model', 'Severity', 'Status', 'Message', 'Confidence', 'Created At'])
            for alert in items:
                confidence = ''
                if alert.detection is not None and alert.detection.confidence is not None:
                    confidence = float(alert.detection.confidence)
                sheet.append([
                    alert.id,
                    alert.model_key,
                    alert.severity,
                    alert.status,
                    alert.message,
                    confidence,
                    alert.created_at.isoformat(),
                ])

        if not alerts:
            summary.append(['(no alerts)', 0, 0, 0, 0, 0, 0])

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="alerts_by_camera_{timestamp}.xlsx"'
        wb.save(response)
        return response

    @action(detail=False, methods=['get'], url_path='export/chart-data')
    def export_chart_data(self, request):
        group_by = request.query_params.get('group_by', 'severity')
        alerts = list(self.get_queryset())
        now = timezone.now()

        buckets = OrderedDict()
        for alert in alerts:
            if group_by == 'camera':
                key = alert.camera.name
            elif group_by == 'model':
                key = alert.model_key
            elif group_by == 'status':
                key = alert.status
            elif group_by == 'time':
                diff = now - alert.created_at
                if diff <= timedelta(minutes=1):
                    key = 'Last minute'
                elif diff <= timedelta(minutes=5):
                    key = 'Last 5 minutes'
                elif diff <= timedelta(hours=1):
                    key = 'Last hour'
                else:
                    key = 'Older'
            else:
                key = alert.severity

            buckets[key] = buckets.get(key, 0) + 1

        labels = list(buckets.keys())
        values = [buckets[label] for label in labels]
        return Response({
            'group_by': group_by,
            'labels': labels,
            'values': values,
            'total': sum(values),
        })

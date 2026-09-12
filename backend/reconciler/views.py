from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from reconciler.models import Location, SystemARecord, SystemBEntry
from reconciler.services.comparator import reconcile_records
from reconciler.services.normalization import safe_parse_decimal


class TenantListView(APIView):
    def get(self, request):
        locations = Location.objects.all().order_by('org_id', 'location_id')
        tenants_map = {}
        for loc in locations:
            if loc.org_id not in tenants_map:
                tenants_map[loc.org_id] = {
                    'org_id': loc.org_id,
                    'locations': [],
                }
            tenants_map[loc.org_id]['locations'].append({
                'location_id': loc.location_id,
                'location_name': loc.location_name,
            })

        return Response({
            'tenants': list(tenants_map.values()),
        })


class DiscrepancyListView(APIView):
    def get(self, request):
        org_id = request.query_params.get('org_id', '').strip()
        reason_filter = request.query_params.get('reason', 'ALL').strip().upper()
        sort_by = request.query_params.get('sort_by', 'value').strip().lower()
        sort_order = request.query_params.get('sort_order', 'asc').strip().lower()

        if not org_id:
            return Response(
                {
                    'error': 'Multi-tenant violation: org_id query parameter is required. Global unscoped queries are strictly prohibited.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        all_locations = Location.objects.all()
        loc_map = {
            loc.location_id: {
                'org_id': loc.org_id,
                'location_name': loc.location_name,
            }
            for loc in all_locations
        }

        tenant_locations = [loc_id for loc_id, info in loc_map.items() if info['org_id'] == org_id]
        if not tenant_locations:
            return Response(
                {
                    'error': f'Tenant "{org_id}" does not exist in location registry.',
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        records_a = list(SystemARecord.objects.values())
        records_b = list(SystemBEntry.objects.values())

        all_discrepancies = reconcile_records(records_a, records_b, loc_map)
        tenant_discrepancies = [d for d in all_discrepancies if d.org_id == org_id]

        stats = {
            'ALL': len(tenant_discrepancies),
            'MISSING_IN_SYSTEM_B': sum(1 for d in tenant_discrepancies if d.reason == 'MISSING_IN_SYSTEM_B'),
            'ORPHAN_IN_SYSTEM_B': sum(1 for d in tenant_discrepancies if d.reason == 'ORPHAN_IN_SYSTEM_B'),
            'DUPLICATE_IN_SYSTEM_B': sum(1 for d in tenant_discrepancies if d.reason == 'DUPLICATE_IN_SYSTEM_B'),
            'VALUE_MISMATCH': sum(1 for d in tenant_discrepancies if d.reason == 'VALUE_MISMATCH'),
        }

        filtered = tenant_discrepancies
        if reason_filter and reason_filter != 'ALL':
            filtered = [d for d in filtered if d.reason == reason_filter]

        def sort_key_val(d):
            val_str = d.val_a if d.val_a is not None else d.val_b
            dec = safe_parse_decimal(val_str)
            return dec if dec is not None else Decimal('-Infinity')

        if sort_by == 'value':
            filtered.sort(key=sort_key_val, reverse=(sort_order == 'desc'))
        elif sort_by == 'record_id':
            filtered.sort(key=lambda d: d.record_id, reverse=(sort_order == 'desc'))

        return Response({
            'org_id': org_id,
            'total_count': len(filtered),
            'stats': stats,
            'results': [d.to_dict() for d in filtered],
        })

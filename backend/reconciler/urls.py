from django.urls import path
from reconciler.views import DiscrepancyListView, TenantListView

urlpatterns = [
    path('tenants/', TenantListView.as_view(), name='tenant-list'),
    path('discrepancies/', DiscrepancyListView.as_view(), name='discrepancy-list'),
]

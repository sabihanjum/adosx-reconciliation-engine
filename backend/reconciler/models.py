from django.db import models

class Location(models.Model):
    location_id = models.CharField(max_length=50, primary_key=True)
    org_id = models.CharField(max_length=50, db_index=True)
    location_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.location_id} ({self.org_id}) - {self.location_name}"


class SystemARecord(models.Model):
    record_id = models.CharField(max_length=50, primary_key=True)
    normalized_record_id = models.CharField(max_length=50, db_index=True)
    location_id = models.CharField(max_length=50, db_index=True, blank=True, default='')
    event_date = models.CharField(max_length=50, blank=True, default='')
    category_code = models.CharField(max_length=50, blank=True, default='')
    actor_id = models.CharField(max_length=50, blank=True, default='')
    base_value_raw = models.CharField(max_length=100, blank=True, default='')
    adjustment_raw = models.CharField(max_length=100, blank=True, default='')
    total_value_raw = models.CharField(max_length=100, blank=True, default='')
    total_value = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    state = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SystemA: {self.record_id} ({self.total_value_raw})"


class SystemBEntry(models.Model):
    entry_id = models.CharField(max_length=50, primary_key=True)
    record_ref_raw = models.CharField(max_length=100, blank=True, default='')
    normalized_record_ref = models.CharField(max_length=50, db_index=True)
    location_id = models.CharField(max_length=50, db_index=True, blank=True, default='')
    recorded_on = models.CharField(max_length=50, blank=True, default='')
    value_raw = models.CharField(max_length=100, blank=True, default='')
    value = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    label = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SystemB: {self.entry_id} -> {self.record_ref_raw} ({self.value_raw})"

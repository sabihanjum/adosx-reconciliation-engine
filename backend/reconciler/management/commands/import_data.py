import csv
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction

from reconciler.models import Location, SystemARecord, SystemBEntry
from reconciler.services.normalization import normalize_reference, safe_parse_decimal


class Command(BaseCommand):
    help = 'Robustly ingests locations.csv, system_a.csv, and system_b.csv into SQLite without dropping malformed rows.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default=None,
            help='Directory containing the CSV files. Defaults to <workspace>/data',
        )

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_dir_arg = options.get('data_dir')
        if data_dir_arg:
            data_dir = Path(data_dir_arg)
        else:
            data_dir = base_dir.parent / 'data'

        if not data_dir.exists():
            self.stderr.write(self.style.ERROR(f'Data directory not found: {data_dir}'))
            return

        self.stdout.write(self.style.NOTICE(f'Ingesting dirty exports from: {data_dir}'))

        locations_file = data_dir / 'locations.csv'
        system_a_file = data_dir / 'system_a.csv'
        system_b_file = data_dir / 'system_b.csv'

        with transaction.atomic():
            self.stdout.write('Loading locations.csv...')
            Location.objects.all().delete()
            loc_count = 0
            with open(locations_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    Location.objects.create(
                        location_id=row['location_id'].strip(),
                        org_id=row['org_id'].strip(),
                        location_name=row['location_name'].strip(),
                    )
                    loc_count += 1
            self.stdout.write(self.style.SUCCESS(f'  [OK] Imported {loc_count} locations.'))

            self.stdout.write('Loading system_a.csv...')
            SystemARecord.objects.all().delete()
            a_count = 0
            a_dirty_values = 0
            with open(system_a_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_id = row.get('record_id', '').strip()
                    norm_id = normalize_reference(raw_id)
                    raw_total = row.get('total_value', '')
                    parsed_total = safe_parse_decimal(raw_total)
                    if parsed_total is None and raw_total != '':
                        a_dirty_values += 1

                    SystemARecord.objects.create(
                        record_id=raw_id,
                        normalized_record_id=norm_id,
                        location_id=row.get('location_id', '').strip(),
                        event_date=row.get('event_date', '').strip(),
                        category_code=row.get('category_code', '').strip(),
                        actor_id=row.get('actor_id', '').strip(),
                        base_value_raw=row.get('base_value', '').strip(),
                        adjustment_raw=row.get('adjustment', '').strip(),
                        total_value_raw=raw_total.strip(),
                        total_value=parsed_total,
                        state=row.get('state', '').strip(),
                    )
                    a_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'  [OK] Imported {a_count} System A records (preserved raw, {a_dirty_values} unparseable decimals).'
                )
            )

            self.stdout.write('Loading system_b.csv...')
            SystemBEntry.objects.all().delete()
            b_count = 0
            b_dirty_refs = 0
            b_dirty_values = 0
            with open(system_b_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entry_id = row.get('entry_id', '').strip()
                    raw_ref = row.get('record_ref', '')
                    norm_ref = normalize_reference(raw_ref)
                    if not raw_ref.strip().startswith('REC-'):
                        b_dirty_refs += 1

                    raw_val = row.get('value', '')
                    parsed_val = safe_parse_decimal(raw_val)
                    if parsed_val is None:
                        b_dirty_values += 1

                    SystemBEntry.objects.create(
                        entry_id=entry_id,
                        record_ref_raw=raw_ref,
                        normalized_record_ref=norm_ref,
                        location_id=row.get('location_id', '').strip(),
                        recorded_on=row.get('recorded_on', '').strip(),
                        value_raw=raw_val,
                        value=parsed_val,
                        label=row.get('label', '').strip(),
                    )
                    b_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'  [OK] Imported {b_count} System B entries ({b_dirty_refs} non-standard references normalized, {b_dirty_values} dirty/blank values safely handled).'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nIngestion completed successfully: {a_count} System A rows and {b_count} System B entries loaded. Zero rows dropped.'
            )
        )

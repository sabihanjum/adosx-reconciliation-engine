import pytest
from decimal import Decimal
from reconciler.services.comparator import reconcile_records
from reconciler.services.normalization import normalize_reference, safe_parse_decimal


LOCATIONS_MAP = {
    'LOC-101': {'org_id': 'ORG-A', 'location_name': 'Location 101'},
    'LOC-102': {'org_id': 'ORG-A', 'location_name': 'Location 102'},
    'LOC-103': {'org_id': 'ORG-A', 'location_name': 'Location 103'},
    'LOC-201': {'org_id': 'ORG-B', 'location_name': 'Location 201'},
    'LOC-202': {'org_id': 'ORG-B', 'location_name': 'Location 202'},
}


def test_detects_record_missing_in_system_b():
    records_a = [
        {'record_id': 'REC-1015', 'location_id': 'LOC-103', 'total_value_raw': '41095.33'}
    ]
    records_b = []

    results = reconcile_records(records_a, records_b, LOCATIONS_MAP)

    assert len(results) == 1
    assert results[0].reason == 'MISSING_IN_SYSTEM_B'
    assert results[0].record_id == 'REC-1015'
    assert results[0].org_id == 'ORG-A'
    assert results[0].val_a == '41095.33'
    assert results[0].val_b is None


def test_detects_orphan_record_in_system_b():
    records_a = []
    records_b = [
        {'entry_id': 'ENT/2026/4901', 'record_ref': 'REC-1999', 'location_id': 'LOC-102', 'value_raw': '41250.00'}
    ]

    results = reconcile_records(records_a, records_b, LOCATIONS_MAP)

    assert len(results) == 1
    assert results[0].reason == 'ORPHAN_IN_SYSTEM_B'
    assert results[0].record_id == 'REC-1999'
    assert results[0].org_id == 'ORG-A'
    assert results[0].val_a is None
    assert results[0].val_b == '41250.00'


def test_detects_duplicate_entries_in_system_b():
    records_a = [
        {'record_id': 'REC-1042', 'location_id': 'LOC-101', 'total_value_raw': '112837.06'}
    ]
    records_b = [
        {'entry_id': 'ENT/2026/4042', 'record_ref': 'REC-1042', 'location_id': 'LOC-101', 'value_raw': '112837.06'},
        {'entry_id': 'ENT/2026/4902', 'record_ref': 'rec1042', 'location_id': 'LOC-101', 'value_raw': '112837.06'},
    ]

    results = reconcile_records(records_a, records_b, LOCATIONS_MAP)

    assert len(results) == 1
    assert results[0].reason == 'DUPLICATE_IN_SYSTEM_B'
    assert results[0].record_id == 'REC-1042'
    assert results[0].org_id == 'ORG-A'
    assert '112837.06; 112837.06' in results[0].val_b


def test_detects_value_mismatch():
    records_a = [
        {'record_id': 'REC-1003', 'location_id': 'LOC-202', 'total_value_raw': '121388.01'}
    ]
    records_b = [
        {'entry_id': 'ENT/2026/4003', 'record_ref': 'REC-1003', 'location_id': 'LOC-202', 'value_raw': '94834.38'}
    ]

    results = reconcile_records(records_a, records_b, LOCATIONS_MAP)

    assert len(results) == 1
    assert results[0].reason == 'VALUE_MISMATCH'
    assert results[0].record_id == 'REC-1003'
    assert results[0].org_id == 'ORG-B'
    assert results[0].val_a == '121388.01'
    assert results[0].val_b == '94834.38'


def test_tenant_boundary_isolation():
    records_a = [
        {'record_id': 'REC-A01', 'location_id': 'LOC-101', 'total_value_raw': '100.00'},
        {'record_id': 'REC-B01', 'location_id': 'LOC-201', 'total_value_raw': '200.00'},
    ]
    records_b = []

    discrepancies = reconcile_records(records_a, records_b, LOCATIONS_MAP)

    org_a_data = [d for d in discrepancies if d.org_id == 'ORG-A']
    org_b_data = [d for d in discrepancies if d.org_id == 'ORG-B']

    assert len(org_a_data) == 1
    assert org_a_data[0].record_id == 'REC-A01'
    assert all(d.org_id == 'ORG-A' for d in org_a_data)

    assert len(org_b_data) == 1
    assert org_b_data[0].record_id == 'REC-B01'
    assert all(d.org_id == 'ORG-B' for d in org_b_data)


def test_canonical_reference_normalization_non_error():
    records_a = [
        {'record_id': 'REC-1112', 'location_id': 'LOC-101', 'total_value_raw': '52028.74'}
    ]
    records_b = [
        {'entry_id': 'ENT/2026/4112', 'record_ref': '1112', 'location_id': 'LOC-101', 'value_raw': '52028.74'}
    ]

    results = reconcile_records(records_a, records_b, LOCATIONS_MAP)

    assert len(results) == 0


def test_dirty_currency_and_comma_parsing():
    assert safe_parse_decimal('1,25,400.00') == Decimal('125400.00')
    assert safe_parse_decimal('$120.50') == Decimal('120.50')
    assert safe_parse_decimal('  450.00  ') == Decimal('450.00')
    assert safe_parse_decimal('') is None
    assert safe_parse_decimal('N/A') is None
    assert safe_parse_decimal('NULL') is None


def test_blank_value_mismatch():
    records_a = [
        {'record_id': 'REC-1050', 'location_id': 'LOC-202', 'total_value_raw': '160405.85'}
    ]
    records_b = [
        {'entry_id': 'ENT/2026/4050', 'record_ref': 'REC-1050', 'location_id': 'LOC-202', 'value_raw': ''}
    ]

    results = reconcile_records(records_a, records_b, LOCATIONS_MAP)

    assert len(results) == 1
    assert results[0].reason == 'VALUE_MISMATCH'
    assert results[0].record_id == 'REC-1050'
    assert results[0].val_a == '160405.85'
    assert results[0].val_b == ''


def test_real_dataset_reconciliation():
    """
    End-to-end regression test against the actual 120-row and 121-entry
    assignment CSV datasets.
    """
    import csv
    from pathlib import Path

    data_dir = Path(__file__).resolve().parent.parent.parent.parent / 'data'
    assert data_dir.exists(), f"Data directory missing at {data_dir}"

    with open(data_dir / 'locations.csv', 'r', encoding='utf-8') as f:
        locs = {
            r['location_id']: {'org_id': r['org_id'], 'location_name': r['location_name']}
            for r in csv.DictReader(f)
        }

    with open(data_dir / 'system_a.csv', 'r', encoding='utf-8') as f:
        recs_a = [
            {'record_id': r['record_id'], 'location_id': r['location_id'], 'total_value_raw': r['total_value']}
            for r in csv.DictReader(f)
        ]

    with open(data_dir / 'system_b.csv', 'r', encoding='utf-8') as f:
        recs_b = [
            {'entry_id': r['entry_id'], 'record_ref': r['record_ref'], 'location_id': r['location_id'], 'value_raw': r['value']}
            for r in csv.DictReader(f)
        ]

    discrepancies = reconcile_records(recs_a, recs_b, locs)

    # Must find exactly 10 genuine discrepancies in the dataset
    assert len(discrepancies) == 10

    # Strict multi-tenant distribution
    org_a_discrepancies = [d for d in discrepancies if d.org_id == 'ORG-A']
    org_b_discrepancies = [d for d in discrepancies if d.org_id == 'ORG-B']
    assert len(org_a_discrepancies) == 7
    assert len(org_b_discrepancies) == 3

    # Ensure REC-1112 was matched without false discrepancy
    assert not any(d.record_id in {'REC-1112', '1112'} for d in discrepancies)


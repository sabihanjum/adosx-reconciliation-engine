from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from .normalization import normalize_reference, safe_parse_decimal


@dataclass
class Discrepancy:
    reason: str
    record_id: str
    location_id: str
    location_name: str
    org_id: str
    val_a: str | None
    val_b: str | None
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def reconcile_records(
    records_a: List[Dict[str, Any]],
    records_b: List[Dict[str, Any]],
    locations_map: Dict[str, Dict[str, str]],
) -> List[Discrepancy]:
    discrepancies: List[Discrepancy] = []

    b_by_ref = defaultdict(list)
    for b in records_b:
        raw_ref = b.get('record_ref') or b.get('record_ref_raw') or ''
        norm_ref = b.get('normalized_record_ref') or normalize_reference(raw_ref)
        b_by_ref[norm_ref].append(b)

    matched_b_refs = set()

    for a in records_a:
        raw_id = a.get('record_id') or ''
        norm_id = a.get('normalized_record_id') or normalize_reference(raw_id)
        loc_id = a.get('location_id') or ''
        loc_info = locations_map.get(loc_id, {})
        org_id = loc_info.get('org_id', 'UNKNOWN')
        loc_name = loc_info.get('location_name', loc_id)

        raw_val_a = a.get('total_value_raw')
        if raw_val_a is None:
            raw_val_a = str(a.get('total_value') or a.get('value') or '')

        b_entries = b_by_ref.get(norm_id, [])

        if not b_entries:
            discrepancies.append(
                Discrepancy(
                    reason='MISSING_IN_SYSTEM_B',
                    record_id=raw_id,
                    location_id=loc_id,
                    location_name=loc_name,
                    org_id=org_id,
                    val_a=raw_val_a,
                    val_b=None,
                    details=f"Record {raw_id} present in System A but absent from System B export.",
                )
            )
        elif len(b_entries) > 1:
            matched_b_refs.add(norm_id)
            entry_ids = [str(e.get('entry_id', '')) for e in b_entries]
            entry_vals = [str(e.get('value_raw') or e.get('value') or '') for e in b_entries]
            discrepancies.append(
                Discrepancy(
                    reason='DUPLICATE_IN_SYSTEM_B',
                    record_id=raw_id,
                    location_id=loc_id,
                    location_name=loc_name,
                    org_id=org_id,
                    val_a=raw_val_a,
                    val_b="; ".join(entry_vals),
                    details=f"Referenced {len(b_entries)} times in System B ({', '.join(entry_ids)}).",
                )
            )
        else:
            matched_b_refs.add(norm_id)
            b_first = b_entries[0]
            raw_val_b = b_first.get('value_raw')
            if raw_val_b is None:
                raw_val_b = str(b_first.get('value') or '')

            dec_a = safe_parse_decimal(raw_val_a)
            dec_b = safe_parse_decimal(raw_val_b)

            if dec_a != dec_b:
                discrepancies.append(
                    Discrepancy(
                        reason='VALUE_MISMATCH',
                        record_id=raw_id,
                        location_id=loc_id,
                        location_name=loc_name,
                        org_id=org_id,
                        val_a=raw_val_a,
                        val_b=raw_val_b,
                        details=f"Values differ: System A reported '{raw_val_a}' vs System B reported '{raw_val_b}'.",
                    )
                )

    for norm_ref, b_entries in b_by_ref.items():
        if norm_ref not in matched_b_refs and norm_ref != '':
            for orphan in b_entries:
                raw_ref = orphan.get('record_ref_raw') or orphan.get('record_ref') or norm_ref
                loc_id = orphan.get('location_id') or ''
                loc_info = locations_map.get(loc_id, {})
                org_id = loc_info.get('org_id', 'UNKNOWN')
                loc_name = loc_info.get('location_name', loc_id)
                raw_val_b = orphan.get('value_raw')
                if raw_val_b is None:
                    raw_val_b = str(orphan.get('value') or '')

                discrepancies.append(
                    Discrepancy(
                        reason='ORPHAN_IN_SYSTEM_B',
                        record_id=str(raw_ref),
                        location_id=loc_id,
                        location_name=loc_name,
                        org_id=org_id,
                        val_a=None,
                        val_b=raw_val_b,
                        details=f"Entry {orphan.get('entry_id', '')} points to non-existent System A reference '{raw_ref}'.",
                    )
                )

    discrepancies.sort(key=lambda d: d.record_id)
    return discrepancies

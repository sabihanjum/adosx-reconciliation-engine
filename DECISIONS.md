# Architectural Decisions Log (DECISIONS.md)

### 1. Ingestion Strategy: Raw Storage with Defensive Parsing vs. Eager Schema Rejection
- **Decision:** Persist all incoming data preserving raw text fields (`base_value_raw`, `total_value_raw`, `record_ref_raw`) alongside defensively parsed canonical types without dropping malformed rows.
- **Alternative:** Strict database-level type constraints and eager casting during ingestion.
- **Reasoning:** System B exports deliberately contain non-standard formats (e.g., `'1,25,400.00'`, blank values `''`, and numeric-only references); eager database validation would cause silent row loss or ingestion pipeline crashes.

### 2. Foreign Reference Normalization: Canonical Prefix Alignment vs. Naive Symbol Stripping
- **Decision:** Normalize reference IDs by stripping non-alphanumerics, lowercasing, and canonicalizing purely numeric references (e.g., `'1112'` -> `'rec1112'`) to align with System A's entity prefix standard.
- **Alternative:** Naive alphanumeric regex stripping (`re.sub(r'[^a-zA-Z0-9]', '', ref).lower()`).
- **Reasoning:** Naive regex leaves System B's `'1112'` and System A's `'REC-1112'` mismatched, incorrectly triggering both a false orphan in System B and a false missing record in System A for what is an identical, valid match.

### 3. Numeric Representation: Python `Decimal` vs. Native Floating-Point
- **Decision:** Parse and compare all monetary and adjustment amounts using Python's `Decimal` type after stripping punctuation and currency symbols.
- **Alternative:** Standard IEEE-754 `float` casting.
- **Reasoning:** Binary floating-point representation introduces subtle precision drift (e.g., representation anomalies on currency decimals), causing false `VALUE_MISMATCH` alerts on valid transactions.

### 4. Multi-Tenant Boundary Enforcement: Mandatory Query-Layer Guard vs. Frontend-Filtered Global Views
- **Decision:** Require explicit `org_id` context on all reconciliation API endpoints, returning HTTP 400 if omitted and strictly filtering data before serialization (`ResultSet = σ_{org_id = target_org}(Discrepancies)`).
- **Alternative:** Global unscoped endpoints that return all records and rely on the client to filter by organization.
- **Reasoning:** Relying on client-side filtering or optional parameters risks catastrophic cross-tenant data leakage, violating strict multi-tenant boundary compliance.

### 5. Comparison Architecture: In-Memory Pure Domain Service vs. Complex SQL Outer Joins
- **Decision:** Implement reconciliation as a deterministic, database-independent Python domain service.
- **Alternative:** Complex SQL full outer joins with SQLite regex extensions or custom database functions.
- **Reasoning:** A pure Python domain function executes in milliseconds, runs in-memory without test database setup, and enables fast, comprehensive regression testing.

### 6. Relational Modeling: Soft String References vs. Rigid Database Foreign Keys
- **Decision:** Store location and record references as indexed CharFields rather than enforcing database-level `ForeignKey(unique=True)` constraints.
- **Alternative:** Rigid database foreign keys between `SystemBEntry` -> `SystemARecord` and records -> `Location`.
- **Reasoning:** System B exports intentionally contain orphan records referencing non-existent System A parents; database foreign key constraints would reject orphaned rows during import.

### 7. Frontend Scope: Focused Audit Dashboard vs. Complex Multi-Route SPA
- **Decision:** Deliver a high-utility, single-page React audit dashboard centered on tenant selection, discrepancy classification badges, and instant value sorting.
- **Alternative:** Multi-page layout with third-party CSS component frameworks, charting libraries, and route navigation.
- **Reasoning:** The assignment explicitly emphasizes "plain and working beats pretty and broken," prioritizing deterministic discrepancy detection and tenant safety over visual fluff.

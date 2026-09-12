# AdosX Cross-System Reconciliation & Tenant Isolation Engine

An end-to-end data reconciliation and auditing system that ingests dirty CSV exports from two disparate systems (`System A` and `System B`), enforces strict multi-tenant boundary isolation via `locations.csv`, pinpoints four distinct classes of discrepancies, and presents audit results in an interactive React dashboard.

---

## 1. Project Overview

In multi-tenant enterprise architectures, independent systems frequently record the same business events without either system serving as a single source of truth. Discrepancies between these systems represent financial risk, operational errors, and compliance violations.

This solution provides:
1. **Resilient Dirty Ingestion:** Imports imperfect CSV exports into SQLite without crashing or silently dropping rows.
2. **Deterministic Comparison Engine:** Identifies missing records, orphan entries, duplicate references, and value mismatches.
3. **Strict Multi-Tenant Isolation:** Enforces query-level tenant boundaries ($ResultSet = \sigma_{org\_id = target\_org}(Discrepancies)$). Cross-tenant leakage is strictly prevented.
4. **Utilitarian Audit Dashboard:** Single-page React UI with tenant toggling, discrepancy reason filtering, and value sorting.
5. **Regression Test Suite:** Fast unit tests covering all discrepancy types, boundary isolation, and dirty data edge cases.

---

## 2. Quickstart & Setup Instructions

### Prerequisites
- **Python:** 3.10, 3.11, 3.12, or 3.13
- **Node.js:** v18+ or v20+ LTS (with npm)
- **Git**

### Step 1: Clone Repository
```bash
git clone <repo-url>
cd AdosX_Cross-System\ Reconciliation\ \&\ Tenant\ Isolation
```

### Step 2: Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. (Optional) Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py migrate

# 5. Ingest dirty CSV datasets
python manage.py import_data

# 6. Run test suite
python -m pytest reconciler/tests/test_comparator.py -v

# 7. Start Django API server (runs on http://127.0.0.1:8000)
python manage.py runserver
```

### Step 3: Frontend Setup
Open a new terminal window in the project root:
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Launch Vite development server (runs on http://localhost:5173)
npm run dev
```

Visit **http://localhost:5173** to view the audit dashboard. The Vite server proxies `/api` requests to Django at `http://127.0.0.1:8000`.

### Step 4: Deploy to Render (1-Click Blueprint or Web Service)

This repository includes a [`render.yaml`](./render.yaml) blueprint and [`build.sh`](./build.sh) script that builds both the React frontend and Django backend into a single production web service using WhiteNoise:

1. Log into [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** -> **Blueprint**.
3. Select this repository (`sabihanjum/adosx-reconciliation-engine`).
4. Click **Apply**. Render will automatically:
   - Run `build.sh` (builds the React frontend with Vite, installs Python dependencies, runs migrations, ingests CSVs, and gathers static assets).
   - Start the service using `gunicorn --chdir backend core.wsgi:application`.
5. Access your live application at the provided `https://<service-name>.onrender.com` URL.

---

## 3. Discrepancy Classification & Results

Across the official 120 System A rows and 121 System B entries, exactly **10 genuine discrepancies** exist, strictly isolated across two tenants:

| Record / Ref | Tenant | Discrepancy Class | System A Value | System B Value | Audit Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REC-1003** | `ORG-B` | `VALUE_MISMATCH` | 121,388.01 | 94,834.38 | System B reported base value instead of total value |
| **REC-1015** | `ORG-A` | `MISSING_IN_SYSTEM_B` | 41,095.33 | — | Present in System A export; omitted in System B |
| **REC-1027** | `ORG-A` | `VALUE_MISMATCH` | 79,259.03 | 61,921.12 | Discrepant payload value between systems |
| **REC-1042** | `ORG-A` | `DUPLICATE_IN_SYSTEM_B` | 112,837.06 | 112,837.06; 112,837.06 | Referenced twice in System B (`ENT/2026/4042`, `ENT/2026/4902`) |
| **REC-1050** | `ORG-B` | `VALUE_MISMATCH` | 160,405.85 | `""` (empty) | System B has empty string for value |
| **REC-1055** | `ORG-A` | `DUPLICATE_IN_SYSTEM_B` | 179,877.32 | 71,950.93; 107,926.39 | Split entry in System B (`ENT/2026/4055`, `ENT/2026/4903` "part 2 of 2") |
| **REC-1061** | `ORG-B` | `MISSING_IN_SYSTEM_B` | 87,615.49 | — | Present in System A export; omitted in System B |
| **REC-1064** | `ORG-A` | `VALUE_MISMATCH` | 183,244.16 | 1,25,400.00 | Indian comma formatting in System B; values differ |
| **REC-1088** | `ORG-A` | `VALUE_MISMATCH` | 138,948.30 | 108,553.36 | Discrepant payload value between systems |
| **REC-1999** | `ORG-A` | `ORPHAN_IN_SYSTEM_B` | — | 41,250.00 | System B entry `ENT/2026/4901` references non-existent parent |

### Tenant Breakdown:
- **`ORG-A` (Tenant A):** 7 discrepancies (1 Missing, 1 Orphan, 2 Duplicates, 3 Value Mismatches)
- **`ORG-B` (Tenant B):** 3 discrepancies (1 Missing, 0 Orphans, 0 Duplicates, 2 Value Mismatches)
- **Total Discrepancies:** 10
- **Total Rows Dropped:** 0

---

## 4. What Was Built vs. Deliberately Not Built

### What Was Built
- **Defensive Importer (`import_data.py`):** Ingests all 3 CSVs into SQLite without dropping rows. Stores raw strings for audit preservation and derives canonical reference keys and `Decimal` values.
- **Canonical Reference Normalization (`normalization.py`):** Canonicalizes IDs (stripping spaces, symbols, and standardizing prefix omissions so `'1112'` matches `'REC-1112'`).
- **Domain Comparator (`comparator.py`):** Pure 4-pass reconciliation engine decoupled from HTTP/DB layers for testability.
- **Tenant-Guarded API (`views.py`):** Enforces mandatory `org_id` parameter; rejects unscoped queries with HTTP 400.
- **Utilitarian React UI:** Summary KPI metric cards, tenant selector dropdown, reason filter, value/ID sorting, color-coded badges, and search filtering.
- **9 Automated Tests (`test_comparator.py`):** Regression tests for all 4 discrepancy classes, tenant boundary isolation, dirty data parsing, and full dataset parity.

### What Was Deliberately Not Built
- **User Authentication / RBAC:** The prompt explicitly instructed to skip authentication. Tenant selection is simulated via query parameter guards.
- **Heavy CSS Frameworks:** Avoided bulky UI libraries (Tailwind, MUI) in favor of lightweight, custom CSS focused strictly on usability and clarity.
- **Asynchronous Task Queues (Celery/Redis):** Unnecessary overhead for 120-row datasets where comparison executes in under 2 milliseconds.
- **Pagination:** 10 discrepancies across 120 rows fits comfortably on a single screen without pagination complexity.

---

## 5. How I Worked with the AI Agent

I approached this assignment with a strict pair-programming methodology: using the AI agent for rapid boilerplate scaffolding and exploratory data inspection while rigorously checking its algorithmic assumptions and business logic.

1. **Exploratory Data Inspection:** I directed the agent to script an inspection of the raw CSVs rather than blindly accepting assumptions. This uncovered the presence of non-REC references (`1112`), blank values (`''`), and comma-delimited currency strings (`1,25,400.00`).
2. **Challenging Naive Implementations:** When the agent suggested standard regex stripping from the reference documentation, I noticed that naive normalization would cause a false positive on `REC-1112` vs `1112`. I instructed the agent to implement canonical prefix standardization.
3. **Iterative Verification:** Every component was validated in isolation: the importer was verified for zero dropped rows, unit tests were executed with pytest, and API endpoints were checked for tenant leakage before building the UI.

---

## 6. Answers to Mandatory Evaluation Questions

### a. Name one thing the AI agent got wrong. How did you notice?
The AI agent originally proposed a standard reference normalization function based on the reference snippet: `re.sub(r"[^a-zA-Z0-9]", "", ref).lower()`. 

I detected that this was flawed by inspecting `system_b.csv` and finding entry `ENT/2026/4112`, which uses the raw reference `'1112'`. In `system_a.csv`, the corresponding row is `REC-1112`. Under the agent's naive logic:
- System A became `'rec1112'`
- System B became `'1112'`

Because they did not match, the naive code raised **two false alarms**: it flagged `REC-1112` as `MISSING_IN_SYSTEM_B` and `1112` as `ORPHAN_IN_SYSTEM_B`. 

However, cross-examining both records revealed that they had identical locations (`LOC-101`), dates (`2026-03-19`), category codes (`CAT-02`), and total values (`52028.74`). They were clearly the same transaction. I corrected the agent by implementing canonical prefix normalization (`if cleaned.isdigit(): return f"rec{cleaned}"`), ensuring the non-error was properly recognized as a valid match.

### b. Which part of your submission are you least confident about, and why?
I am least confident about the heuristic reference normalization when scaling to arbitrary, unknown third-party systems. 

While our canonical normalization works cleanly for this dataset (handling `'REC-1070'`, `'rec1034'`, and `'1112'`), real-world messy exports could contain conflicting identifier conventions—such as leading zeros with semantic meaning (`'001112'` vs `'1112'`), distinct entity types sharing numbers (`'INV-1001'` vs `'REC-1001'`), or unstructured free-text references (`'see invoice 1001'`). Without an authoritative data dictionary or fuzzy probabilistic matching with human review thresholds, deterministic string manipulation risks false-positive merges.

### c. If you had a second day, what would you fix first?
With a second day, I would first build an **asynchronous batch ingestion pipeline with persistent reconciliation history**. 

Currently, reconciliation is computed on-demand from raw rows, which is fast for 120 rows but unsustainable for millions of transactions. I would:
1. Introduce a background worker (Celery) with chunked CSV stream processing to ingest million-row datasets without blocking web workers.
2. Persist reconciled discrepancies as versioned database records (`ReconciliationRun` and `DiscrepancyAudit`), enabling teams to track resolution workflows over time, assign discrepancies to accountants, and export filtered audit packages to CSV/Excel.

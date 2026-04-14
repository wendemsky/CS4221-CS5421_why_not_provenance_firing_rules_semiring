# WHY-NOT Provenance Playground

This repository contains a Python prototype for **WHY-NOT provenance** using firing-rule style explanations, plus SQL test planning and sample TPC-C export data.

## What this repo is for

It helps you answer:

> “Why is tuple `Q(...)` **missing** from my query result?”

Instead of only returning empty/non-empty results, the system returns:
- failed derivations
- per-goal success/failure
- an explanation graph (tuple -> rule -> failed goals)

---

## Quick start

Python version: 3.10.12
Before you start, make sure to install packages in requirements.txt for necessary packages.
`pip install -r requirements.txt`


1. Enter the project implementation directory:

```bash
cd rule_firing
```

2. Run on an input file:

Navigate to `src` and run.

```bash
python3 why_not_provenance.py < YOUR_INPUT_FILE.txt > YOUR_OUTPUT_FILE.json
```

3. (Optional) Enable PostgreSQL-backed mode with `.env` (`env` should be placed in `rule_firing/src`):

```env
WHY_NOT_DB_CONNECTION=postgresql://user:pass@host:5432/db
```

Supported env keys:
- `WHY_NOT_DB_CONNECTION`
- `DATABASE_URL`
- `POSTGRES_CONNECTION_STRING`

You can also control concurrency:

```bash
WHY_NOT_MAX_WORKERS=4 python3 why_not_provenance.py < test.txt > test_result.json
```

---

## What to read first

- `README.md` — implementation usage and input format
- `src/provenance_visualizer/README.md` - instructions on how to use the visualizer
- `tests/README.md` — SQL-focused evaluation plan (correctness, completeness, informativeness)
- `TPC_C_export/TPCCReadme.txt` — context for bundled TPC-C data files

---

## Notes

- Current output mode is focused on **WHYNOT** explanation.
- SQL support is intentionally limited to a practical subset for provenance experiments.
- Completeness depends on active binding strategy (join-driven vs exhaustive style), so keep configuration fixed when benchmarking.

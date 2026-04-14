# Why-Not Provenance Project

This repository is organized around the two implementation directions discussed in the report for topic 8, plus the final submission materials.

## Repository Layout

```text
.
├── rule_firing/            Teammate implementation for firing-rules why-not provenance
├── semiring_provenance/    Semiring-based provenance system, queries, benchmarks, and TPC-C assets
├── submission_documents/   Report sources, outline, and benchmark/result files used for submission
├── .env.example            Database configuration template
└── README.md               Top-level guide
```

## What Is Where

### `rule_firing/`
- Rule-firing implementation and notes.
- Includes the `rile_firing/src` package, visualizer work, tests, and the original archive kept locally for reference.
- Refer to `rule_firing/README.md` and `rule_firing/src/provenance_visualizer/README.md` for more details.

### `semiring_provenance/`
- Main Python implementation for semiring-based why-not provenance. (This project is developed and tested using Python 3.13.1.)
- Contains:
  - `src/` for parser, annotator, evaluator, semirings, and explainer
  - `queries/` for the core SQL examples
  - `benchmark/` for correctness and performance scripts
  - `TPC_C_export/` for the TPC-C schema/data loading files
  - `cli.py` and `main.py` for running the system

### `submission_documents/`
- `report/` for LaTeX sources and figures
- `outline/` for the original project brief
- `results/` for benchmark outputs used in analysis

## Quick Start

### For semiring provenance
1. Copy `.env.example` to `.env` in the repo root and fill in the PostgreSQL credentials.
2. Create a virtual environment and install the semiring dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r semiring_provenance\requirements.txt
```

### For rule-firing provenance
1. Create `.env` in the `rule_firing/src` directory and fill in the PostgreSQL credentials.
2. Create a virtual environment and install the dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r rule_firing\requirements.txt
```

3. Refer to `rule_firing/README.md` and `rule_firing/src/provenance_visualizer/README.md` for more details on how to use the system and the visualizer.


## Running The Semiring System

```powershell
python semiring_provenance\cli.py tree --query semiring_provenance\queries\q1_select.sql
python semiring_provenance\cli.py evaluate --query semiring_provenance\queries\q3_join.sql --semiring how
python semiring_provenance\cli.py explain --query semiring_provenance\queries\q1_select.sql --missing "i_name=Meprobamate,i_price=11.64"
python semiring_provenance\cli.py benchmark correctness
python semiring_provenance\cli.py benchmark performance
```

## AI Declaration 
This repository includes code and content generated with the assistance of AI tools, including Claude, and has been reviewed and validated by the author.



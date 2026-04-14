# Semiring Provenance

This folder contains the semiring-based why-not provenance implementation for the project.

## Main Contents

- `src/`: parser, annotator, evaluator, semirings, why-not engine, and explainer
- `queries/`: sample SQL workload
- `benchmark/`: correctness and performance benchmarks
- `TPC_C_export/`: schema and data-loading SQL for the TPC-C subset
- `cli.py`: main command-line entry point
- `main.py`: quick runner over the sample queries

## Typical Commands

```powershell
python semiring_provenance\cli.py tree --query semiring_provenance\queries\q1_select.sql
python semiring_provenance\cli.py evaluate --query semiring_provenance\queries\q3_join.sql --semiring how
python semiring_provenance\cli.py explain --query semiring_provenance\queries\q1_select.sql --missing "i_name=Meprobamate,i_price=11.64"
python semiring_provenance\benchmark\run_semiring_benchmark.py > submission_documents\results\semiring_results.csv
python semiring_provenance\benchmark\run_firing_rules_benchmark.py > submission_documents\results\firing_rules_results.csv
```

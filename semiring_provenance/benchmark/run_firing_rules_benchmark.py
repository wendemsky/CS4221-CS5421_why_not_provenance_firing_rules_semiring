# benchmark/run_firing_rules_benchmark.py
#
# Firing-rules-side performance benchmark.
#
# Uses the same query_spec.py as the semiring benchmark so both sides
# operate on identical logical queries over the same tpcc_db PostgreSQL
# database.
#
# How the firing rules system loads data:
#   When WHY_NOT_DB_CONNECTION is set, the engine automatically fetches every
#   table mentioned in rule body goals (warehouses, items, stocks) from
#   PostgreSQL at the start of each explain_why_not() call. No manual EDB
#   loading is needed - this is equivalent to our annotator's get_k_relation().
#
# Space metrics recorded (firing rules side):
#   failed_derivations  - number of failed derivation records returned
#   total_goals         - total goal results across all failed derivations
#                         (measures depth/width of the explanation tree)
#   json_chars          - serialised JSON size of the full result dict
#                         (closest proxy to in-memory footprint)
#
# Output: CSV written to stdout (redirect to file for analysis).
#
# Usage:
#   python semiring_provenance\benchmark\run_firing_rules_benchmark.py `
#       > submission_documents\results\firing_rules_results.csv
#
# Requires .env in the project root with DB_USER, DB_PASSWORD, DB_HOST etc.

import csv
import json
import os
import statistics
import sys
import time

_SEMIRING_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(_SEMIRING_ROOT)
_FR_PACKAGE_DIR = os.path.join(_REPO_ROOT, "rule_firing", "firing_rules")

sys.path.insert(0, _SEMIRING_ROOT)
sys.path.insert(0, _FR_PACKAGE_DIR)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(_REPO_ROOT, ".env"))

_db_user = os.getenv("DB_USER", "postgres")
_db_pass = os.getenv("DB_PASSWORD", "")
_db_host = os.getenv("DB_HOST", "localhost")
_db_port = os.getenv("DB_PORT", "5432")
_db_name = os.getenv("DB_NAME", "tpcc_db")

_CONN_STR = f"postgresql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}"
os.environ["WHY_NOT_DB_CONNECTION"] = _CONN_STR

from provenance.api import explain_why_not  # noqa: E402
from benchmark.query_spec import QUERIES  # noqa: E402

N_RUNS = 5

FIELDNAMES = [
    "query_id",
    "operator_type",
    "time_ms_median",
    "time_ms_min",
    "time_ms_max",
    "failed_derivations",
    "total_goals",
    "json_chars",
]


def measure_space(result: dict) -> tuple:
    """Extract space metrics from an explain_why_not() result."""
    n_derivations = result.get("failed_derivation_count", 0)
    n_goals = sum(
        len(d.get("goal_results", []))
        for d in result.get("failed_derivations", [])
    )
    json_chars = len(json.dumps(result))
    return n_derivations, n_goals, json_chars


def run_benchmark():
    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDNAMES)
    writer.writeheader()

    for q in QUERIES:
        qid = q["id"]
        qtype = q["operator_type"]
        rules_text = "\n".join(q["datalog_rules"])
        program = f"{rules_text}\nWHYNOT {q['whynot_target']}"

        times = []
        result = None

        for run_idx in range(N_RUNS):
            try:
                t0 = time.perf_counter()
                result = explain_why_not(program)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                times.append(elapsed_ms)
            except Exception as exc:
                print(f"# RUN ERROR {qid} run {run_idx}: {exc}", file=sys.stderr)
                break

        if not times or result is None:
            print(f"# SKIP {qid}: no successful runs", file=sys.stderr)
            continue

        if result.get("failed_derivation_count", 0) == 0:
            print(
                f"# WARN {qid}: failed_derivation_count=0 - "
                f"target {q['whynot_target']} may actually be present in the result.",
                file=sys.stderr,
            )

        n_derivations, n_goals, json_chars = measure_space(result)

        writer.writerow({
            "query_id": qid,
            "operator_type": qtype,
            "time_ms_median": round(statistics.median(times), 3),
            "time_ms_min": round(min(times), 3),
            "time_ms_max": round(max(times), 3),
            "failed_derivations": n_derivations,
            "total_goals": n_goals,
            "json_chars": json_chars,
        })

        print(f"# done {qid} ({qtype})", file=sys.stderr)

    print(f"\n# Connection used: {_CONN_STR.split('@')[1]}", file=sys.stderr)


if __name__ == "__main__":
    run_benchmark()

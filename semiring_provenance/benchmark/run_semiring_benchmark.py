# benchmark/run_semiring_benchmark.py
#
# Semiring-side performance benchmark.
#
# For each of the 16 queries in query_spec.py, this script:
#
#   1. Parses the SQL and evaluates it against tpcc_db with all four semirings.
#   2. Runs each (query, semiring) pair N_RUNS times and takes the median time.
#   3. Measures three space metrics on the output K-relation:
#        annotation_terms  - total number of top-level terms across all output
#                            tuples (witness sets for Why, monomials for How).
#        annotation_tokens - total base-tuple token references across all
#                            output tuples (sum of witness/monomial sizes).
#        annotation_chars  - total serialised character length of all
#                            annotations (proxy for memory footprint).
#
# Output: CSV written to stdout (redirect to a file for analysis).
#
# Usage:
#   python semiring_provenance\benchmark\run_semiring_benchmark.py `
#       > submission_documents\results\semiring_results.csv
#
# The firing rules side produces a CSV with the same query_id and
# operator_type columns so the two files can be joined for comparison.

import csv
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.annotator import Annotator, get_connection
from src.evaluator import Evaluator
from src.parser import parse_query
from src.semirings import BooleanSemiring, BagSemiring, WhyProvenance, HowProvenance
from benchmark.query_spec import QUERIES

N_RUNS = 5

SEMIRINGS = [
    ("boolean", BooleanSemiring()),
    ("bag", BagSemiring()),
    ("why", WhyProvenance()),
    ("how", HowProvenance()),
]

FIELDNAMES = [
    "query_id",
    "operator_type",
    "semiring",
    "time_ms_median",
    "time_ms_min",
    "time_ms_max",
    "output_tuples",
    "annotation_terms",
    "annotation_tokens",
    "annotation_chars",
]


def _annotation_terms(annotation) -> int:
    if isinstance(annotation, (bool, int)):
        return 1
    if isinstance(annotation, frozenset):
        return len(annotation)
    if isinstance(annotation, dict):
        return len(annotation)
    return 1


def _annotation_tokens(annotation) -> int:
    if isinstance(annotation, (bool, int)):
        return 1
    if isinstance(annotation, frozenset):
        return sum(len(w) for w in annotation)
    if isinstance(annotation, dict):
        return sum(len(m) for m in annotation.keys())
    return 1


def measure_space(k_relation):
    total_terms = sum(_annotation_terms(row["_annotation"]) for row in k_relation)
    total_tokens = sum(_annotation_tokens(row["_annotation"]) for row in k_relation)
    total_chars = sum(len(repr(row["_annotation"])) for row in k_relation)
    return total_terms, total_tokens, total_chars


def run_once(annotator, tree, semiring) -> tuple:
    evaluator = Evaluator(annotator, semiring)
    t0 = time.perf_counter()
    trace = evaluator.evaluate(tree)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return elapsed_ms, trace


def run_benchmark():
    conn = get_connection()
    annotator = Annotator(conn)

    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDNAMES)
    writer.writeheader()

    skipped = []

    for q in QUERIES:
        qid = q["id"]
        qtype = q["operator_type"]

        if q["sql"] is None:
            skipped.append(qid)
            print(f"# SKIP {qid} ({qtype}): sql=None", file=sys.stderr)
            continue

        try:
            tree = parse_query(q["sql"])
        except Exception as exc:
            print(f"# PARSE ERROR {qid}: {exc}", file=sys.stderr)
            continue

        for sr_name, semiring in SEMIRINGS:
            times = []
            trace = None

            for _ in range(N_RUNS):
                try:
                    elapsed, trace = run_once(annotator, tree, semiring)
                    times.append(elapsed)
                except Exception as exc:
                    print(f"# RUN ERROR {qid} [{sr_name}]: {exc}", file=sys.stderr)
                    break

            if not times:
                continue

            n_out = len(trace.k_relation)
            terms, tokens, chars = measure_space(trace.k_relation)

            writer.writerow({
                "query_id": qid,
                "operator_type": qtype,
                "semiring": sr_name,
                "time_ms_median": round(statistics.median(times), 3),
                "time_ms_min": round(min(times), 3),
                "time_ms_max": round(max(times), 3),
                "output_tuples": n_out,
                "annotation_terms": terms,
                "annotation_tokens": tokens,
                "annotation_chars": chars,
            })

        print(f"# done {qid}", file=sys.stderr)

    if skipped:
        print(
            f"\n# Skipped {len(skipped)} JOIN_3WAY queries: {skipped}",
            file=sys.stderr,
        )

    conn.close()


if __name__ == "__main__":
    run_benchmark()

"""
main.py - Run all sample queries with all semirings and display K-relation output.
"""

import os

from src.parser import parse_query
from src.annotator import Annotator, get_connection
from src.evaluator import Evaluator
from src.semirings import BooleanSemiring, BagSemiring, WhyProvenance, HowProvenance

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

QUERIES = [
    ("Q1 - SELECT filter", os.path.join(BASE_DIR, "queries", "q1_select.sql")),
    ("Q2 - PROJECT + SELECT", os.path.join(BASE_DIR, "queries", "q2_project.sql")),
    ("Q3 - JOIN with filter", os.path.join(BASE_DIR, "queries", "q3_join.sql")),
    ("Q4 - UNION", os.path.join(BASE_DIR, "queries", "q4_union.sql")),
]

SEMIRINGS = [
    BooleanSemiring(),
    BagSemiring(),
    WhyProvenance(),
    HowProvenance(),
]


def load_sql(path):
    with open(path) as f:
        return "\n".join(
            line for line in f
            if not line.strip().startswith("--") and line.strip()
        )


def print_result(rows, semiring):
    if not rows:
        print("  (empty result)")
        return
    cols = [k for k in rows[0] if not k.startswith("_")]
    col_w = 18
    header = "  ".join(f"{c:<{col_w}}" for c in cols) + "  ANNOTATION"
    print("  " + header)
    print("  " + "-" * len(header))
    for row in rows[:10]:  # cap at 10 rows for readability
        vals = "  ".join(f"{str(row[c]):<{col_w}}" for c in cols)
        annot = semiring.display(row["_annotation"])
        print(f"  {vals}  {annot}")
    if len(rows) > 10:
        print(f"  ... ({len(rows) - 10} more rows)")


def main():
    conn = get_connection()
    annotator = Annotator(conn)

    for q_label, q_file in QUERIES:
        sql = load_sql(q_file)
        tree = parse_query(sql)

        print(f"\n{'=' * 70}")
        print(f"  {q_label}")
        print(f"  SQL: {sql.strip()}")
        print(f"{'=' * 70}")

        for semiring in SEMIRINGS:
            evaluator = Evaluator(annotator, semiring)
            trace = evaluator.evaluate(tree)
            rows = trace.k_relation
            print(f"\n  [{type(semiring).__name__}]  ({len(rows)} tuples)")
            print_result(rows, semiring)

    conn.close()


if __name__ == "__main__":
    main()

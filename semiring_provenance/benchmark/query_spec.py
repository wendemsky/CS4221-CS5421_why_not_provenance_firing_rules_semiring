# benchmark/query_spec.py
#
# Shared TPC-C Performance Evaluation Query Suite — 16 queries
#
# Used by BOTH the semiring provenance system and the firing rules system
# for a directly comparable time and space analysis.
#
# 3-way JOIN queries were removed: the semiring parser supports only one JOIN
# clause, so those queries cannot be evaluated on the semiring side and would
# produce no comparable data point. Both systems run the same 16 queries.
#
# Schema:
#   items(i_id, i_im_id, i_name, i_price)
#   warehouses(w_id, w_name, w_street, w_city, w_country)
#   stocks(w_id, i_id, s_qty)
#
# Known TPC-C values used for WHYNOT targets:
#   Warehouse 1   : DabZ,      Indonesia  (w_id=1)
#   Warehouse 7   : Blogpad,   Malaysia   (w_id=7)
#   Warehouse 281 : Crescent Oaks, Singapore (w_id=281)
#   Warehouse 301 : Schmedeman,   Singapore (w_id=301)
#   Item 1  : Indapamide,        price=95.23
#   Item 2  : SYLATRON,          price=80.22
#   Item 3  : Meprobamate,       price=11.64
#   Item 9  : TOPIRAMATE,        price=48.58
#   stocks(301, 1, 338)   qty=338
#   stocks(281, 2, 9)     qty=9
#   stocks(7,   2, 2)     qty=2
#
# Each entry has:
#   id             : Q01–Q20
#   description    : human-readable label
#   operator_type  : SELECT | PROJECT | JOIN_2WAY | JOIN_3WAY | UNION_2 | UNION_3
#   sql            : SQL string for the semiring side
#                    None  →  requires chained JOIN; semiring side skips this query
#   datalog_rules  : list of rule strings for the firing rules side
#   whynot_target  : the specific missing tuple (firing rules WHYNOT argument)
#   missing_reason : plain-English explanation of why the tuple is absent

QUERIES = [

    # =========================================================================
    # GROUP 1 — SELECT  (σ)
    # Single-table filter; the simplest operator.
    # Expected behaviour: both systems fast; annotation size trivially small.
    # =========================================================================

    {
        "id": "Q01",
        "description": "Filter warehouses in Singapore (single equality predicate)",
        "operator_type": "SELECT",
        "sql": (
            "SELECT w_id, w_name, w_country "
            "FROM warehouses "
            "WHERE w_country = 'Singapore'"
        ),
        "datalog_rules": [
            "r1: Q(W_ID) :- warehouses(W_ID,W_NAME,W_STREET,W_CITY,W_COUNTRY), "
            "W_COUNTRY = Singapore."
        ],
        "whynot_target": "Q(1)",
        "missing_reason": "Warehouse 1 (DabZ) is in Indonesia; equality filter fails.",
    },

    {
        "id": "Q02",
        "description": "Filter items with price > 50 (single range predicate)",
        "operator_type": "SELECT",
        "sql": (
            "SELECT i_id, i_name, i_price "
            "FROM items "
            "WHERE i_price > 50"
        ),
        "datalog_rules": [
            "r1: Q(I_ID) :- items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 50."
        ],
        "whynot_target": "Q(3)",
        "missing_reason": "Item 3 (Meprobamate) has price=11.64; price > 50 fails.",
    },

    {
        "id": "Q03",
        "description": "Filter items with 30 < price < 90 (two range predicates, AND)",
        "operator_type": "SELECT",
        "sql": (
            "SELECT i_id, i_name, i_price "
            "FROM items "
            "WHERE i_price > 30 AND i_price < 90"
        ),
        "datalog_rules": [
            "r1: Q(I_ID) :- items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 30, I_PRICE < 90."
        ],
        "whynot_target": "Q(1)",
        "missing_reason": "Item 1 (Indapamide) price=95.23; fails the upper bound (< 90).",
    },

    {
        "id": "Q04",
        "description": "Filter stocks with qty > 500 (range on numeric column)",
        "operator_type": "SELECT",
        "sql": (
            "SELECT w_id, i_id, s_qty "
            "FROM stocks "
            "WHERE s_qty > 500"
        ),
        "datalog_rules": [
            "r1: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), S_QTY > 500."
        ],
        "whynot_target": "Q(301,1)",
        "missing_reason": "stocks(301,1) has qty=338; qty > 500 fails.",
    },

    # =========================================================================
    # GROUP 2 — PROJECT  (π)
    # Column projection; duplicate output tuples fold via semiring.add().
    # Expected behaviour: Why/How annotations grow when rows collapse to same key.
    # =========================================================================

    {
        "id": "Q05",
        "description": "Project single column: country of Singapore warehouses",
        "operator_type": "PROJECT",
        "sql": (
            "SELECT w_country "
            "FROM warehouses "
            "WHERE w_country = 'Singapore'"
        ),
        "datalog_rules": [
            "r1: Q(W_COUNTRY) :- warehouses(W_ID,W_NAME,W_STREET,W_CITY,W_COUNTRY), "
            "W_COUNTRY = Singapore."
        ],
        "whynot_target": "Q(Indonesia)",
        "missing_reason": "No warehouse exists with country=Indonesia that also passes country=Singapore.",
    },

    {
        "id": "Q06",
        "description": "Project two columns: name and price of items with price > 50",
        "operator_type": "PROJECT",
        "sql": (
            "SELECT i_name, i_price "
            "FROM items "
            "WHERE i_price > 50"
        ),
        "datalog_rules": [
            "r1: Q(I_NAME,I_PRICE) :- items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 50."
        ],
        "whynot_target": "Q(Meprobamate,11.64)",
        "missing_reason": "Meprobamate has price=11.64; fails price > 50.",
    },

    # =========================================================================
    # GROUP 3 — 2-WAY JOIN  (⋈)
    # Two tables joined on a shared key, with varying filter complexity.
    # Annotation size grows multiplicatively per join pair.
    # =========================================================================

    {
        "id": "Q07",
        "description": "Join stocks and items; filter qty > 500",
        "operator_type": "JOIN_2WAY",
        "sql": (
            "SELECT s.w_id, s.i_id, s.s_qty "
            "FROM stocks s JOIN items i ON s.i_id = i.i_id "
            "WHERE s.s_qty > 500"
        ),
        "datalog_rules": [
            "r1: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "items(I_ID,I_IM_ID,I_NAME,I_PRICE), S_QTY > 500."
        ],
        "whynot_target": "Q(301,1)",
        "missing_reason": "stocks(301,1) qty=338; qty > 500 fails.",
    },

    {
        "id": "Q08",
        "description": "Join stocks and items; filter price > 90",
        "operator_type": "JOIN_2WAY",
        "sql": (
            "SELECT s.w_id, s.i_id, i.i_price "
            "FROM stocks s JOIN items i ON s.i_id = i.i_id "
            "WHERE i.i_price > 90"
        ),
        "datalog_rules": [
            "r1: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 90."
        ],
        "whynot_target": "Q(281,2)",
        "missing_reason": "Item 2 (SYLATRON) price=80.22; price > 90 fails.",
    },

    {
        "id": "Q09",
        "description": "Join stocks and warehouses; filter country = Singapore",
        "operator_type": "JOIN_2WAY",
        "sql": (
            "SELECT s.w_id, s.i_id "
            "FROM stocks s JOIN warehouses w ON s.w_id = w.w_id "
            "WHERE w.w_country = 'Singapore'"
        ),
        "datalog_rules": [
            "r1: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "warehouses(W_ID,W_NAME,W_STREET,W_CITY,W_COUNTRY), W_COUNTRY = Singapore."
        ],
        "whynot_target": "Q(7,2)",
        "missing_reason": "Warehouse 7 is in Malaysia; country = Singapore fails.",
    },

    {
        "id": "Q10",
        "description": "Join stocks and items; filter price > 90 AND qty > 100 (two predicates after join)",
        "operator_type": "JOIN_2WAY",
        "sql": (
            "SELECT s.w_id, s.i_id "
            "FROM stocks s JOIN items i ON s.i_id = i.i_id "
            "WHERE i.i_price > 90 AND s.s_qty > 100"
        ),
        "datalog_rules": [
            "r1: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 90, S_QTY > 100."
        ],
        "whynot_target": "Q(281,2)",
        "missing_reason": "Item 2 price=80.22 fails price>90; stocks(281,2) qty=9 also fails qty>100.",
    },

    # =========================================================================
    # GROUP 5 — UNION 2-BRANCH  (∪)
    # Two rules / two SELECT branches with the same output schema.
    # A tuple is absent only if it fails ALL branches simultaneously.
    # Semiring: duplicate tuples get annotations combined via add().
    # Firing rules: failed_derivation_count covers failures across all rules.
    # =========================================================================

    {
        "id": "Q15",
        "description": "Union: Singapore warehouses ∪ Malaysia warehouses",
        "operator_type": "UNION_2",
        "sql": (
            "SELECT w_id, w_country FROM warehouses WHERE w_country = 'Singapore' "
            "UNION "
            "SELECT w_id, w_country FROM warehouses WHERE w_country = 'Malaysia'"
        ),
        "datalog_rules": [
            "r1: Q(W_ID) :- warehouses(W_ID,W_NAME,W_STREET,W_CITY,W_COUNTRY), "
            "W_COUNTRY = Singapore.",
            "r2: Q(W_ID) :- warehouses(W_ID,W_NAME,W_STREET,W_CITY,W_COUNTRY), "
            "W_COUNTRY = Malaysia.",
        ],
        "whynot_target": "Q(1)",
        "missing_reason": "Warehouse 1 is in Indonesia; fails both r1 (Singapore) and r2 (Malaysia).",
    },

    {
        "id": "Q16",
        "description": "Union: expensive items (price > 90) ∪ very cheap items (price < 20)",
        "operator_type": "UNION_2",
        "sql": (
            "SELECT i_id, i_price FROM items WHERE i_price > 90 "
            "UNION "
            "SELECT i_id, i_price FROM items WHERE i_price < 20"
        ),
        "datalog_rules": [
            "r1: Q(I_ID) :- items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 90.",
            "r2: Q(I_ID) :- items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE < 20.",
        ],
        "whynot_target": "Q(2)",
        "missing_reason": "Item 2 price=80.22; not > 90 (r1 fails) and not < 20 (r2 fails).",
    },

    # =========================================================================
    # GROUP 6 — UNION 3-BRANCH  (∪∪)
    # Three rules / three SELECT branches. Tests annotation accumulation across
    # more branches. A tuple is absent only if it falls outside all three ranges.
    # =========================================================================

    {
        "id": "Q17",
        "description": "3-branch union on items: price>90 ∪ 50<price<90 ∪ price<10",
        "operator_type": "UNION_3",
        "sql": (
            "SELECT i_id, i_price FROM items WHERE i_price > 90 "
            "UNION "
            "SELECT i_id, i_price FROM items WHERE i_price > 50 AND i_price < 90 "
            "UNION "
            "SELECT i_id, i_price FROM items WHERE i_price < 10"
        ),
        "datalog_rules": [
            "r1: Q(I_ID) :- items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 90.",
            "r2: Q(I_ID) :- items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 50, I_PRICE < 90.",
            "r3: Q(I_ID) :- items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE < 10.",
        ],
        "whynot_target": "Q(9)",
        "missing_reason": (
            "Item 9 (TOPIRAMATE) price=48.58: not>90 (r1 fails), "
            "not in (50,90) (r2 fails), not<10 (r3 fails). Falls in gap [10,50]."
        ),
    },

    # =========================================================================
    # GROUP 7 — UNION OF JOINS  (∪ with ⋈ in each branch)
    # Each branch is a 2-way join. Tests annotation growth from combined
    # join multiplication and union addition.
    # =========================================================================

    {
        "id": "Q18",
        "description": "Union of joins: (stocks⋈items, price>90) ∪ (stocks⋈items, qty>500)",
        "operator_type": "UNION_2",
        "sql": (
            "SELECT s.w_id, s.i_id FROM stocks s JOIN items i ON s.i_id = i.i_id "
            "WHERE i.i_price > 90 "
            "UNION "
            "SELECT s.w_id, s.i_id FROM stocks s JOIN items i ON s.i_id = i.i_id "
            "WHERE s.s_qty > 500"
        ),
        "datalog_rules": [
            "r1: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 90.",
            "r2: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "items(I_ID,I_IM_ID,I_NAME,I_PRICE), S_QTY > 500.",
        ],
        "whynot_target": "Q(301,2)",
        "missing_reason": (
            "stocks(301,2) qty=6: price=80.22 not>90 (r1 fails), qty=6 not>500 (r2 fails)."
        ),
    },

    {
        "id": "Q19",
        "description": "Union of joins: (stocks⋈warehouses, Singapore) ∪ (stocks⋈warehouses, Malaysia)",
        "operator_type": "UNION_2",
        "sql": (
            "SELECT s.w_id, s.i_id FROM stocks s JOIN warehouses w ON s.w_id = w.w_id "
            "WHERE w.w_country = 'Singapore' "
            "UNION "
            "SELECT s.w_id, s.i_id FROM stocks s JOIN warehouses w ON s.w_id = w.w_id "
            "WHERE w.w_country = 'Malaysia'"
        ),
        "datalog_rules": [
            "r1: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "warehouses(W_ID,W_NAME,W_STREET,W_CITY,W_COUNTRY), W_COUNTRY = Singapore.",
            "r2: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "warehouses(W_ID,W_NAME,W_STREET,W_CITY,W_COUNTRY), W_COUNTRY = Malaysia.",
        ],
        "whynot_target": "Q(1,2)",
        "missing_reason": (
            "Warehouse 1 is in Indonesia; fails both r1 (Singapore) and r2 (Malaysia)."
        ),
    },

    {
        "id": "Q20",
        "description": (
            "3-branch union of joins: "
            "(stocks⋈items, price>90) ∪ "
            "(stocks⋈items, 50<price<90 AND qty>100) ∪ "
            "(stocks⋈items, qty>500 AND price<50)"
        ),
        "operator_type": "UNION_3",
        "sql": (
            "SELECT s.w_id, s.i_id FROM stocks s JOIN items i ON s.i_id = i.i_id "
            "WHERE i.i_price > 90 "
            "UNION "
            "SELECT s.w_id, s.i_id FROM stocks s JOIN items i ON s.i_id = i.i_id "
            "WHERE i.i_price > 50 AND i.i_price < 90 AND s.s_qty > 100 "
            "UNION "
            "SELECT s.w_id, s.i_id FROM stocks s JOIN items i ON s.i_id = i.i_id "
            "WHERE s.s_qty > 500 AND i.i_price < 50"
        ),
        "datalog_rules": [
            "r1: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 90.",
            "r2: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "items(I_ID,I_IM_ID,I_NAME,I_PRICE), I_PRICE > 50, I_PRICE < 90, S_QTY > 100.",
            "r3: Q(W_ID,I_ID) :- stocks(W_ID,I_ID,S_QTY), "
            "items(I_ID,I_IM_ID,I_NAME,I_PRICE), S_QTY > 500, I_PRICE < 50.",
        ],
        "whynot_target": "Q(7,2)",
        "missing_reason": (
            "stocks(7,2) qty=2, item 2 price=80.22: "
            "price not>90 (r1 fails), price in (50,90) but qty=2 not>100 (r2 fails), "
            "qty not>500 (r3 fails)."
        ),
    },
]

# ---------------------------------------------------------------------------
# Quick lookup helpers
# ---------------------------------------------------------------------------

QUERY_BY_ID = {q["id"]: q for q in QUERIES}

QUERIES_BY_OPERATOR = {}
for q in QUERIES:
    QUERIES_BY_OPERATOR.setdefault(q["operator_type"], []).append(q)

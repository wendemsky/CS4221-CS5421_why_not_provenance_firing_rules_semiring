# Implementation Details

## 1. Overview

This system implements a **firing-rules WHY-NOT provenance engine** for a constrained Datalog + SQL setting.
Given a provenance query such as `WHYNOT Q(301,1)`, it explains why a tuple is missing by:

1. normalizing mixed input (facts, rules, SQL, question),
2. enumerating candidate derivations for the target tuple,
3. evaluating each body goal (success/failure), and
4. returning both tabular and graph-shaped explanations.

The runtime is organized as a pipeline:

- **Entry layer** (CLI/API)
- **Input normalization** (parser + optional PostgreSQL loading + SQL parsing/lowering)
- **WHY-NOT evaluation engine**
- **JSON output generation**

---

## 2. Module Responsibilities

- `firing_rules/why_not_provenance.py`  
  CLI wrapper; reads from argv/stdin and prints JSON.

- `firing_rules/provenance/api.py`  
  Minimal API exposing `explain_why_not(query_text)`.

- `firing_rules/provenance/input_parser.py`  
  Parses mixed input blocks, resolves connection strings, optionally loads base tables and executes SQL, and builds a normalized `Program` object.

- `firing_rules/provenance/sql_rule_builder.py`  
  Parses supported SQL subset and lowers each SQL block to a Datalog-like `Rule`.

- `firing_rules/provenance/engine.py`  
  Core WHY-NOT evaluator: materialization, binding generation, goal checks, failed-derivation collection, explanation graph construction.

- `firing_rules/provenance/helpers.py`  
  Shared parsing/evaluation utilities (atom/goal parsing, top-level splitting, variable detection, comparison evaluation).

- `firing_rules/provenance/postgres_backend.py`  
  PostgreSQL adapter (table loading and SQL execution with row normalization).

- `firing_rules/provenance/models/*`  
  Dataclasses representing `Atom`, `Goal`, `Rule`, `Program`, and question metadata.

---

## 3. Internal Data Model

### 3.1 Program IR
The parser emits a `Program` object containing:

- `edb`: dictionary from predicate -> list of tuples,
- `schemas`: predicate -> column names,
- `rules`: explicit Datalog rules + SQL-translated rules,
- `question`: provenance question (`mode`, target atom),
- optional SQL execution payloads (`sql_queries`, `sql_results`).

### 3.2 Goal kinds
Each rule body goal has one of three kinds:

- `pos`: positive relational atom (must exist),
- `neg`: negated relational atom (`not R(...)` must hold),
- `cmp`: scalar comparison (`=, !=, <, <=, >, >=`).

### 3.3 Value conventions
- Facts and DB rows are normalized to strings.
- Comparisons attempt numeric coercion when both sides are numeric; otherwise string comparison is used.
- Variables follow an ALL_CAPS pattern (`[A-Z_][A-Z0-9_]*`) to avoid confusing literals (e.g., `Singapore`) with variables.

---

## 4. Algorithm A: Input Parsing and Normalization

### 4.1 Supported blocks
The parser scans input line-by-line and accepts:

- `SCHEMA ...`
- EDB facts (`R(a,b).`)
- rules (`r1: Q(X) :- ...`)
- SQL blocks (`SELECT ...;` or `SQL: SELECT ...;`)
- provenance question (`WHYNOT ...` or `WHY ...`, but execution path is WHYNOT-only)
- optional DB connection directive (`CONNECTION: ...`)

### 4.2 Connection resolution
Connection string lookup order:

1. `.env` / environment variable `WHY_NOT_DB_CONNECTION`
2. `DATABASE_URL`
3. `POSTGRES_CONNECTION_STRING`
4. inline connection directive in input (if present)

### 4.3 Optional PostgreSQL stage
If a connection string is present:

1. referenced tables are discovered (from SQL `FROM/JOIN` and rule body base predicates),
2. base rows are fetched into `edb`,
3. SQL blocks are executed and raw rows stored in `sql_results`.

Table loading and SQL execution can run concurrently with a worker count controlled by `WHY_NOT_MAX_WORKERS`.

---

## 5. Algorithm B: SQL-to-Rule Lowering

Each SQL block is translated into one Datalog-like rule.

### 5.1 SQL subset handled
- `SELECT ... FROM ...`
- `JOIN ... ON ...`
- `WHERE` with conjunctions (`AND`)
- comparisons (`=, !=, <, <=, >, >=`)
- limited `NOT EXISTS (SELECT ... FROM table alias WHERE alias.col = ...)`

### 5.2 Lowering strategy
Given a parsed SQL query:

1. For each table reference, create a positive atom goal with synthetic variables (e.g., `S_W_ID`, `I_I_PRICE`).
2. Convert join and where predicates into:
   - comparison goals, or
   - a negated atom goal for `NOT EXISTS`.
3. Convert selected expressions into head terms.
4. Emit a rule `sql_rk: Head :- goals...`.

If there is exactly one SQL block, its head predicate matches the provenance question predicate; with multiple SQL blocks, heads are `QSQL1`, `QSQL2`, etc.

---

## 6. Algorithm C: WHY-NOT Evaluation Engine

Let `target = Q(t1,...,tn)`.

### 6.1 Phase 1: Relation initialization and head materialization
1. Initialize relation store from `Program.edb`.
2. For each rule:
   - compute variable domains from active constants,
   - generate candidate bindings using join-driven positive-goal unification,
   - evaluate each binding and materialize successful heads into relation store.

This enriches relations before provenance filtering.

### 6.2 Phase 2: Target-rule filtering
1. Keep only rules whose head predicate equals `target.predicate`.
2. For each target rule, constrain head variables to target tuple values.
3. Enumerate bindings and evaluate body goals.
4. Keep records where grounded head equals the target tuple and overall status is `false`.

### 6.3 Binding generation details
The engine uses a two-step strategy:

1. **Join-driven step:** recursively unify positive body atoms against relation rows.
2. **Expansion step:** enumerate remaining unbound variables via Cartesian products over domains.

This reduces search compared with fully naive enumeration.

### 6.4 Goal evaluation rules
For each grounded goal:

- Positive atom: success iff tuple exists in relation.
- Negated atom: success iff tuple does **not** exist.
- Comparison: success iff comparison evaluates true after term resolution.

Each firing record stores:

- `rule_id`
- full `binding`
- per-goal list (`goal_index`, grounded `goal`, `ok`)
- aggregate `status`

### 6.5 Explanation graph construction
For each failed record:

1. add a missing tuple node,
2. add a failed rule-instance node (rule id + binding),
3. add nodes only for failed goals,
4. connect edges `tuple -> failed rule -> failed goals`.

### 6.6 Concurrency
Failed-derivation collection across target rules can execute in parallel using `ThreadPoolExecutor`. Results are reassembled in rule order for deterministic output shape.

---

## 7. Output Structure

The engine returns JSON with:

- `mode`
- `target`
- `failed_derivation_count`
- `failed_derivations`
- `explanation_graph`
- `query_results`
- `message`

This supports both machine processing (`failed_derivations`) and direct visualization (`explanation_graph`).

---

## 8. Example Input/Output (Datalog)

### Input
```text
Train(n,c).
Train(c,s).
Train(n,w).
Train(w,s).
r1: Q(X,Y) :- Train(X,Z), Train(Z,Y), X = Y.
WHYNOT Q(n,s)
```

### Output (excerpt)
```json
{
  "mode": "WHYNOT",
  "target": "Q(n, s)",
  "failed_derivation_count": 2,
  "failed_derivations": [
    {
      "rule_id": "r1",
      "binding": {"X": "n", "Y": "s", "Z": "c"},
      "goal_results": [
        {"goal_index": 1, "goal": "Train(n, c)", "ok": true},
        {"goal_index": 2, "goal": "Train(c, s)", "ok": true},
        {"goal_index": 3, "goal": "n = s", "ok": false}
      ],
      "status": false
    }
  ],
  "message": "Tuple is missing because every relevant derivation failed."
}
```

Interpretation: candidate joins exist, but the comparison `n = s` fails for each relevant binding.

---

## 9. Example Input/Output (SQL block lowered to rule)

### Input
```text
SCHEMA items(i_id,i_price).
SCHEMA stocks(w_id,i_id,s_qty).
items(1,95.23).
items(2,120).
stocks(301,1,338).
stocks(301,2,10).

SELECT s.w_id, s.i_id
FROM stocks s
JOIN items i ON s.i_id = i.i_id
WHERE i.i_price > 99;

WHYNOT Q(301,1)
```

### Output (excerpt)
```json
{
  "mode": "WHYNOT",
  "target": "Q(301, 1)",
  "failed_derivation_count": 2,
  "failed_derivations": [
    {
      "rule_id": "sql_r1",
      "binding": {
        "S_W_ID": "301",
        "S_I_ID": "1",
        "I_I_ID": "1",
        "I_I_PRICE": "95.23"
      },
      "goal_results": [
        {"goal_index": 3, "goal": "1 = 1", "ok": true},
        {"goal_index": 4, "goal": "95.23 > 99", "ok": false}
      ],
      "status": false
    }
  ]
}
```

Interpretation: for tuple `(301,1)`, one failure comes from the price filter (`95.23 > 99` false); another candidate binding can fail on join equality (`1 = 2` false).

---

## 10. Practical Notes and Limits

- Effective explanation path is currently **WHYNOT-only**.
- SQL support is intentionally constrained (no aggregates, no OR, no complex nested queries beyond supported pattern).
- Multiple SQL blocks require target predicate alignment (`QSQL1`, `QSQL2`, ...).
- Domain expansion for unbound variables can increase runtime; join-driven binding mitigates this but does not eliminate worst-case combinatorics.

These constraints are deliberate to keep the implementation transparent and auditable for provenance-focused research experiments.

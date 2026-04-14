# config.py
# Loads database connection settings from the repository root .env file.

import os
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, ".env"))

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "tpcc_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

# Primary key column(s) for each TPC-C table.
# Used by the annotator to construct unique provenance tokens per base tuple.
TABLE_PKS = {
    "items": ["i_id"],
    "warehouses": ["w_id"],
    "stocks": ["w_id", "i_id"],
}

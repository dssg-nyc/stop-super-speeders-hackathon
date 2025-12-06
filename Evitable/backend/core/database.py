import duckdb
from pathlib import Path
from functools import lru_cache

DB_PATH = Path("../data/duckdb/test.duckdb")
DATA_DIR = Path("../data/opendata")

class Database:
    def __init__(self):
        self.con = None

    def connect(self):
        if self.con:
            return self.con
        
        # Ensure directory exists
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"🔌 Connecting to DuckDB at {DB_PATH}")
        self.con = duckdb.connect(str(DB_PATH), read_only=False)
        self.con.execute("INSTALL httpfs; LOAD httpfs;")
        return self.con

    def get_connection(self):
        if not self.con:
            self.connect()
        return self.con

    def close(self):
        if self.con:
            self.con.close()
            self.con = None

@lru_cache()
def get_db():
    db = Database()
    db.connect()
    return db

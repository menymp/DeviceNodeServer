# db.py
import aiomysql
import json
import os
from typing import List, Dict, Any
from datetime import datetime

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD_FILE = os.getenv("DB_PASSWORD_FILE", None)
DB_NAME = os.getenv("DB_NAME", "appdb")

def _read_secret(path):
    if not path:
        return os.getenv("DB_PASSWORD", "")
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception:
        return os.getenv("DB_PASSWORD", "")

DB_PASSWORD = _read_secret(DB_PASSWORD_FILE)

class SchedulerDB:
    def __init__(self):
        self.pool = None

    async def init(self):
        self.pool = await aiomysql.create_pool(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME,
            autocommit=True, minsize=1, maxsize=5
        )

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def fetch_rules(self) -> List[Dict[str, Any]]:
        """
        Fetch enabled rules only (used for initial scheduling and resets).
        Returns list of dicts with parsed JSON and updated_at as datetime.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id, name, enabled, rule_json, safe_state, updated_at FROM scheduler_rules WHERE enabled = 1")
                rows = await cur.fetchall()
                return [self._normalize_row(r) for r in rows]

    async def fetch_all_rules(self) -> List[Dict[str, Any]]:
        """
        Fetch all rules (enabled or not) for change detection.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id, name, enabled, rule_json, safe_state, updated_at FROM scheduler_rules")
                rows = await cur.fetchall()
                return [self._normalize_row(r) for r in rows]

    def _normalize_row(self, r: Dict[str, Any]) -> Dict[str, Any]:
        # parse JSON fields if returned as strings
        if isinstance(r.get('rule_json'), (str, bytes)):
            r['rule_json'] = json.loads(r['rule_json'])
        if isinstance(r.get('safe_state'), (str, bytes)):
            r['safe_state'] = json.loads(r['safe_state'])
        # ensure updated_at is datetime
        if isinstance(r.get('updated_at'), str):
            try:
                r['updated_at'] = datetime.fromisoformat(r['updated_at'])
            except Exception:
                r['updated_at'] = None
        return r

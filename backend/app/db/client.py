"""Supabase client management and tenant connection factory."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from backend.app.config import get_settings

logger = logging.getLogger("payfilter.db")

_supabase_client = None


class InMemorySupabaseTable:
    """In-memory table simulator for testing when external Supabase is offline."""

    def __init__(self, table_name: str, db_store: Dict[str, List[Dict[str, Any]]]):
        self.table_name = table_name
        self.db_store = db_store
        if table_name not in self.db_store:
            self.db_store[table_name] = []
        self._filters = []
        self._order_col = None
        self._order_desc = False
        self._limit_val = None
        self._offset_val = 0

    def select(self, columns: str = "*", count: Optional[str] = None):
        self._select_cols = columns
        self._count_mode = count
        return self

    def insert(self, values: Any):
        rows_to_insert = values if isinstance(values, list) else [values]
        import copy
        import uuid
        from datetime import datetime, timezone

        inserted = []
        for r in rows_to_insert:
            item = copy.deepcopy(r)
            if "id" not in item or not item["id"]:
                item["id"] = str(uuid.uuid4())
            if "created_at" not in item or not item["created_at"]:
                item["created_at"] = datetime.now(timezone.utc).isoformat()
            self.db_store[self.table_name].append(item)
            inserted.append(item)

        class Result:
            data = inserted
            count = len(inserted)

        return Result()

    def update(self, values: Dict[str, Any]):
        class ExecutableUpdate:
            def __init__(self, table, vals):
                self.table = table
                self.vals = vals
                self._filters = []

            def eq(self, col, val):
                self._filters.append((col, val))
                return self

            def execute(self):
                # Check append-only restriction
                if self.table.table_name == "audit_log":
                    raise RuntimeError("Permission denied: audit_log is strictly append-only")
                matched = []
                for row in self.table.db_store[self.table.table_name]:
                    match = True
                    for col, val in self._filters:
                        if str(row.get(col)) != str(val):
                            match = False
                            break
                    if match:
                        row.update(self.vals)
                        matched.append(row)

                class Result:
                    data = matched

                return Result()

        return ExecutableUpdate(self, values)

    def delete(self):
        class ExecutableDelete:
            def __init__(self, table):
                self.table = table
                self._filters = []

            def eq(self, col, val):
                self._filters.append((col, val))
                return self

            def execute(self):
                if self.table.table_name == "audit_log":
                    raise RuntimeError("Permission denied: audit_log is strictly append-only")
                to_delete = []
                for row in self.table.db_store[self.table.table_name]:
                    match = True
                    for col, val in self._filters:
                        if str(row.get(col)) != str(val):
                            match = False
                            break
                    if match:
                        to_delete.append(row)
                for item in to_delete:
                    self.table.db_store[self.table.table_name].remove(item)

                class Result:
                    data = to_delete

                return Result()

        return ExecutableDelete(self)

    def eq(self, col: str, val: Any):
        self._filters.append(("eq", col, val))
        return self

    def lt(self, col: str, val: Any):
        self._filters.append(("lt", col, val))
        return self

    def lte(self, col: str, val: Any):
        self._filters.append(("lte", col, val))
        return self

    def gt(self, col: str, val: Any):
        self._filters.append(("gt", col, val))
        return self

    def gte(self, col: str, val: Any):
        self._filters.append(("gte", col, val))
        return self

    def order(self, column: str, desc: bool = False):
        self._order_col = column
        self._order_desc = desc
        return self

    def limit(self, count: int):
        self._limit_val = count
        return self

    def offset(self, start: int):
        self._offset_val = start
        return self

    def range(self, start: int, end: int):
        self._offset_val = start
        self._limit_val = (end - start) + 1
        return self

    def single(self):
        self._limit_val = 1
        self._single = True
        return self

    def execute(self):
        import copy
        results = copy.deepcopy(self.db_store[self.table_name])

        # Apply filters
        for op, col, val in self._filters:
            if op == "eq":
                results = [r for r in results if str(r.get(col)) == str(val)]
            elif op == "lt":
                results = [r for r in results if r.get(col) is not None and str(r.get(col)) < str(val)]
            elif op == "lte":
                results = [r for r in results if r.get(col) is not None and str(r.get(col)) <= str(val)]
            elif op == "gt":
                results = [r for r in results if r.get(col) is not None and str(r.get(col)) > str(val)]
            elif op == "gte":
                results = [r for r in results if r.get(col) is not None and str(r.get(col)) >= str(val)]

        total_count = len(results)

        # Ordering
        if self._order_col:
            results.sort(
                key=lambda x: str(x.get(self._order_col, "")),
                reverse=self._order_desc,
            )

        # Slicing
        start = self._offset_val
        if self._limit_val is not None:
            end = start + self._limit_val
            results = results[start:end]
        else:
            results = results[start:]

        class Result:
            data = results[0] if getattr(self, "_single", False) and results else (None if getattr(self, "_single", False) else results)
            count = total_count

        return Result()


class InMemorySupabaseClient:
    """Mock Supabase client providing isolated table storage for testing."""

    def __init__(self, current_merchant_id: Optional[str] = None):
        self.db_store: Dict[str, List[Dict[str, Any]]] = {
            "merchants": [],
            "transactions": [],
            "audit_log": [],
            "rules_config": [],
            "user_roles": [],
            "kill_switch": [],
        }
        self.current_merchant_id = current_merchant_id

    def table(self, table_name: str) -> InMemorySupabaseTable:
        return InMemorySupabaseTable(table_name, self.db_store)


def get_supabase_client(api_key: Optional[str] = None) -> Any:
    """Factory providing Supabase client instance."""
    global _supabase_client
    settings = get_settings()

    # If an in-memory client was explicitly set (e.g. by reset_in_memory_db in tests)
    if isinstance(_supabase_client, InMemorySupabaseClient):
        return _supabase_client

    # Use in-memory client if mock or placeholder URL configured
    if "mock" in settings.SUPABASE_URL or "your-project" in settings.SUPABASE_URL:
        if _supabase_client is None or not isinstance(_supabase_client, InMemorySupabaseClient):
            _supabase_client = InMemorySupabaseClient()
        return _supabase_client

    if api_key is None and _supabase_client is not None and not isinstance(_supabase_client, InMemorySupabaseClient):
        return _supabase_client

    from supabase import create_client

    key = api_key or settings.SUPABASE_SERVICE_KEY
    client = create_client(settings.SUPABASE_URL, key)
    if api_key is None:
        _supabase_client = client
    return client


def reset_in_memory_db() -> InMemorySupabaseClient:
    """Helper to reset in-memory test database."""
    global _supabase_client
    _supabase_client = InMemorySupabaseClient()
    return _supabase_client

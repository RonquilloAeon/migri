import re
from typing import Any, Dict, List

import aiosqlite

from migri.elements import Query
from migri.interfaces import ConnectionBackend, TransactionBackend


class SQLiteConnection(ConnectionBackend):
    @staticmethod
    def _compile(query: Query) -> dict:
        q = query.statement
        v = []

        if query.placeholders:
            for p in query.placeholders:
                # Append value
                v.append(query.values[p.replace("$", "")])

                # Substitute
                q = re.sub(f"\\{p}", "?", q)

        return {"query": q, "values": v}

    async def connect(self):
        self._db = await aiosqlite.connect(self._db_name)

    async def disconnect(self):
        await self._db.close()

    async def execute(self, query: Query):
        ...

    async def fetch(self, query: Query) -> Dict[str, Any]:
        ...

    async def fetch_all(self, query: Query) -> List[Dict[str, Any]]:
        ...

    def transaction(self) -> "TransactionBackend":
        return SQLiteTransaction(self)


class SQLiteTransaction(TransactionBackend):
    ...

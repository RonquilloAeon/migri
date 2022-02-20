import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import asyncpg

from migri.elements import Query
from migri.interfaces import ConnectionBackend, TransactionBackend


@dataclass
class PostgreSQLConnection(ConnectionBackend):
    _dialect = "postgresql"
    connection: Optional[asyncpg.Connection] = None

    @staticmethod
    def _compile(query: Query) -> dict:
        q = query.statement
        v = []

        if query.placeholders:
            keys = list(query.values.keys())
            v = [query.values[k] for k in keys]

            for p in set(query.placeholders):
                # Find index of key and add 1
                replacement = f"${keys.index(p.replace('$', '')) + 1}"

                # Substitute
                q = re.sub(f"\\{p}", replacement, q)

        return {"query": q, "values": v}

    async def connect(self):
        if not self.db:
            if self.connection is not None:
                self.db = self.connection
            else:
                self.db = await asyncpg.connect(
                    host=self.db_host,
                    port=self.db_port,
                    user=self.db_user,
                    password=self.db_pass,
                    database=self.db_name,
                )

    async def disconnect(self):
        await self.db.close()

    async def execute(self, query: Query):
        q = self._compile(query)
        await self.db.execute(q["query"], *q["values"])

    async def fetch(self, query: Query) -> Dict[str, Any]:
        q = self._compile(query)
        res = await self.db.fetchrow(q["query"], *q["values"])
        return dict(res)

    async def fetch_all(self, query: Query) -> List[Dict[str, Any]]:
        q = self._compile(query)
        res = await self.db.fetch(q["query"], *q["values"])

        return [dict(r) for r in res]

    def transaction(self) -> TransactionBackend:
        return PostgreSQLTransaction(self)


class PostgreSQLTransaction(TransactionBackend):
    def __init__(self, connection: ConnectionBackend):
        super().__init__(connection)
        self._committed = False
        self._transaction = None

    async def start(self):
        self._transaction = self._connection.database.transaction()
        await self._transaction.start()

    async def commit(self):
        await self._transaction.commit()
        self._committed = True

    async def rollback(self):
        if not self._committed:
            await self._transaction.rollback()
